// Log that content script has loaded
console.log('ChatGPT Conversation Helper: Content script loaded successfully on ' + window.location.href);

// Apply marker classes to conversation elements for better extraction
function applyMarkerClasses() {
  // Find conversation elements
  const conversationContainers = [
    ...document.querySelectorAll('div[data-testid="conversation-turn"]'),
    ...document.querySelectorAll('div.items-start.gap-3 > div'),
    ...document.querySelectorAll('article.text-token-text-primary')
  ];
  
  conversationContainers.forEach(container => {
    if (!container.classList.contains('chatgpt-helper-conversation-element')) {
      container.classList.add('chatgpt-helper-conversation-element');
      
      // Determine if it's a user or assistant message
      const isUserMessage = (
        container.hasAttribute('data-message-author-role') && 
        container.getAttribute('data-message-author-role') === 'user'
      ) || (
        container.querySelector('[data-message-author-role="user"]')
      ) || (
        container.classList.contains('user') ||
        container.textContent.length < 100 // User messages are typically shorter
      );
      
      if (isUserMessage) {
        container.classList.add('chatgpt-helper-user-message');
      } else {
        container.classList.add('chatgpt-helper-assistant-message');
      }
    }
  });
}

// Run marker class application immediately and periodically
applyMarkerClasses();
setInterval(applyMarkerClasses, 2000);

// Notify the background script that content script is loaded
try {
  chrome.runtime.sendMessage({ action: "contentScriptLoaded", url: window.location.href });
} catch (error) {
  console.error('Error notifying background script:', error);
}

// Listen for messages from the popup
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
  // Simple ping to check if content script is loaded
  if (request.action === "ping") {
    console.log('Received ping request');
    sendResponse({ success: true, message: "Content script is loaded" });
    return true;
  }
  
  if (request.action === "extract") {
    try {
      console.log('Extracting conversation...');
      
      // Safety mechanism - if we can't extract the conversation properly, at least return something
      let conversation;
      try {
        conversation = extractConversation();
      } catch (extractError) {
        console.error('Error during extraction:', extractError);
        // Fallback to a basic extraction
        conversation = {
          title: document.title || "ChatGPT Conversation",
          create_time: new Date().toISOString(),
          update_time: new Date().toISOString(),
          mapping: {},
          messages: []
        };
        
        // Try to at least get some text content from the page
        const texts = Array.from(document.querySelectorAll('div.text-token-text-primary')).map(el => el.textContent);
        if (texts.length > 0) {
          let msgId = 1;
          let isUser = true;
          texts.forEach((text, i) => {
            if (text && text.trim()) {
              const messageId = `message-${msgId}`;
              conversation.mapping[messageId] = {
                id: messageId,
                role: isUser ? 'user' : 'assistant',
                content: `<p>${text}</p>`,
                text_content: text,
                timestamp: new Date().toISOString()
              };
              conversation.messages.push(messageId);
              msgId++;
              isUser = !isUser; // Alternate between user and assistant
            }
          });
        }
      }
      
      const format = request.format || 'json';
      let formattedData;
      
      switch(format) {
        case 'json':
          formattedData = JSON.stringify(conversation, null, 2);
          break;
        case 'markdown':
          formattedData = convertToMarkdown(conversation);
          break;
        case 'text':
          formattedData = convertToText(conversation);
          break;
        default:
          formattedData = JSON.stringify(conversation, null, 2);
      }
      
      sendResponse({ success: true, data: formattedData });
    } catch (error) {
      console.error('Error extracting conversation:', error);
      sendResponse({ success: false, error: error.message });
    }
    return true;
  } else if (request.action === "sendMessage") {
    try {
      console.log('Sending message:', request.message);
      sendMessage(request.message);
      sendResponse({ success: true });
    } catch (error) {
      console.error("Error sending message:", error);
      sendResponse({ success: false, error: error.message });
    }
    return true;
  } else if (request.action === "applyStyles") {
    try {
      console.log('Applying styles:', request.styles);
      applyStyles(request.styles);
      sendResponse({ success: true });
    } catch (error) {
      console.error("Error applying styles:", error);
      sendResponse({ success: false, error: error.message });
    }
    return true;
  }
});

