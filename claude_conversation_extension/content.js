// 자동 저장 변수
let autoSaveEnabled = false;
let autoSaveInterval = 5; // 기본값 5분
let autoSaveTimer = null;

// DOM에서 Claude 대화 추출
function extractClaudeConversation(currentOnly = false) {
  try {
    const conversations = [];
    
    // 업데이트된 Claude 인터페이스 구조 지원 (개발자 도구 정보 기반)
    // 다양한 Claude 인터페이스 구조 시도
    let messageContainers = [];
    const possibleSelectors = [
      // 원래 선택자
      '.claude-conversation-message',
      '[data-message-id]',
      '.message-content',
      '.message',
      '.message-container',
      '.conversation-message',
      '.chat-message',
      // 새 구조 기반 선택자 (개발자 도구에서 확인)
      '.font-claude-message',
      '.whitespace-pre-wrap.break-words',
      '.data-test-render-count',
      '.sticky.bottom-0',
      // 특정 맥락 선택자
      '[aria-label="Message content"]',
      '[role="paragraph"]',
      // 일반 텍스트 컨테이너
      'p',
      'div > p',
      'div > div > p'
    ];
    
    // 여러 선택자를 시도하여, 메시지 컨테이너를 찾습니다
    for (const selector of possibleSelectors) {
      const elements = document.querySelectorAll(selector);
      if (elements.length > 0) {
        messageContainers = elements;
        console.log(`[Claude Extractor] 찾은 선택자: ${selector}, 요소 개수: ${elements.length}`);
        break;
      }
    }
    
    // 메시지를 찾을 수 없는 경우, 클래스나 속성으로 인식되는 모든 div 요소를 시도합니다
    if (messageContainers.length === 0) {
      console.log('[Claude Extractor] 일반 선택자로 메시지를 찾을 수 없어, 대화 내용이 있을 가능성이 높은 모든 div를 검사합니다');
      
      // 페이지에서 "Human", "Claude", "Assistant" 등의 텍스트가 포함된 요소를 찾습니다
      const allDivs = document.querySelectorAll('div');
      const potentialMessages = Array.from(allDivs).filter(div => {
        const text = div.textContent.toLowerCase();
        return text.includes('human:') || text.includes('claude:') || text.includes('assistant:') || 
               (div.textContent.length > 50 && (div.querySelector('p') || div.querySelector('pre')));
      });
      
      if (potentialMessages.length > 0) {
        messageContainers = potentialMessages;
        console.log(`[Claude Extractor] 대체 방법으로 ${potentialMessages.length}개 메시지 요소를 찾았습니다`);
      }
    }
    
    if (messageContainers.length === 0) {
      console.error('지원되는 Claude 인터페이스를 찾을 수 없습니다.');
      return { success: false, error: '지원되는 Claude 인터페이스를 찾을 수 없습니다. 페이지 구조가 변경되었을 수 있습니다.' };
    }
    
    // 실제 메시지 추출
    messageContainers.forEach(container => {
      // 사용자(Human) 또는 Claude 확인 - 더 많은 방법으로 시도
      let isHuman = false;
      
      // 요소 텍스트 내용 가져오기
      const containerText = container.textContent.trim();
      
      // 컨테이너와 모든 상위 요소의 클래스 리스트 수집 (디버깅 목적)
      let parentClasses = [];
      let currentElement = container;
      while (currentElement && currentElement !== document.body) {
        if (currentElement.className) {
          parentClasses.push(currentElement.className);
        }
        currentElement = currentElement.parentElement;
      }
      
      // 방법 1: 클래스로 확인
      if (container.classList.contains('message-user') || 
          container.classList.contains('user-message') ||
          container.classList.contains('human-message') ||
          container.querySelector('.user-message-content') !== null) {
        isHuman = true;
      }
      
      // 방법 2: 데이터 속성으로 확인
      if (!isHuman && container.hasAttribute('data-message-author-role')) {
        isHuman = container.getAttribute('data-message-author-role') === 'user' || 
                 container.getAttribute('data-message-author-role') === 'human';
      }
      
      // 방법 3: 부모 요소의 클래스로 확인
      if (!isHuman && container.parentElement) {
        isHuman = container.parentElement.classList.contains('user-message') || 
                  container.parentElement.classList.contains('human-message');
      }
      
      // 방법 4: 텍스트 내용으로 확인 (Human: 또는 Claude: 로 시작하는 텍스트)
      if (!isHuman && containerText.startsWith('Human:')) {
        isHuman = true;
      } else if (containerText.startsWith('Claude:') || containerText.startsWith('Assistant:')) {
        isHuman = false;
      }
      
      // 새로운 Claude 인터페이스용 추가 확인 방법
      if (!isHuman && parentClasses.some(cls => cls.includes('user') || cls.includes('human'))) {
        isHuman = true;
      } else if (parentClasses.some(cls => cls.includes('claude') || cls.includes('assistant'))) {
        isHuman = false;
      }
      
      // 메시지 텍스트 추출
      let messageText = '';
      let messageContent = null;
      
      // 메시지 콘텐츠 요소 찾기 시도
      const contentSelectors = [
        '.message-content', 
        '.claude-message-content', 
        '.user-message-content',
        '.whitespace-pre-wrap',
        '[role="paragraph"]',
        'p'
      ];
      
      for (const selector of contentSelectors) {
        const element = container.querySelector(selector);
        if (element) {
          messageContent = element;
          break;
        }
      }
      
      // 메시지 컨텐츠 요소를 찾지 못한 경우 컨테이너 자체를 사용
      if (!messageContent) {
        messageContent = container;
      }
      
      if (messageContent) {
        // 코드 블록, 텍스트 등 다양한 형식 처리
        const codeBlocks = messageContent.querySelectorAll('pre code, pre, code');
        
        if (codeBlocks.length > 0) {
          // 코드 블록이 있는 경우
          try {
            // 복잡한 DOM 구조에서 텍스트와 코드 블록을 추출하는 재귀 함수
            const extractTextAndCode = (element) => {
              if (!element) return '';
              
              // 텍스트 노드인 경우
              if (element.nodeType === Node.TEXT_NODE) {
                return element.textContent;
              }
              
              // 코드 블록인 경우
              if (element.tagName === 'PRE' || element.tagName === 'CODE' || element.querySelector('pre, code')) {
                const codeElement = element.tagName === 'CODE' ? element : element.querySelector('code') || element;
                const language = codeElement.className.replace('language-', '').trim() || '';
                return `\n\`\`\`${language}\n${codeElement.textContent}\n\`\`\`\n`;
              }
              
              // 복합 요소인 경우 재귀적으로 처리
              return Array.from(element.childNodes)
                .map(child => extractTextAndCode(child))
                .join('');
            };
            
            messageText = extractTextAndCode(messageContent);
          } catch (error) {
            console.error('[Claude Extractor] 코드 블록 처리 중 오류:', error);
            messageText = messageContent.textContent;
          }
        } else {
          // 일반 텍스트만 있는 경우
          messageText = messageContent.textContent;
        }
      }
      
      // 메시지가 의미 있는 내용을 가지고 있는지 확인
      const trimmedText = messageText.trim();
      if (trimmedText.length > 0) {
        // 중복 메시지 방지를 위한 간단한 해시 생성
        const messageHash = `${isHuman ? 'user' : 'assistant'}-${trimmedText.substring(0, 100)}`;
        
        // 중복 메시지 확인 (마지막 메시지와 동일한지)
        const isDuplicate = conversations.length > 0 && 
                          conversations[conversations.length - 1].role === (isHuman ? 'user' : 'assistant') &&
                          conversations[conversations.length - 1].content === trimmedText;
        
        if (!isDuplicate) {
          // 대화 객체 생성
          conversations.push({
            role: isHuman ? 'user' : 'assistant',
            content: trimmedText
          });
        }
      }
    });
    
    // 대화가 추출되지 않았거나 너무 적게 추출된 경우 (단일 메시지만 있는 경우)
    if (conversations.length === 0) {
      console.error('[Claude Extractor] 대화를 추출할 수 없습니다. 페이지 구조가 변경되었을 수 있습니다.');
      return {
        success: false,
        error: '대화를 추출할 수 없습니다. 페이지 구조가 변경되었거나 대화가 없습니다.',
        debugInfo: {
          url: window.location.href,
          documentTitle: document.title,
          bodyClasses: document.body.className
        }
      };
    }
    
    // 만약 현재 대화만 추출하는 경우, 가장 최근 교환만 반환
    if (currentOnly && conversations.length >= 2) {
      const lastIdx = conversations.length - 1;
      return {
        success: true,
        conversations: [
          conversations[lastIdx - 1],
          conversations[lastIdx]
        ]
      };
    }
    
    return { success: true, conversations };
  } catch (error) {
    console.error('Claude 대화 추출 중 오류 발생:', error);
    return { success: false, error: error.message };
  }
}

