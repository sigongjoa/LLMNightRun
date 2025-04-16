// Listen for messages from content script
chrome.runtime.onMessage.addListener(function(message, sender, sendResponse) {
  if (message.action === "contentScriptLoaded") {
    console.log('Content script loaded in tab:', sender.tab.id, 'URL:', message.url);
    // You could store this information if needed
  }
});

// Handle installation and update events
chrome.runtime.onInstalled.addListener(function() {
  console.log('AI Chat Helper extension installed');
  
  // Initialize storage with empty scheduled messages if not exists
  chrome.storage.local.get('scheduledMessages', function(data) {
    if (!data.scheduledMessages) {
      chrome.storage.local.set({'scheduledMessages': []});
    } else {
      // Check for any pending scheduled messages and set alarms
      setupAlarmsForScheduledMessages(data.scheduledMessages);
    }
  });
});

// Inject content script when a tab is updated
chrome.tabs.onUpdated.addListener(function(tabId, changeInfo, tab) {
  // Only run if the page is fully loaded
  if (changeInfo.status !== 'complete') return;
  
  // Check if we're on a supported chat page
  if (
    tab.url && (
      tab.url.includes('chat.openai.com') || 
      tab.url.includes('chatgpt.com') || 
      tab.url.includes('claude.ai')
    )
  ) {
    // Inject the content script
    chrome.scripting.executeScript({
      target: {tabId: tabId},
      files: ['content.js']
    }).catch(err => console.error('Failed to inject content script:', err));
  }
});

// Function to update a message status
function updateMessageStatus(messageId, status) {
  console.log(`Updating message ${messageId} status to ${status}`);
  
  chrome.storage.local.get('scheduledMessages', function(data) {
    if (!data.scheduledMessages) return;
    
    const scheduledMessages = data.scheduledMessages;
    const updatedMessages = scheduledMessages.map(msg => {
      if (msg.id === messageId) {
        return {...msg, status: status};
      }
      return msg;
    });
    
    chrome.storage.local.set({'scheduledMessages': updatedMessages}, function() {
      console.log('Message status updated in storage');
    });
  });
}

// Listen for alarms to send scheduled messages
chrome.alarms.onAlarm.addListener(function(alarm) {
  console.log('Alarm triggered:', alarm);
  
  if (alarm.name.startsWith('scheduled-message-')) {
    const messageId = alarm.name.replace('scheduled-message-', '');
    console.log('Processing scheduled message with ID:', messageId);
    
    // Get the scheduled message from storage
    chrome.storage.local.get('scheduledMessages', function(data) {
      if (!data.scheduledMessages) {
        console.error('No scheduled messages found in storage');
        return;
      }
      
      const scheduledMessages = data.scheduledMessages;
      const messageToSend = scheduledMessages.find(msg => msg.id === messageId);
      
      if (!messageToSend) {
        console.error('Message not found in scheduled messages:', messageId);
        return;
      }
      
      if (messageToSend.status === 'scheduled') {
        console.log('Found message to send:', messageToSend);
        
        // Find active ChatGPT or Claude tab
        findActiveChatTab().then(function(tab) {
          if (tab) {
            console.log('Found active chat tab:', tab.id);
            
            // Send message to content script to post the message
            chrome.tabs.sendMessage(tab.id, {
              action: 'sendMessage',
              message: messageToSend.message
            }, function(response) {
              if (chrome.runtime.lastError) {
                console.error('Error sending message to tab:', chrome.runtime.lastError);
                
                // Inject content script and try again
                chrome.scripting.executeScript({
                  target: { tabId: tab.id },
                  files: ['content.js']
                }).then(() => {
                  console.log('Content script injected, trying again to send message...');
                  setTimeout(() => {
                    chrome.tabs.sendMessage(tab.id, {
                      action: 'sendMessage',
                      message: messageToSend.message
                    }, function(secondResponse) {
                      if (chrome.runtime.lastError) {
                        console.error('Still failed to send message after content script injection:', chrome.runtime.lastError);
                      } else if (secondResponse && secondResponse.success) {
                        console.log('Message sent successfully after content script injection');
                        updateMessageStatus(messageId, 'sent');
                      }
                    });
                  }, 500); // Wait for content script to initialize
                }).catch(err => {
                  console.error('Failed to inject content script:', err);
                });
                
                return;
              }
              
              if (response && response.success) {
                console.log('Scheduled message sent successfully');
                updateMessageStatus(messageId, 'sent');
              } else {
                console.error('Failed to send scheduled message');
              }
            });
          } else {
            console.error('No active chat tab found');
          }
        });
      }
    });
  }
});

// Function to find an active ChatGPT or Claude tab
function findActiveChatTab() {
  return new Promise((resolve) => {
    chrome.tabs.query({}, function(tabs) {
      // First try to find an active chat tab
      for (const tab of tabs) {
        if (
          (tab.url.includes('chat.openai.com') || 
           tab.url.includes('chatgpt.com') || 
           tab.url.includes('claude.ai')) && 
          tab.active
        ) {
          return resolve(tab);
        }
      }
      
      // If no active chat tab, find any chat tab
      for (const tab of tabs) {
        if (
          tab.url.includes('chat.openai.com') || 
          tab.url.includes('chatgpt.com') || 
          tab.url.includes('claude.ai')
        ) {
          return resolve(tab);
        }
      }
      
      // No chat tab found
      resolve(null);
    });
  });
}

// Set up alarms for all scheduled messages
function setupAlarmsForScheduledMessages(messages) {
  if (!messages || messages.length === 0) return;
  
  const now = new Date().getTime();
  
  messages.forEach(message => {
    if (message.status === 'scheduled') {
      const scheduleTime = new Date(message.scheduleTime).getTime();
      
      // Only create alarms for future messages
      if (scheduleTime > now) {
        chrome.alarms.create(`scheduled-message-${message.id}`, {
          when: scheduleTime
        });
        console.log(`Created alarm for message ID ${message.id} at ${new Date(scheduleTime).toLocaleString()}`);
      }
    }
  });
}

// Listen for storage changes to update alarms
chrome.storage.onChanged.addListener(function(changes, namespace) {
  if (namespace === 'local' && changes.scheduledMessages) {
    console.log('Scheduled messages updated in storage');
    // Clear all existing alarms
    chrome.alarms.clearAll(function() {
      // Set up new alarms for updated scheduled messages
      setupAlarmsForScheduledMessages(changes.scheduledMessages.newValue);
    });
  }
});

// Check active alarms on startup
chrome.alarms.getAll(function(alarms) {
  console.log('Current alarms on startup:', alarms);
});

console.log('Background script initialized');