// Function to send a message
function sendMessage(message) {
  if (!message) {
    throw new Error("메시지가 비어있습니다.");
  }
  
  console.log('Attempting to send message:', message);
  
  // Try different input selectors for ChatGPT
  let inputElement = null;
  let sendButton = null;
  
  // ChatGPT selectors
  const chatgptSelectors = [
    'textarea[data-id="root"]', 
    'textarea[placeholder="Send a message"]',
    'textarea[placeholder*="message"]',
    'div[role="textbox"]',
    '.chat-input textarea',
    '#prompt-textarea',
    'textarea.w-full',
    'textarea'
  ];
  
  // Try all possible selectors
  for (const selector of chatgptSelectors) {
    const element = document.querySelector(selector);
    if (element) {
      inputElement = element;
      console.log('Found input element with selector:', selector);
      break;
    }
  }
  
  if (!inputElement) {
    throw new Error("입력 필드를 찾을 수 없습니다.");
  }
  
  // Focus the input element
  inputElement.focus();
  
  // Reset any existing value
  if (inputElement.tagName === 'TEXTAREA') {
    inputElement.value = '';
  } else if (inputElement.getAttribute('contenteditable') === 'true') {
    inputElement.innerHTML = '';
  }

  // Force a small delay before typing to ensure focus is complete
  setTimeout(() => {
    // Set the value for textarea elements
    if (inputElement.tagName === 'TEXTAREA') {
      // Set through property
      inputElement.value = message;
      
      // Trigger multiple events to ensure it's registered
      inputElement.dispatchEvent(new Event('input', { bubbles: true }));
      inputElement.dispatchEvent(new Event('change', { bubbles: true }));
    } 
    // Set innerHTML for contenteditable divs
    else if (inputElement.getAttribute('contenteditable') === 'true') {
      inputElement.innerHTML = message;
      
      // Trigger events
      inputElement.dispatchEvent(new Event('input', { bubbles: true }));
      inputElement.dispatchEvent(new Event('change', { bubbles: true }));
    }

    // Force a delay to find the send button after input is registered
    setTimeout(() => {
      // Common send button selectors for ChatGPT (updated for latest UI)
      const sendButtonSelectors = [
        'button[data-testid="send-button"]',
        'button.chat-send-button',
        'button[aria-label="Send message"]',
        'button.send',
        'button[type="submit"]',
        'form button',
        'button.absolute.p-1.rounded-md.md\\:bottom-3.md\\:p-2',
        'button.absolute',
        'button.bottom-0',
        'button svg',
        'button.enabled',
        'button:not([disabled])', // Any enabled button
        'button:enabled',
        'button:has(svg)' // Button containing SVG (send icon)
      ];
      
      // Try to find the send button
      for (const selector of sendButtonSelectors) {
        try {
          const buttons = document.querySelectorAll(selector);
          if (buttons.length > 0) {
            // Use the most likely send button (usually near the input)
            for (const button of buttons) {
              const rect = button.getBoundingClientRect();
              if (rect.width > 0 && rect.height > 0) {
                // Check if it's visible and likely to be send button
                if (
                  button.textContent?.includes('send') ||
                  button.innerHTML?.includes('plane') ||
                  button.innerHTML?.includes('send') ||
                  button.innerHTML?.includes('arrow') ||
                  (button.classList.contains('send') || button.classList.contains('submit')) ||
                  // Check if near the input field
                  Math.abs(button.getBoundingClientRect().left - inputElement.getBoundingClientRect().right) < 150
                ) {
                  sendButton = button;
                  console.log('Found send button with selector:', selector);
                  break;
                }
              }
            }
          }
          if (sendButton) break;
        } catch (e) {
          console.error('Error finding button with selector:', selector, e);
        }
      }
      
      // If no send button found via selectors, try position-based detection
      if (!sendButton) {
        console.log('No button found with standard selectors, trying position-based detection');
        const allButtons = document.querySelectorAll('button, div[role="button"], span[role="button"]');
        
        if (inputElement) {
          const inputRect = inputElement.getBoundingClientRect();
          
          // Find the closest button to the input field
          let bestCandidate = null;
          let minDistance = Infinity;
          
          for (const btn of allButtons) {
            const btnRect = btn.getBoundingClientRect();
            
            // Check if button is visible
            if (btnRect.width > 0 && btnRect.height > 0) {
              // Check if button is on screen
              if (btnRect.top > 0 && btnRect.bottom < window.innerHeight) {
                // Check if button is to the right or below the input field
                const horizontalProximity = Math.abs(btnRect.left - inputRect.right);
                const verticalProximity = Math.abs(btnRect.top - inputRect.bottom);
                
                // Calculate weighted distance
                const weightedDistance = horizontalProximity + verticalProximity * 0.5;
                
                if (weightedDistance < minDistance) {
                  minDistance = weightedDistance;
                  bestCandidate = btn;
                }
              }
            }
          }
          
          if (bestCandidate && minDistance < 200) {
            sendButton = bestCandidate;
            console.log('Found button using position-based detection, distance:', minDistance);
          }
        }
      }
      
      // Click the send button
      if (sendButton) {
        console.log('Clicking send button:', sendButton.tagName, sendButton.className);
        
        // Try multiple click methods to ensure success
        try {
          // Remove disabled attribute if present
          if (sendButton.hasAttribute('disabled')) {
            sendButton.removeAttribute('disabled');
          }
          
          // 1. Standard click method
          sendButton.click();
          
          // 2. Mouse event simulation
          sendButton.dispatchEvent(new MouseEvent('click', {
            view: window,
            bubbles: true,
            cancelable: true
          }));
          
          // 3. mousedown/mouseup event simulation
          sendButton.dispatchEvent(new MouseEvent('mousedown', {
            view: window,
            bubbles: true,
            cancelable: true
          }));
          
          sendButton.dispatchEvent(new MouseEvent('mouseup', {
            view: window,
            bubbles: true,
            cancelable: true
          }));
          
          console.log('Successfully triggered click events on button');
        } catch (e) {
          console.error('Error clicking button:', e);
        }
      } else {
        console.log('No send button found, trying keyboard event as fallback');
        
        // Try to submit with Enter key
        const enterEvent = new KeyboardEvent('keydown', {
          bubbles: true,
          cancelable: true,
          key: 'Enter',
          code: 'Enter',
          keyCode: 13,
          which: 13,
          shiftKey: false,
          ctrlKey: false,
          metaKey: false
        });
        
        inputElement.dispatchEvent(enterEvent);
      }
    }, 300); // Wait for button to activate
  }, 100); // Wait for input to be focused
}

