document.addEventListener('DOMContentLoaded', function() {
  const exportBtn = document.getElementById('export-btn');
  const openScheduleBtn = document.getElementById('open-schedule-btn');
  const applyStyleBtn = document.getElementById('apply-style-btn');
  const statusDiv = document.getElementById('status');
  const tabs = document.querySelectorAll('.tab');
  const tabContents = document.querySelectorAll('.tab-content');
  const darkModeCheckbox = document.getElementById('apply-dark-mode');
  const compactModeCheckbox = document.getElementById('apply-compact-mode');
  const customCssTextarea = document.getElementById('custom-css');
  const colorOptions = document.querySelectorAll('.color-option');
  
  let selectedColor = '#10a37f'; // Default color
  
  // Load saved style preferences
  chrome.storage.local.get('customStyles', function(data) {
    if (data.customStyles) {
      darkModeCheckbox.checked = data.customStyles.darkMode;
      compactModeCheckbox.checked = data.customStyles.compactMode;
      selectedColor = data.customStyles.accentColor;
      customCssTextarea.value = data.customStyles.customCSS || '';
      
      // Highlight the selected color option
      colorOptions.forEach(option => {
        if (option.style.backgroundColor === selectedColor) {
          option.style.border = '2px solid black';
        }
      });
    }
  });
  
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
  
  // Color palette selection
  colorOptions.forEach(option => {
    option.addEventListener('click', function() {
      // Reset all borders
      colorOptions.forEach(o => o.style.border = '1px solid #ddd');
      
      // Set selected border and update selectedColor
      this.style.border = '2px solid black';
      selectedColor = this.style.backgroundColor;
    });
  });
  
  // Check if we're on a ChatGPT page
  chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
    if (!tabs || !tabs[0] || !tabs[0].url) {
      statusDiv.textContent = 'URL을 확인할 수 없습니다.';
      exportBtn.disabled = true;
      openScheduleBtn.disabled = true;
      applyStyleBtn.disabled = true;
      return;
    }
    
    const currentUrl = tabs[0].url;
    const isChatGPTPage = currentUrl.includes('chat.openai.com') || 
                         currentUrl.includes('chatgpt.com');
    
    if (!isChatGPTPage) {
      statusDiv.textContent = 'ChatGPT 페이지에서만 사용 가능합니다.';
      exportBtn.disabled = true;
      openScheduleBtn.disabled = true;
      applyStyleBtn.disabled = true;
      return;
    }
    
    // Initially show loading state
    statusDiv.textContent = '확장 프로그램 초기화 중...';
    
    // Check content script status
    ensureContentScriptLoaded(function(success) {
      if (success) {
        statusDiv.textContent = '사용 준비가 되었습니다.';
        exportBtn.disabled = false;
        openScheduleBtn.disabled = false;
        applyStyleBtn.disabled = false;
      } else {
        statusDiv.textContent = '초기화 실패. 페이지를 새로고침해 주세요.';
        exportBtn.disabled = true;
        openScheduleBtn.disabled = true;
        applyStyleBtn.disabled = true;
      }
    });
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
      try {
        chrome.tabs.sendMessage(
          tabs[0].id,
          { action: "extract", format: format },
          function(response) {
            if (chrome.runtime.lastError) {
              console.error('Error sending message to content script:', chrome.runtime.lastError);
              statusDiv.textContent = '오류: 콘텐츠 스크립트와 통신할 수 없습니다.';
              // Try to inject the content script again
              tryInjectContentScript(tabs[0].id, function(success) {
                if (success) {
                  statusDiv.textContent = '콘텐츠 스크립트 재로드 성공. 다시 시도해 주세요.';
                } else {
                  statusDiv.textContent = '콘텐츠 스크립트 로드 실패. 페이지를 새로고침해 주세요.';
                }
              });
              return;
            }
            
            if (response && response.success) {
              statusDiv.textContent = '추출 완료! 다운로드 중...';
              
              // Generate filename based on date
              const date = new Date();
              const formattedDate = date.toISOString().split('T')[0];
              const filename = `chatgpt_conversation_${formattedDate}.${format === 'json' ? 'json' : (format === 'markdown' ? 'md' : 'txt')}`;
              
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
      } catch (error) {
        console.error('메시지 전송 중 오류 발생:', error);
        statusDiv.textContent = '오류 발생: ' + error.message;
      }
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
  
  // Helper function to inject content script
  function tryInjectContentScript(tabId, callback) {
    chrome.scripting.executeScript({
      target: { tabId: tabId },
      files: ['scripts/content.js']
    }).then(() => {
      console.log('Content script injected, waiting for initialization...');
      
      // Wait a moment for the script to initialize
      setTimeout(() => {
        // Check if it's working
        chrome.tabs.sendMessage(tabId, { action: "ping" }, function(response) {
          if (chrome.runtime.lastError) {
            console.error('Failed to initialize content script after injection:', chrome.runtime.lastError);
            callback(false);
          } else {
            console.log('Content script successfully initialized');
            callback(true);
          }
        });
      }, 800); // Increased wait time for initialization
    }).catch(err => {
      console.error('Failed to inject content script:', err);
      callback(false);
    });
  }

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
            tryInjectContentScript(tabs[0].id, callback);
          } else {
            console.log('Content script already loaded');
            callback(true);
          }
        });
      } catch (error) {
        console.error('Error checking content script:', error);
        tryInjectContentScript(tabs[0].id, callback);
      }
    });
  }
  
  // Handle schedule button click
  openScheduleBtn.addEventListener('click', function() {
    // Open schedule page in a new tab
    chrome.tabs.create({url: 'scheduled.html'});
  });
  
  // Handle apply style button click
  applyStyleBtn.addEventListener('click', function() {
    // Get style settings
    const styles = {
      darkMode: darkModeCheckbox.checked,
      compactMode: compactModeCheckbox.checked,
      accentColor: selectedColor,
      customCSS: customCssTextarea.value
    };
    
    // Save to storage
    chrome.storage.local.set({'customStyles': styles}, function() {
      console.log('Styles saved:', styles);
    });
    
    // Apply to active tab
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      chrome.tabs.sendMessage(
        tabs[0].id,
        { action: "applyStyles", styles: styles },
        function(response) {
          if (chrome.runtime.lastError) {
            console.error('Error sending styles to content script:', chrome.runtime.lastError);
            statusDiv.textContent = '오류: 스타일을 적용할 수 없습니다.';
            return;
          }
          
          if (response && response.success) {
            statusDiv.textContent = '스타일이 적용되었습니다!';
            setTimeout(() => {
              statusDiv.textContent = '사용 준비가 되었습니다.';
            }, 3000);
          } else {
            statusDiv.textContent = '오류: ' + (response ? response.error : '알 수 없는 오류');
          }
        }
      );
    });
  });
});
