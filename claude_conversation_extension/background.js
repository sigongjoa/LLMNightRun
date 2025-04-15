// 확장 프로그램이 설치되거나 업데이트될 때 실행
chrome.runtime.onInstalled.addListener(() => {
  console.log('Claude Conversation Extractor가 설치되었습니다.');
});

// Claude 페이지에서 탭이 업데이트될 때 콘텐츠 스크립트 강제 주입
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url && (
      tab.url.includes('claude.ai') || 
      tab.url.includes('anthropic.com'))) {
    
    console.log('Claude 페이지 감지됨, 콘텐츠 스크립트 주입 시도:', tab.url);
    
    // 스크립트 주입 시도
    chrome.scripting.executeScript({
      target: { tabId: tabId },
      files: ['content.js']
    }).then(() => {
      console.log('콘텐츠 스크립트 주입 성공');
      
      // 스크립트가 로드되었음을 알리는 메시지 전송
      chrome.tabs.sendMessage(tabId, { action: "scriptLoaded" })
        .then(response => {
          console.log('응답 받음:', response);
        })
        .catch(error => {
          console.error('메시지 전송 실패:', error);
        });
    }).catch(err => {
      console.error('콘텐츠 스크립트 주입 실패:', err);
    });
  }
});

// 팝업에서 오는 메시지 처리
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "getActiveTabInfo") {
    chrome.tabs.query({ active: true, currentWindow: true }, tabs => {
      if (tabs.length > 0) {
        sendResponse({ 
          success: true, 
          url: tabs[0].url, 
          id: tabs[0].id 
        });
      } else {
        sendResponse({ 
          success: false, 
          error: "활성 탭을 찾을 수 없습니다" 
        });
      }
    });
    return true; // 비동기 응답을 위해 true 반환
  }
  
  if (request.action === "reinjectContentScript") {
    chrome.tabs.query({ active: true, currentWindow: true }, tabs => {
      if (tabs.length > 0) {
        chrome.scripting.executeScript({
          target: { tabId: tabs[0].id },
          files: ['content.js']
        }).then(() => {
          sendResponse({ success: true });
        }).catch(err => {
          sendResponse({ 
            success: false, 
            error: err.message 
          });
        });
      } else {
        sendResponse({ 
          success: false, 
          error: "활성 탭을 찾을 수 없습니다" 
        });
      }
    });
    return true; // 비동기 응답을 위해 true 반환
  }
});