// Function to extract conversation
function extractConversation() {
  console.log('Starting conversation extraction');
  
  // 1. Get the thread container
  let threadContainer = null;
  
  // For ChatGPT, try to find the thread container - updated selectors for new UI
  const chatgptContainer = document.querySelector('div[class*="react-scroll-to-bottom"] > div > div') || 
                          document.querySelector('main div.overflow-y-auto') ||
                          document.querySelector('main div[class*="conversation"]') ||
                          document.querySelector('div[class*="chat-container"]') ||
                          document.querySelector('div[role="presentation"]') ||
                          // More specific selectors to target only the conversation area
                          document.querySelector('main div.items-start.gap-3') ||
                          document.querySelector('div[data-testid="conversation-turn-stream"]')?.parentElement ||
                          document.querySelector('article.text-token-text-primary') ||
                          document.querySelector('main');
  
  if (chatgptContainer) {
    threadContainer = chatgptContainer;
    console.log('Using ChatGPT container');
  } else {
    // Try a more generic approach
    console.log('Trying generic container approach');
    const possibleContainers = document.querySelectorAll('main div.overflow-y-auto, .chat-container, .message-container');
    for (const container of possibleContainers) {
      // Look for a container with multiple child elements
      if (container.children.length > 3) {
        threadContainer = container;
        break;
      }
    }
  }
  
  if (!threadContainer) {
    console.error('Thread container not found!');
    console.log('Document body HTML structure (first 1000 chars):', document.body.innerHTML.substring(0, 1000));
    throw new Error("대화 스레드를 찾을 수 없습니다.");
  }
  
  console.log('Thread container found with children count:', threadContainer.children.length);
  
  // 2. Extract all message blocks
  const messageBlocks = Array.from(threadContainer.querySelectorAll(
    // Common message container classes/attributes for ChatGPT
    '.message, .chat-message, .message-container, ' +
    'div[data-message-author-role], ' + 
    'div[data-testid="conversation-turn"], ' +
    'div.group.w-full, ' +
    'div.relative.markdown, ' +
    'article.text-token-text-primary'
  ));
  
  // Filter out sidebar menu items and any other unrelated elements
  const filteredMessageBlocks = messageBlocks.filter(block => {
    // Skip elements that are part of the sidebar
    if (block.closest('#__next > div > div:first-child') || 
        block.closest('nav') || 
        block.closest('.sidebar') || 
        block.closest('header') ||
        block.closest('footer')) {
      return false;
    }
    
    // Skip elements with very little content
    if (block.textContent.trim().length < 2) {
      return false;
    }
    
    // Skip elements that are likely UI components, not messages
    if (block.querySelector('button') || 
        block.getAttribute('role') === 'button' || 
        block.classList.contains('button')) {
      return false;
    }
    
    return true;
  });
  
  console.log('After filtering sidebar items:', filteredMessageBlocks.length);
  
  // First try to use the marked elements for better extraction
  if (filteredMessageBlocks.length === 0) {
    console.log('Trying to use marked elements for extraction');
    const markedElements = Array.from(document.querySelectorAll('.chatgpt-helper-conversation-element'));
    
    if (markedElements.length > 0) {
      filteredMessageBlocks.push(...markedElements);
      console.log('Using marked elements for extraction:', markedElements.length);
    }
  }
  
  // If no specific message blocks were found, try more aggressive approaches
  if (filteredMessageBlocks.length === 0) {
    console.log('No specific message blocks found, trying additional selectors...');
    
    // Try with more generic selectors for ChatGPT
    const chatgptMessageSelectors = [
      '[data-message-author-role]',
      '[data-testid*="conversation-turn"]',
      'div[class*="conversation-turn"]',
      'div[class*="ConversationTurn"]',
      'div.relative.group',
      'div.text-token-text-primary',
      'div.flex.flex-col.items-start',
      'div.markdown',
      'main > div > div > div', // Very generic last resort
      'div > div > div > div > div' // Ultra generic last resort
    ];
    
    for (const selector of chatgptMessageSelectors) {
      const foundMessages = threadContainer.querySelectorAll(selector);
      if (foundMessages && foundMessages.length > 0) {
        console.log(`Found ${foundMessages.length} messages using selector: ${selector}`);
        
        // Filter out sidebar elements here too
        const filteredFoundMessages = Array.from(foundMessages).filter(block => {
          if (block.closest('#__next > div > div:first-child') || 
              block.closest('nav') || 
              block.closest('.sidebar') || 
              block.closest('header') ||
              block.closest('footer')) {
            return false;
          }
          if (block.textContent.trim().length < 2) {
            return false;
          }
          return true;
        });
        
        if (filteredFoundMessages.length > 0) {
          filteredMessageBlocks.push(...filteredFoundMessages);
          break;
        }
      }
    }
    
    // If still nothing, get direct children of the thread container
    if (filteredMessageBlocks.length === 0) {
      console.log('No specific message blocks found, using direct children');
      const directChildren = Array.from(threadContainer.children).filter(child => {
        // Filter out any obvious non-message elements
        return (
          child.textContent.trim() && 
          !child.className.includes('typing') && 
          !child.className.includes('input') && 
          !child.className.includes('composer') &&
          !child.closest('nav') && 
          !child.closest('.sidebar')
        );
      });
      
      if (directChildren.length > 0) {
        filteredMessageBlocks.push(...directChildren);
        console.log('Added direct children as message blocks, new count:', filteredMessageBlocks.length);
      }
      
      // Last resort - use all divs with text
      if (filteredMessageBlocks.length === 0) {
        console.log('No direct children found, using all divs with content');
        const allDivsWithContent = threadContainer.querySelectorAll('div');
        const filteredDivs = Array.from(allDivsWithContent).filter(div => {
          // Take only divs that have text and look like they could be messages
          const text = div.textContent.trim();
          return text.length > 20 && 
                 !div.className.includes('typing') && 
                 !div.querySelector('input') && 
                 !div.querySelector('textarea') &&
                 !div.closest('nav') && 
                 !div.closest('.sidebar') && 
                 !div.closest('header') &&
                 !div.closest('footer');
        });
        
        if (filteredDivs.length > 0) {
          // Sort by text length - messages are usually longer
          filteredDivs.sort((a, b) => 
            b.textContent.trim().length - a.textContent.trim().length
          );
          
          // Take top divs
          const topDivs = filteredDivs.slice(0, 20);
          filteredMessageBlocks.push(...topDivs);
          console.log('Added top divs with content as message blocks, new count:', filteredMessageBlocks.length);
        }
      }
    }
  }
  
  if (filteredMessageBlocks.length === 0) {
    console.log('DOM structure:', threadContainer.outerHTML.substring(0, 500));
    throw new Error("메시지를 찾을 수 없습니다.");
  }
  
  // 3. Process each message block
  const conversation = {
    title: document.title.replace(" - ChatGPT", ""),
    create_time: new Date().toISOString(),
    update_time: new Date().toISOString(),
    mapping: {},
    messages: []
  };
  
  let messageId = 1;
  
  // Function to recursively get all text content, preserving structure
  function getTextContent(element) {
    if (!element) return '';
    
    // Check for code blocks
    if (element.tagName === 'PRE' || 
        element.className.includes('code') || 
        element.parentElement?.tagName === 'CODE' ||
        element.querySelector('code')) {
      return element.innerHTML;
    }
    
    // For regular text, recursively get all text content
    return Array.from(element.childNodes).map(node => {
      if (node.nodeType === Node.TEXT_NODE) {
        return node.textContent;
      } else if (node.nodeType === Node.ELEMENT_NODE) {
        // Handle special elements
        if (node.tagName === 'BR') return '\n';
        if (node.tagName === 'P') return getTextContent(node) + '\n';
        if (node.tagName === 'DIV' && !node.className.includes('chat-message')) return getTextContent(node) + '\n';
        if (node.tagName === 'LI') return '- ' + getTextContent(node) + '\n';
        if (node.tagName === 'UL' || node.tagName === 'OL') return getTextContent(node) + '\n';
        if (node.tagName === 'H1') return '# ' + getTextContent(node) + '\n';
        if (node.tagName === 'H2') return '## ' + getTextContent(node) + '\n';
        if (node.tagName === 'H3') return '### ' + getTextContent(node) + '\n';
        if (node.tagName === 'STRONG' || node.tagName === 'B') return '**' + getTextContent(node) + '**';
        if (node.tagName === 'EM' || node.tagName === 'I') return '*' + getTextContent(node) + '*';
        return getTextContent(node);
      }
      return '';
    }).join('');
  }
  
  filteredMessageBlocks.forEach((block, index) => {
    // Determine if it's a user or assistant message
    
    // ChatGPT specific indicators
    const hasChatGPTImg = block.querySelector('img[alt="ChatGPT"]');
    const hasUserImg = block.querySelector('img[alt="User"]');
    
    // Role attribute indicators
    const hasAssistantRole = block.querySelector('[data-message-author-role="assistant"], [data-testid*="assistant"]') ||
                           block.getAttribute('data-message-author-role') === 'assistant';
    const hasUserRole = block.querySelector('[data-message-author-role="user"], [data-testid*="user"]') ||
                       block.getAttribute('data-message-author-role') === 'user';
    
    // Class name indicators
    const hasAssistantClass = block.className.includes('assistant') || 
                             block.className.includes('bot') || 
                             block.className.includes('ai') ||
                             block.classList.contains('chatgpt-helper-assistant-message');
    const hasUserClass = block.className.includes('user') || 
                        block.className.includes('human') ||
                        block.classList.contains('chatgpt-helper-user-message');
    
    // Combine all indicators
    const isAssistantMessage = hasChatGPTImg || hasAssistantRole || hasAssistantClass;
    const isUserMessage = hasUserImg || hasUserRole || hasUserClass;
    
    let role = 'unknown';
    
    if (isUserMessage) {
      role = 'user';
    } else if (isAssistantMessage) {
      role = 'assistant';
    } else {
      // If we can't determine the role, try to infer based on position
      if (index > 0 && conversation.messages.length > 0) {
        // If the last message was from the user, this is likely from the assistant
        const lastMessageId = conversation.messages[conversation.messages.length - 1];
        const lastMessage = conversation.mapping[lastMessageId];
        if (lastMessage && lastMessage.role === 'user') {
          role = 'assistant';
        } else {
          role = 'user';
        }
      } else if (index === 0) {
        // First message is typically from the user
        role = 'user';
      } else {
        // Alternating pattern
        role = (index % 2 === 0) ? 'user' : 'assistant';
      }
    }
    
    console.log(`Message ${index}, determined role: ${role}`);
    
    // Extract message content
    let contentElement = null;
    
    // Try different selectors for message content
    const contentSelectors = [
      '[data-message-text="true"]',
      '.markdown',
      'div[class*="prose"]',
      '.message-content',
      '.chat-content',
      '.message-text',
      '.content',
      'div[class*="content"]',
      'div[class*="text"]',
      'p',
      'span'
    ];
    
    // Try each selector
    for (const selector of contentSelectors) {
      const element = block.querySelector(selector);
      if (element && element.textContent.trim()) {
        contentElement = element;
        console.log(`Found content with selector: ${selector}`);
        break;
      }
    }
    
    // If no specific content element was found, use the message block itself
    if (!contentElement) {
      contentElement = block;
      console.log('Using block as content element');
    }
    
    // Extract both HTML content and text content
    const content = contentElement.innerHTML;
    const textContent = getTextContent(contentElement).trim();
    
    // Skip empty messages
    if (!textContent) {
      console.log('Skipping empty message');
      return;
    }
    
    const message = {
      id: `message-${messageId}`,
      role: role,
      content: content,
      text_content: textContent,
      timestamp: new Date().toISOString()
    };
    
    // Add to the mapping and messages
    conversation.mapping[message.id] = message;
    conversation.messages.push(message.id);
    
    messageId++;
  });
  
  // Special case: no messages found
  if (conversation.messages.length === 0) {
    console.log('No valid messages found after processing');
    throw new Error("유효한 메시지를 추출할 수 없습니다.");
  }
  
  console.log(`Successfully extracted ${conversation.messages.length} messages`);
  return conversation;
}