// 대화를 다양한 형식으로 변환
function formatConversation(conversations, format) {
  if (format === 'json') {
    const data = {
      conversations,
      timestamp: new Date().toISOString(),
      source: 'claude_conversation_extractor'
    };
    return JSON.stringify(data, null, 2);
  } else if (format === 'markdown') {
    return conversations.map(conv => {
      const role = conv.role === 'user' ? '## Human' : '## Claude';
      return `${role}:\n\n${conv.content}\n\n`;
    }).join('');
  } else { // 기본값: txt
    return conversations.map(conv => {
      const role = conv.role === 'user' ? 'Human' : 'Claude';
      return `${role}: ${conv.content}\n\n`;
    }).join('');
  }
}

// 파일 다운로드 함수
function downloadConversation(content, format) {
  const date = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const extension = format === 'json' ? 'json' : 
                   format === 'markdown' ? 'md' : 'txt';
  const filename = `claude_conversation_${date}.${extension}`;
  
  const blob = new Blob([content], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  
  URL.revokeObjectURL(url);
}

// 자동 저장 시작
function startAutoSave() {
  if (autoSaveTimer) {
    clearInterval(autoSaveTimer);
  }
  
  if (autoSaveEnabled) {
    console.log(`자동 저장 활성화: ${autoSaveInterval}분 간격`);
    autoSaveTimer = setInterval(performAutoSave, autoSaveInterval * 60 * 1000);
  }
}

// 자동 저장 수행
function performAutoSave() {
  const result = extractClaudeConversation(false);
  if (result.success) {
    const content = formatConversation(result.conversations, 'json');
    downloadConversation(content, 'json');
    
    // 사용자에게 알림
    const notification = document.createElement('div');
    notification.textContent = '대화가 자동 저장되었습니다.';
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.backgroundColor = 'rgba(76, 175, 80, 0.9)';
    notification.style.color = 'white';
    notification.style.padding = '10px 20px';
    notification.style.borderRadius = '4px';
    notification.style.zIndex = '9999';
    document.body.appendChild(notification);
    
    // 3초 후 알림 제거
    setTimeout(() => {
      document.body.removeChild(notification);
    }, 3000);
  }
}

// 메시지 리스너
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
  if (request.action === "extractConversation") {
    const result = extractClaudeConversation(request.currentOnly);
    
    if (result.success) {
      const content = formatConversation(result.conversations, request.format);
      downloadConversation(content, request.format);
    }
    
    sendResponse(result);
    return true;
  } 
  else if (request.action === "updateAutoSaveSettings") {
    autoSaveEnabled = request.enabled;
    autoSaveInterval = request.interval;
    startAutoSave();
    sendResponse({ success: true });
    return true;
  }
  else if (request.action === "debugPageStructure") {
    // 페이지 구조 디버깅 정보 수집 및 콘솔 출력
    debugPageStructure();
    sendResponse({ success: true });
    return true;
  }
});

