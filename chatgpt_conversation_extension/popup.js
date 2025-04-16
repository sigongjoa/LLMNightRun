document.addEventListener('DOMContentLoaded', function() {
  const exportBtn = document.getElementById('export-btn');
  const openScheduleBtn = document.getElementById('open-schedule-btn');
  const statusDiv = document.getElementById('status');
  const tabs = document.querySelectorAll('.tab');
  const tabContents = document.querySelectorAll('.tab-content');
  
  // Tab switching functionality
  tabs.forEach(tab => {
    tab.addEventListener('click', function() {
      // Remove active class from all tabs and contents
      tabs.forEach(t => t.classList.remove('active'));
      tabContents.forEach(content => content.classList.remove('active'));
      
      // Add active class to clicked tab and corresponding content
      this.classList.add('active');
      const tabId = this.getAttribute('data-tab');
      document.getElementById(`${tabId}-tab`).classList.add('active');
    });
  });
  
  // Check if we're on an AI chat page
  chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
    if (!tabs || !tabs[0] || !tabs[0].url) {
      statusDiv.textContent = 'URL을 확인할 수 없습니다.';
      exportBtn.disabled = true;
      openScheduleBtn.disabled = true;
      return;
    }
    
    const currentUrl = tabs[0].url;
    const isChatPage = currentUrl.includes('chat.openai.com') || 
                     currentUrl.includes('chatgpt.com') || 
                     currentUrl.includes('claude.ai');
    
    if (!isChatPage) {
      statusDiv.textContent = 'AI 채팅 페이지에서만 사용 가능합니다.';
      exportBtn.disabled = true;
      openScheduleBtn.disabled = true;
      return;
    }
    
    // Initially show loading state
    statusDiv.textContent = '확장 프로그램 초기화 중...';
    // We'll check content script status when a button is clicked
  });
  
  // Function to handle export functionality
  function handleExport() {
    console.log('Handling export functionality');
    statusDiv.textContent = '대화 내용을 추출 중...';
    
    // Get the selected format
    const format = document.querySelector('input[name="format"]:checked').value;
    
    // Send message to content script to extract the conversation
    console.log('Sending extract message to content script...');
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      chrome.tabs.sendMessage(
        tabs[0].id,
        { action: "extract", format: format },
        function(response) {
          if (chrome.runtime.lastError) {
            console.error('Error sending message to content script:', chrome.runtime.lastError);
            statusDiv.textContent = '오류: 콘텐츠 스크립트와 통신할 수 없습니다.';
            return;
          }
          
          if (response && response.success) {
            statusDiv.textContent = '추출 완료! 다운로드 중...';
            
            // Generate filename based on date
            const date = new Date();
            const formattedDate = date.toISOString().split('T')[0];
            const platformName = getCurrentPlatformName();
            const filename = `${platformName}_conversation_${formattedDate}.${format === 'json' ? 'json' : (format === 'markdown' ? 'md' : 'txt')}`;
            
            // Create download
            const blob = new Blob([response.data], {type: 'application/json'});
            const url = URL.createObjectURL(blob);
            
            chrome.downloads.download({
              url: url,
              filename: filename,
              saveAs: true
            }, function() {
              statusDiv.textContent = '다운로드 완료!';
              setTimeout(() => {
                statusDiv.textContent = '사용 준비가 되었습니다.';
              }, 3000);
            });
          } else {
            statusDiv.textContent = '오류: ' + (response ? response.error : '알 수 없는 오류');
          }
        }
      );
    });
  }
  
  // Handle export button click
  exportBtn.addEventListener('click', function() {
    console.log('Export button clicked');
    // Check if content script is loaded before proceeding
    ensureContentScriptLoaded(function(success) {
      if (success) {
        handleExport();
      } else {
        statusDiv.textContent = '콘텐츠 스크립트 로드 실패. 페이지를 새로고침해 주세요.';
      }
    });
  });
  
  // Function to ensure content script is loaded
  function ensureContentScriptLoaded(callback) {
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      if (!tabs || !tabs[0]) {
        console.error('No active tab found');
        callback(false);
        return;
      }
      
      console.log('Checking if content script is loaded in tab:', tabs[0].id);
      
      // Try to ping the content script
      try {
        chrome.tabs.sendMessage(tabs[0].id, { action: "ping" }, function(response) {
          if (chrome.runtime.lastError) {
            console.log('Content script not loaded, injecting...');
            
            // Try to inject the content script
            chrome.scripting.executeScript({
              target: { tabId: tabs[0].id },
              files: ['content.js']
            }).then(() => {
              console.log('Content script injected, waiting for initialization...');
              
              // Wait a moment for the script to initialize
              setTimeout(() => {
                // Check again
                chrome.tabs.sendMessage(tabs[0].id, { action: "ping" }, function(secondResponse) {
                  if (chrome.runtime.lastError) {
                    console.error('Failed to initialize content script after injection:', chrome.runtime.lastError);
                    callback(false);
                  } else {
                    console.log('Content script successfully initialized');
                    callback(true);
                  }
                });
              }, 500); // Wait 500ms for initialization
            }).catch(err => {
              console.error('Failed to inject content script:', err);
              callback(false);
            });
          } else {
            console.log('Content script already loaded');
            callback(true);
          }
        });
      } catch (error) {
        console.error('Error checking content script:', error);
        callback(false);
      }
    });
  }
  
  // Handle schedule button click
  openScheduleBtn.addEventListener('click', function() {
    // Open schedule page in a new tab
    chrome.tabs.create({url: 'scheduled.html'});
  });
  
  // Function to get the current chat platform name
  function getCurrentPlatformName() {
    let platformName = 'ai_chat'; // Default value
    
    try {
      // Just read from current URL
      chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        if (tabs && tabs[0] && tabs[0].url) {
          const currentUrl = tabs[0].url;
          if (currentUrl.includes('chat.openai.com') || currentUrl.includes('chatgpt.com')) {
            platformName = 'chatgpt';
          } else if (currentUrl.includes('claude.ai')) {
            platformName = 'claude';
          }
        }
      });
    } catch (error) {
      console.error('Error getting platform name:', error);
    }
    
    return platformName;
  }
});