// Function to convert conversation to Markdown
function convertToMarkdown(conversation) {
  let markdown = `# ${conversation.title}\n\n`;
  markdown += `생성 시간: ${new Date(conversation.create_time).toLocaleString()}\n\n`;
  
  conversation.messages.forEach(messageId => {
    const message = conversation.mapping[messageId];
    const sender = message.role === 'user' ? '**사용자**' : '**ChatGPT**';
    
    markdown += `## ${sender} - ${new Date(message.timestamp).toLocaleString()}\n\n`;
    markdown += `${message.text_content}\n\n`;
    markdown += `---\n\n`;
  });
  
  return markdown;
}

// Function to convert conversation to plain text
function convertToText(conversation) {
  let text = `${conversation.title}\n\n`;
  text += `생성 시간: ${new Date(conversation.create_time).toLocaleString()}\n\n`;
  
  conversation.messages.forEach(messageId => {
    const message = conversation.mapping[messageId];
    const sender = message.role === 'user' ? '사용자' : 'ChatGPT';
    
    text += `[${sender}] - ${new Date(message.timestamp).toLocaleString()}\n`;
    text += `${message.text_content}\n\n`;
  });
  
  return text;
}

// Function to apply custom styles to ChatGPT interface
function applyStyles(styles) {
  // Remove existing custom styles if any
  const existingStyles = document.getElementById('chatgpt-helper-custom-styles');
  if (existingStyles) {
    existingStyles.remove();
  }
  
  // Create a new style element
  const styleElement = document.createElement('style');
  styleElement.id = 'chatgpt-helper-custom-styles';
  
  let cssRules = '';
  
  // Apply dark mode if enabled
  if (styles.darkMode) {
    cssRules += `
      body {
        background-color: #1e1e2e !important;
        color: #cdd6f4 !important;
      }
      main {
        background-color: #1e1e2e !important;
        color: #cdd6f4 !important;
      }
      .dark {
        background-color: #181825 !important;
      }
      [data-message-author-role="assistant"] {
        background-color: #313244 !important;
        color: #cdd6f4 !important;
      }
      [data-message-author-role="user"] {
        background-color: #252536 !important;
        color: #cdd6f4 !important;
      }
      textarea, input, select {
        background-color: #313244 !important;
        color: #cdd6f4 !important;
        border-color: #45475a !important;
      }
      button {
        background-color: #585b70 !important;
        color: #cdd6f4 !important;
      }
      a {
        color: #89b4fa !important;
      }
      pre, code {
        background-color: #1e1e2e !important;
        color: #a6e3a1 !important;
        border-color: #45475a !important;
      }
    `;
  }
  
  // Apply compact mode if enabled
  if (styles.compactMode) {
    cssRules += `
      main {
        max-width: 900px !important;
        margin: 0 auto !important;
      }
      [data-message-author-role] {
        padding: 0.75rem !important;
        margin-bottom: 0.5rem !important;
      }
      p {
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
      }
      h1, h2, h3, h4, h5, h6 {
        margin-top: 1rem !important;
        margin-bottom: 0.5rem !important;
      }
      pre {
        margin: 0.5rem 0 !important;
        padding: 0.5rem !important;
      }
    `;
  }
  
  // Apply accent color
  if (styles.accentColor) {
    cssRules += `
      :root {
        --accent-color: ${styles.accentColor} !important;
      }
      button[data-testid="send-button"] {
        background-color: ${styles.accentColor} !important;
      }
      a:hover {
        color: ${styles.accentColor} !important;
      }
      .active {
        border-color: ${styles.accentColor} !important;
      }
      [data-message-author-role="assistant"] strong,
      [data-message-author-role="assistant"] b {
        color: ${styles.accentColor} !important;
      }
    `;
  }
  
  // Apply custom CSS if provided
  if (styles.customCSS) {
    cssRules += styles.customCSS;
  }
  
  styleElement.textContent = cssRules;
  document.head.appendChild(styleElement);
  
  console.log('Applied custom styles to ChatGPT interface');
}

// Log that the content script has loaded at the end
console.log("ChatGPT Conversation Helper - 콘텐츠 스크립트 로드 완료");