// 현재 페이지 구조를 확인하고 디버그 정보 출력
function debugPageStructure() {
  console.log('[Claude Extractor] 페이지 구조 디버깅:');
  
  // 이미지에서 발견된 DOM 구조의 클래스명 포함
  const selectors = [
    // 일반 선택자
    '.claude-conversation-message',
    '[data-message-id]',
    '.message-content',
    '.message',
    '.message-container',
    '.conversation-message',
    '.chat-message',
    // 새로 발견된 선택자
    '.whitespace-pre-wrap',
    '.break-words',
    '.data-test-render-count',
    '.font-claude-message',
    '.sticky.bottom-0',
    '.absolute.bottom-0',
    '[aria-hidden="true"]',
    '.grid-gap-2',
    '[data-message]',
    '[role="paragraph"]'
  ];
  
  selectors.forEach(selector => {
    try {
      const elements = document.querySelectorAll(selector);
      console.log(`[Claude Extractor] ${selector}: ${elements.length}개 요소 발견`);
      
      // 첫 번째 요소의 텍스트 내용 샘플 표시
      if (elements.length > 0) {
        const sampleText = elements[0].textContent.substring(0, 50).replace(/\n/g, ' ') + 
                          (elements[0].textContent.length > 50 ? '...' : '');
        console.log(`[Claude Extractor] 샘플 텍스트: "${sampleText}"`);
      }
    } catch (error) {
      console.error(`[Claude Extractor] 선택자 ${selector} 검사 중 오류:`, error);
    }
  });
  
  // 페이지 URL 및 기타 정보 출력
  console.log('[Claude Extractor] 현재 URL:', window.location.href);
  console.log('[Claude Extractor] 현재 도메인:', window.location.hostname);
  console.log('[Claude Extractor] 경로:', window.location.pathname);
  console.log('[Claude Extractor] Body 클래스:', document.body.className);
  console.log('[Claude Extractor] HTML 클래스:', document.documentElement.className);
  console.log('[Claude Extractor] 페이지 타이틀:', document.title);
  
  // 가장 긴 텍스트를 가진 요소 찾기 (잠재적인 메시지 컨테이너)
  const allElements = document.querySelectorAll('div, p, span');
  let longestTextElement = null;
  let longestTextLength = 0;
  
  allElements.forEach(el => {
    const textLength = el.textContent.length;
    if (textLength > longestTextLength && textLength < 10000) {
      longestTextLength = textLength;
      longestTextElement = el;
    }
  });
  
  if (longestTextElement) {
    console.log('[Claude Extractor] 가장 긴 텍스트 요소:', longestTextElement);
    console.log('[Claude Extractor] 텍스트 길이:', longestTextLength);
    console.log('[Claude Extractor] 샘플:', longestTextElement.textContent.substring(0, 100) + '...');
    console.log('[Claude Extractor] 클래스:', longestTextElement.className);
  }
}

