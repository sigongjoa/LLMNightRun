// Special function for Claude to send message directly with keyboard events
function sendMessageWithKeyboard(inputElement, message) {
  console.log('Attempting special Claude keyboard method');
  
  // Focus the input
  inputElement.focus();
  
  // Clear existing content if needed
  if (inputElement.tagName === 'TEXTAREA') {
    inputElement.value = '';
  } else if (inputElement.getAttribute('contenteditable') === 'true') {
    inputElement.innerHTML = '';
  }
  
  // Add the message
  if (inputElement.tagName === 'TEXTAREA') {
    inputElement.value = message;
  } else if (inputElement.getAttribute('contenteditable') === 'true') {
    inputElement.innerHTML = message;
  }
  
  // Trigger a series of events
  const events = [
    new Event('input', { bubbles: true }),
    new Event('change', { bubbles: true }),
    new KeyboardEvent('keydown', { bubbles: true, keyCode: 13, key: 'Enter' }),
    new KeyboardEvent('keypress', { bubbles: true, keyCode: 13, key: 'Enter' }),
    new KeyboardEvent('keyup', { bubbles: true, keyCode: 13, key: 'Enter' })
  ];
  
  // Fire all events
  events.forEach(event => {
    inputElement.dispatchEvent(event);
  });
  
  // Finally simulate Enter key with all possible properties
  setTimeout(() => {
    const enterEvent = new KeyboardEvent('keydown', {
      bubbles: true,
      cancelable: true,
      key: 'Enter',
      code: 'Enter',
      keyCode: 13,
      which: 13,
      location: 0,
      ctrlKey: false,
      shiftKey: false,
      altKey: false,
      metaKey: false
    });
    inputElement.dispatchEvent(enterEvent);
    
    console.log('Completed keyboard-based sending attempt');
  }, 100);
  
  return true;
}

// Log that content script has loaded
console.log('AI Chat Helper: Content script loaded successfully on ' + window.location.href);

// Notify the background script that content script is loaded
try {
  chrome.runtime.sendMessage({ action: "contentScriptLoaded", url: window.location.href });
} catch (error) {
  console.error('Error notifying background script:', error);
}

// Special function for Claude message extraction
function extractClaudeMessages() {
  console.log('Using specialized Claude message extraction');
  
  // Let's look for specific Claude patterns
  // First, find the main conversation area
  const messageContainers = [];
  
  // Get all elements that have text content > 20 chars and look like they could be messages
  const allElements = document.querySelectorAll('div, section, article, p');
  const contentElements = Array.from(allElements).filter(el => {
    const text = el.innerText?.trim();
    if (!text || text.length < 20) return false;
    
    // Skip elements that are likely inputs or UI elements
    if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') return false;
    if (el.getAttribute('contenteditable') === 'true') return false;
    if (el.classList && (el.classList.contains('input') || el.classList.contains('textarea'))) return false;
    
    // Skip elements with too many child elements (likely UI containers)
    if (el.children.length > 20) return false;
    
    return true;
  });
  
  console.log(`Found ${contentElements.length} potential message elements`);
  
  // Sort by position in page (top to bottom)
  contentElements.sort((a, b) => {
    const rectA = a.getBoundingClientRect();
    const rectB = b.getBoundingClientRect();
    return rectA.top - rectB.top;
  });
  
  // Group elements by apparent sections (messages)
  // We'll use vertical position to determine if elements are part of the same message
  let lastTop = -1;
  let currentGroup = [];
  const messageGroups = [];
  
  contentElements.forEach(el => {
    const rect = el.getBoundingClientRect();
    
    // If this element is far from the last one, it's probably a new message
    if (lastTop === -1 || rect.top - lastTop > 50) {
      if (currentGroup.length > 0) {
        messageGroups.push(currentGroup);
      }
      currentGroup = [el];
    } else {
      currentGroup.push(el);
    }
    
    lastTop = rect.top;
  });
  
  // Add the last group
  if (currentGroup.length > 0) {
    messageGroups.push(currentGroup);
  }
  
  console.log(`Grouped into ${messageGroups.length} potential messages`);
  
  // Process each group to create message objects
  const messages = [];
  let userMessageCount = 0;
  let assistantMessageCount = 0;
  
  messageGroups.forEach((group, index) => {
    // Determine if this is likely a user or assistant message
    // For Claude, user messages are usually shorter and might be on the right side
    // Assistant messages are usually longer and may contain formatting
    
    // Get the full text of this group
    const groupText = group.map(el => el.innerText.trim()).join('\n');
    
    // Heuristics for role detection:
    // 1. Position - usually alternates
    // 2. Length - user messages typically shorter
    // 3. Style/class - may have user/assistant indicators
    
    let isUserMessage = false;
    
    // Check position classes (may indicate right-aligned)
    const hasRightAlignClasses = group.some(el => {
      const classList = el.className || '';
      return classList.includes('right') || 
             classList.includes('user') || 
             classList.includes('human') || 
             getComputedStyle(el).textAlign === 'right';
    });
    
    // Check if contains a user indicator class
    const hasUserClasses = group.some(el => {
      const classList = el.className || '';
      return classList.includes('user') || classList.includes('human');
    });
    
    // Check if contains an assistant indicator class
    const hasAssistantClasses = group.some(el => {
      const classList = el.className || '';
      return classList.includes('assistant') || 
             classList.includes('ai') || 
             classList.includes('claude') || 
             classList.includes('bot');
    });
    
    // Make determination based on collected evidence
    if (hasUserClasses || hasRightAlignClasses) {
      isUserMessage = true;
    } else if (hasAssistantClasses) {
      isUserMessage = false;
    } else {
      // If we can't determine by classes, use length and position
      if (groupText.length < 200 && (index % 2 === 0)) {
        isUserMessage = true;
      } else if (index % 2 === 0) {
        // First message is typically user
        isUserMessage = true;
      } else {
        isUserMessage = false;
      }
    }
    
    if (isUserMessage) {
      userMessageCount++;
    } else {
      assistantMessageCount++;
    }
    
    // Create the message object
    messages.push({
      id: `message-${index + 1}`,
      role: isUserMessage ? 'user' : 'assistant',
      content: group.map(el => el.innerHTML || el.innerText).join('\n'),
      text_content: groupText,
      timestamp: new Date().toISOString()
    });
  });
  
  console.log(`Created ${messages.length} messages (${userMessageCount} user, ${assistantMessageCount} assistant)`);
  
  return messages;
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
      
      // Check if it's a Claude page
      const isClaudePage = window.location.href.includes('claude.ai');
      let conversation;
      
      if (isClaudePage) {
        console.log('Detected Claude page, using specialized extraction');
        const messages = extractClaudeMessages();
        
        // Create conversation object in the expected format
        conversation = {
          title: document.title.replace(" - Claude", ""),
          create_time: new Date().toISOString(),
          update_time: new Date().toISOString(),
          mapping: {},
          messages: []
        };
        
        // Add messages to the mapping
        messages.forEach(message => {
          conversation.mapping[message.id] = message;
          conversation.messages.push(message.id);
        });
        
      } else {
        // Use the regular extraction for other pages
        conversation = extractConversation();
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
  }
});