// 페이지가 완전히 로드된 후 지연 시간을 두고 초기화하는 함수
function delayedInitialization(retryCount = 0, maxRetries = 5) {
  console.log(`[Claude Extractor] 초기화 시도 #${retryCount + 1}`);
  
  // 디버그 정보 출력
  debugPageStructure();
  
  // 간단한 테스트 추출을 시도
  const testResult = extractClaudeConversation(true);
  if (testResult.success && testResult.conversations && testResult.conversations.length > 0) {
    console.log('[Claude Extractor] 메시지 추출 테스트 성공!', testResult.conversations.length, '개 메시지 발견');
    return; // 성공하면 중단
  }
  
  // 최대 재시도 횟수에 도달했는지 확인
  if (retryCount >= maxRetries) {
    console.log('[Claude Extractor] 최대 초기화 시도 횟수에 도달했습니다. 페이지 새로고침 또는 확장 프로그램 재설치가 필요할 수 있습니다.');
    return;
  }
  
  // 실패한 경우 재시도 (지수 백오프 적용)
  const delay = Math.pow(2, retryCount) * 1000; // 1s, 2s, 4s, 8s, 16s
  console.log(`[Claude Extractor] ${delay}ms 후에 다시 시도합니다...`);
  setTimeout(() => delayedInitialization(retryCount + 1, maxRetries), delay);
}

// 전역 상태 - 스크립트가 로드되었는지 확인
const SCRIPT_ID = 'claude-extractor-' + Math.random().toString(36).substring(2, 9);
let scriptLoaded = false;

// 다른 인스턴스가 이미 실행 중인지 확인
function checkForDuplicates() {
  if (window[SCRIPT_ID]) {
    console.warn('[Claude Extractor] 이미 다른 인스턴스가 실행 중입니다. 이 인스턴스는 비활성화됩니다.');
    return true;
  }
  
  // 이 인스턴스를 전역 공간에 등록
  window[SCRIPT_ID] = true;
  return false;
}