// Function to send a message
function sendMessage(message) {
  if (!message) {
    throw new Error("메시지가 비어있습니다.");
  }
  
  console.log('Attempting to send message:', message);
  
  // Try different input selectors for different chat platforms
  let inputElement = null;
  let sendButton = null;  // Initialize sendButton variable here
  
  // ChatGPT selectors
  const chatgptSelectors = [
    'textarea[data-id="root"]', 
    'textarea[placeholder="Send a message"]',
    'div[role="textbox"]',
    '.chat-input textarea'
  ];
  
  // Claude selectors
  const claudeSelectors = [
    'div[contenteditable="true"]',
    '.cl-textgenerationtextarea-input',
    '.chat-input div[contenteditable]',
    'footer textarea', // Claude의 새로운 DOM 구조
    '.editor-wrapper textarea', // 또 다른 가능한 selector
    'textarea[placeholder*="메시지"]', // 한국어 클로드
    'textarea[placeholder*="message"]' // 영어 클로드
  ];
  
  // Try all possible selectors
  const allSelectors = [...chatgptSelectors, ...claudeSelectors];
  
  for (const selector of allSelectors) {
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

  // Claude에 최적화된 방법 시도 (keyboard events만 사용)
  const isClaudePage = window.location.href.includes('claude.ai');
  if (isClaudePage) {
    console.log('Detected Claude page, trying specialized keyboard method');
    const result = sendMessageWithKeyboard(inputElement, message);
    if (result) {
      console.log('Used specialized Claude keyboard method');
      return;
    }
  }
  
  // Focus the input element
  inputElement.focus();
  
  // Set the value for textarea elements
  if (inputElement.tagName === 'TEXTAREA') {
    inputElement.value = message;
    
    // Trigger input event to activate the send button
    inputElement.dispatchEvent(new Event('input', { bubbles: true }));
  } 
  // Set innerHTML for contenteditable divs (Claude)
  else if (inputElement.getAttribute('contenteditable') === 'true') {
    inputElement.innerHTML = message;
    
    // Trigger input event
    inputElement.dispatchEvent(new Event('input', { bubbles: true }));
    inputElement.dispatchEvent(new Event('change', { bubbles: true }));
    
    // Claude에서 한국어 메시지 입력 후 추가 이벤트 발생 시도
    // keyup 및 keydown 이벤트도 트리거
    inputElement.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true }));
    inputElement.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
    inputElement.dispatchEvent(new KeyboardEvent('input', { bubbles: true }));
  }
  
  // Common send button selectors
  const sendButtonSelectors = [
    'button[data-testid="send-button"]',
    'button.chat-send-button',
    'button[aria-label="Send message"]',
    'button.send',
    'button[type="submit"]',
    'form button',
    '.chat-input button',
    'button.primary',
    '.send-button',
    // 클로드 특화 선택자
    'footer button',  // 클로드 푸터의 전송 버튼
    'footer div[role="button"]', // 역할 속성 사용
    'footer svg', // SVG 아이콘 직접 클릭
    '.editor-wrapper button', // 에디터 주변 버튼
    'button:has(svg)' // SVG를 포함한 버튼 (이 선택자는 일부 브라우저에서 작동하지 않을 수 있음)
  ];
  
  // 단순히 버튼 목록을 순회하는 대신 특별한 로직 추가
  // 클로드 전송 버튼을 더 정확하게 찾기 위한 시도
  
  // 1. 먼저 일반적인 버튼 선택자로 시도
  for (const selector of sendButtonSelectors) {
    try {
      const buttons = document.querySelectorAll(selector);
      if (buttons.length > 0) {
        // 가장 아래에 있는 버튼이 전송 버튼일 가능성이 높음
        for (const button of buttons) {
          // 버튼의 영역 확인 (보이는지 여부)
          const rect = button.getBoundingClientRect();
          if (rect.width > 0 && rect.height > 0) {
            // 텍스트 내용이나 버튼 위치로 판단
            if (
              button.textContent?.includes('send') ||
              button.textContent?.includes('전송') ||
              button.innerHTML?.includes('plane') ||
              button.innerHTML?.includes('send') ||
              button.innerHTML?.includes('arrow') ||
              (button.classList.contains('send') || button.classList.contains('submit') || 
               button.classList.contains('primary')) ||
              // 입력 필드 옆에 있는지 확인
              (inputElement && Math.abs(button.getBoundingClientRect().left - 
                                  (inputElement.getBoundingClientRect().right + 50)) < 100)
            ) {
              sendButton = button;
              console.log('Found good send button candidate with selector:', selector);
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
  
  // 2. 만약 일반 선택자로 찾지 못했다면, 위치 기반 추론 (클로드에 효과적)
  if (!sendButton) {
    console.log('No button found with standard selectors, trying position-based detection');
    // 페이지에서 모든 버튼 요소 찾기
    const allButtons = document.querySelectorAll('button, div[role="button"], span[role="button"]');
    
    // 입력 필드 주변에 있는지 확인
    if (inputElement) {
      const inputRect = inputElement.getBoundingClientRect();
      
      // 입력 필드 근처에서 가장 적합한 버튼 후보 찾기
      let bestCandidate = null;
      let minDistance = Infinity;
      
      for (const btn of allButtons) {
        const btnRect = btn.getBoundingClientRect();
        
        // 버튼이 보이는지 확인
        if (btnRect.width > 0 && btnRect.height > 0) {
          // 버튼이 화면에 보이는지 확인
          if (btnRect.top > 0 && btnRect.bottom < window.innerHeight) {
            // 입력 필드 오른쪽 또는 아래에 있는지 확인
            const horizontalProximity = Math.abs(btnRect.left - inputRect.right);
            const verticalProximity = Math.abs(btnRect.top - inputRect.bottom);
            
            // 가중치를 적용한 거리 계산
            const weightedDistance = horizontalProximity + verticalProximity * 0.5;
            
            if (weightedDistance < minDistance) {
              minDistance = weightedDistance;
              bestCandidate = btn;
            }
          }
        }
      }
      
      if (bestCandidate && minDistance < 200) { // 거리 임계값 설정
        sendButton = bestCandidate;
        console.log('Found button using position-based detection, distance:', minDistance);
      }
    }
    
    // 3. 마지막 수단: 페이지 하단에 있는 SVG를 포함한 요소 찾기 (클로드 특화)
    if (!sendButton) {
      console.log('Trying to find SVG in footer area');
      const svgElements = document.querySelectorAll('svg');
      let footerSvg = null;
      
      // 가장 아래에 있는 svg 요소를 찾음
      for (const svg of svgElements) {
        const rect = svg.getBoundingClientRect();
        // 화면에 보이는 SVG이고, 페이지 하단 30% 영역에 있는지 확인
        if (rect.width > 0 && rect.height > 0 && rect.top > window.innerHeight * 0.7) {
          footerSvg = svg;
          break;
        }
      }
      
      if (footerSvg) {
        // SVG의 부모 요소 중에서 클릭 가능한 요소 찾기
        let clickableParent = footerSvg;
        for (let i = 0; i < 3; i++) { // 최대 3단계 부모까지 확인
          if (clickableParent.parentElement) {
            clickableParent = clickableParent.parentElement;
            // 클릭 가능한 요소인지 확인
            if (clickableParent.tagName === 'BUTTON' || 
                clickableParent.getAttribute('role') === 'button' ||
                clickableParent.onclick ||
                window.getComputedStyle(clickableParent).cursor === 'pointer') {
              sendButton = clickableParent;
              console.log('Found clickable parent of SVG in footer');
              break;
            }
          } else {
            break;
          }
        }
        
        // 클릭 가능한 부모를 찾지 못했다면 SVG 자체를 클릭
        if (!sendButton) {
          sendButton = footerSvg;
          console.log('Using footer SVG directly as send button');
        }
      }
    }
  }
  
  // If no send button found, try to submit via keyboard event
  if (!sendButton) {
    console.log('No send button found, trying keyboard event');
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
    return;
  }
  
  // Click the send button
  if (sendButton) {
    console.log('Clicking send button:', sendButton.tagName, sendButton.className);
    
    // 여러 이벤트 트리거로 시도
    try {
      // 1. 표준 클릭 메서드
      sendButton.click();
      
      // 2. 마우스 이벤트 시뮬레이션
      sendButton.dispatchEvent(new MouseEvent('click', {
        view: window,
        bubbles: true,
        cancelable: true
      }));
      
      // 3. mousedown/mouseup 이벤트 시뮬레이션
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
    console.log('No send button available, using keyboard event as fallback');
  }
}

// Function to extract conversation
function extractConversation() {
  console.log('Starting conversation extraction');
  // 1. Get the thread container - handling multiple possible DOM structures
  let threadContainer = null;
  
  // For ChatGPT structure
  const chatgptContainer = document.querySelector('div[class*="react-scroll-to-bottom"] > div > div');
  
  // For Claude structure - extended selectors
  const claudeContainers = [
    document.querySelector('.chat-content, .cl-msgs-container'),
    document.querySelector('.cl-thread'),
    document.querySelector('.cl-thread-container'),
    document.querySelector('[class*="thread"]'),
    document.querySelector('main > div > div'),
    document.querySelector('main'),
    document.querySelector('[class*="conversation-container"]'),
    document.querySelector('[class*="message-list"]')
  ].filter(Boolean); // Remove null/undefined
  
  // Find the first container with children
  const claudeContainer = claudeContainers.find(container => 
    container && container.children && container.children.length > 2
  );
  
  // Set the appropriate container
  if (chatgptContainer) {
    threadContainer = chatgptContainer;
    console.log('Using ChatGPT container');
  } else if (claudeContainer) {
    threadContainer = claudeContainer;
    console.log('Using Claude container:', claudeContainer.className);
  } else {
    // Try a more generic approach for any chat interface
    console.log('Trying generic container approach');
    const possibleContainers = document.querySelectorAll('main div, .chat-container, .message-container');
    for (const container of possibleContainers) {
      // Look for a container with multiple child elements that likely contains messages
      if (container.children.length > 3) {
        threadContainer = container;
        break;
      }
    }
  }
  
  if (!threadContainer) {
    console.error('Thread container not found!');
    // Try to log what is available in the DOM
    console.log('Document body HTML structure (first 1000 chars):', document.body.innerHTML.substring(0, 1000));
    console.log('All potential containers:', document.querySelectorAll('main, [class*="chat"], [class*="message"], [class*="thread"]'));
    throw new Error("대화 스레드를 찾을 수 없습니다.");
  }
  
  console.log('Thread container found with children count:', threadContainer.children.length);
  
  // 2. Extract all message blocks - with broader selector patterns
  const messageBlocks = Array.from(threadContainer.querySelectorAll(
    // Common message container classes/attributes across different chat platforms
    '.message, .chat-message, .message-container, div[class*="message"], div[class*="group"], ' +
    'div[role="listitem"], div[data-message], div[data-testid*="message"], ' +
    'div[class*="human"], div[class*="assistant"], div[class*="user"], ' +
    'div[data-message-author-role], div[class*="bubble"]'
  ));
  
  console.log('Initial message blocks found:', messageBlocks.length);
  
  // If no specific message blocks were found, try more aggressive approaches
  if (messageBlocks.length === 0) {
    console.log('No specific message blocks found, trying additional selectors...');
    
    // 1. Try with more generic selectors for Claude
    const claudeMessageSelectors = [
      '.cl-message',
      '.cl-message-container',
      '[class*="message-container"]',
      '[class*="message_"]',
      '[class*="Message_"]',
      '.cl-user-message, .cl-assistant-message',
      '[data-message]',
      'main > div > div > div' // Very generic last resort
    ];
    
    for (const selector of claudeMessageSelectors) {
      const foundMessages = threadContainer.querySelectorAll(selector);
      if (foundMessages && foundMessages.length > 0) {
        console.log(`Found ${foundMessages.length} messages using selector: ${selector}`);
        messageBlocks.push(...Array.from(foundMessages));
        break;
      }
    }
    
    // 2. If still nothing, get direct children of the thread container
    if (messageBlocks.length === 0) {
      console.log('No specific message blocks found, using direct children');
      const directChildren = Array.from(threadContainer.children).filter(child => {
        // Filter out any obvious non-message elements
        return (
          child.textContent.trim() && 
          !child.className.includes('typing') && 
          !child.className.includes('input') && 
          !child.className.includes('composer')
        );
      });
      
      if (directChildren.length > 0) {
        messageBlocks.push(...directChildren);
        console.log('Added direct children as message blocks, new count:', messageBlocks.length);
      }
      
      // 3. Last resort - use all divs with text
      if (messageBlocks.length === 0) {
        console.log('No direct children found, using all divs with content');
        const allDivsWithContent = threadContainer.querySelectorAll('div');
        const filteredDivs = Array.from(allDivsWithContent).filter(div => {
          // Take only divs that have text and look like they could be messages
          const text = div.textContent.trim();
          return text.length > 20 && !div.className.includes('typing') && 
                 !div.querySelector('input') && !div.querySelector('textarea');
        });
        
        if (filteredDivs.length > 0) {
          // Take only the most likely candidates
          // Sort by text length - messages are usually longer
          filteredDivs.sort((a, b) => 
            b.textContent.trim().length - a.textContent.trim().length
          );
          
          // Take top 20 - normally a conversation doesn't have hundreds of messages displayed
          const topDivs = filteredDivs.slice(0, 20);
          messageBlocks.push(...topDivs);
          console.log('Added top divs with content as message blocks, new count:', messageBlocks.length);
        }
      }
    }
  }
  
  if (messageBlocks.length === 0) {
    console.log('DOM structure:', threadContainer.outerHTML.substring(0, 500));
    throw new Error("메시지를 찾을 수 없습니다.");
  }
  
  // 3. Process each message block
  const conversation = {
    title: document.title.replace(" - ChatGPT", "").replace(" - Claude", ""),
    create_time: new Date().toISOString(),
    update_time: new Date().toISOString(),
    mapping: {},
    messages: []
  };
  
  let messageId = 1;
  
  // Function to recursively get all text content, preserving some structure
  function getTextContent(element) {
    if (!element) return '';
    
    // If it's a code block, we want to preserve its formatting
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
  
  messageBlocks.forEach((block, index) => {
    // Determine if it's a user or assistant message using multiple possible indicators
    
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
                             block.className.includes('ai');
    const hasUserClass = block.className.includes('user') || 
                        block.className.includes('human');
    
    // Position indicator (in many interfaces user messages are on the right)
    const possibleUserAlign = window.getComputedStyle(block).textAlign === 'right' || 
                             window.getComputedStyle(block).alignSelf === 'flex-end';
    
    // Combine all indicators
    const isAssistantMessage = hasChatGPTImg || hasAssistantRole || hasAssistantClass;
    const isUserMessage = hasUserImg || hasUserRole || hasUserClass || (possibleUserAlign && !isAssistantMessage);
    
    let role = 'unknown';
    
    // Skip if we can't determine the role
    if (!isUserMessage && !isAssistantMessage) {
      // Try to infer role based on position if this is not the first message
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
        // First message is typically from the system or assistant
        role = 'assistant';
      } else {
        // If we still can't determine, use alternating pattern
        role = (index % 2 === 0) ? 'user' : 'assistant';
      }
    } else {
      role = isUserMessage ? 'user' : 'assistant';
    }
    
    console.log(`Message ${index}, determined role: ${role}`);
    
    // Extract message content with improved content detection
    let contentElement = null;
    
    // Try different possible selectors based on various chat platforms
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
    
    // Try each selector until we find a match
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
    
    // Extract both HTML content and text content with special handling
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
    const sender = message.role === 'user' ? '**사용자**' : '**AI**';
    
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
    const sender = message.role === 'user' ? '사용자' : 'AI';
    
    text += `[${sender}] - ${new Date(message.timestamp).toLocaleString()}\n`;
    text += `${message.text_content}\n\n`;
  });
  
  return text;
}

// Log that the content script has loaded at the end
console.log("AI Chat Helper - 콘텐츠 스크립트 로드 완료");