// 초기화 로직
function initialize() {
  // 중복 인스턴스 체크
  if (checkForDuplicates()) return;
  
  // 스크립트 로드 플래그 설정
  scriptLoaded = true;
  
  // 콘솔에 로드 메시지 출력
  console.log('[Claude Extractor] Claude Conversation Extractor v1.1 로드됨');
  console.log('[Claude Extractor] 스크립트 ID:', SCRIPT_ID);
  console.log('[Claude Extractor] 현재 URL:', window.location.href);
  
  // 저장된 자동 저장 설정 불러오기
  try {
    chrome.storage.sync.get(['autoSaveEnabled', 'autoSaveInterval'], function(data) {
      if (data) {
        autoSaveEnabled = data.autoSaveEnabled || false;
        autoSaveInterval = data.autoSaveInterval || 5;
        startAutoSave();
      }
    });
  } catch (error) {
    console.error('[Claude Extractor] 스토리지 접근 오류:', error);
  }
  
  // 페이지가 완전히 로드된 후 초기화
  if (document.readyState === 'complete') {
    // 즉시 초기화 시작
    delayedInitialization();
  } else {
    // 페이지 로드를 기다림
    window.addEventListener('load', function() {
      // 페이지 로드 후 약간의 지연 시간을 두고 초기화 (프레임워크가 DOM을 업데이트할 시간 제공)
      setTimeout(() => delayedInitialization(), 1000);
    });
  }
  
  // DOM 변경 감지 (대화 업데이트 등)
  try {
    const observer = new MutationObserver(function(mutations) {
      console.log('[Claude Extractor] DOM 변경 감지됨');
    });
    
    // 5초 후에 DOM 관찰 시작 (너무 많은 업데이트 방지)
    setTimeout(() => {
      observer.observe(document.body, { childList: true, subtree: true });
    }, 5000);
  } catch (error) {
    console.error('[Claude Extractor] MutationObserver 오류:', error);
  }
  
  // 페이지에 확장 프로그램이 로드되었음을 알리는 마커 추가
  try {
    const marker = document.createElement('div');
    marker.id = 'claude-extractor-marker';
    marker.style.display = 'none';
    marker.dataset.scriptId = SCRIPT_ID;
    marker.dataset.timestamp = new Date().toISOString();
    document.body.appendChild(marker);
  } catch (error) {
    console.error('[Claude Extractor] 마커 추가 오류:', error);
  }
}

// 페이지에 스크립트가 이미 로드되었는지 확인하는 함수
function isScriptAlreadyLoaded() {
  return !!document.getElementById('claude-extractor-marker');
}

// 초기화 즉시 실행
initialize();

// 백그라운드 스크립트로부터의 메시지 처리
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
  // 스크립트가 로드되었는지 확인하는 메시지
  if (request.action === "scriptLoaded") {
    console.log('[Claude Extractor] 백그라운드로부터 scriptLoaded 메시지 수신');
    sendResponse({
      success: true, 
      scriptId: SCRIPT_ID,
      url: window.location.href,
      alreadyLoaded: scriptLoaded,
      timestamp: new Date().toISOString()
    });
    return true;
  }
  
  // 기존 메시지 핸들러 유지
  if (request.action === "extractConversation") {
    const result = extractClaudeConversation(request.currentOnly);
    
    if (result.success) {
      const content = formatConversation(result.conversations, request.format);
      downloadConversation(content, request.format);
    }
    
    sendResponse(result);
    return true;
  } 
  else if (request.action === "updateAutoSaveSettings") {
    autoSaveEnabled = request.enabled;
    autoSaveInterval = request.interval;
    startAutoSave();
    sendResponse({ success: true });
    return true;
  }
  else if (request.action === "debugPageStructure") {
    // 페이지 구조 디버깅 정보 수집 및 콘솔 출력
    debugPageStructure();
    sendResponse({ 
      success: true,
      scriptId: SCRIPT_ID,
      url: window.location.href,
      timestamp: new Date().toISOString()
    });
    return true;
  }
  else if (request.action === "checkAlive") {
    sendResponse({ 
      alive: true, 
      scriptId: SCRIPT_ID,
      timestamp: new Date().toISOString()
    });
    return true;
  }
});
