// 스타일 및 레이아웃 문제 수정 스크립트

// 이미 스크립트가 실행되었는지 확인
// 한 번만 실행되도록 스크립트 실행 여부 표시
if (window.fixStylesInitialized) {
  console.log('fixStyles already initialized, skipping...');
} else {
  window.fixStylesInitialized = true;
  
  // 중복된 스타일시트와 레이아웃 요소를 정리하는 함수
  function cleanupDuplicates() {
    // 중복된 헤더 정리
    const headers = document.querySelectorAll('header');
    if (headers.length > 1) {
      // 첫 번째를 제외한 중복된 헤더 제거
      for (let i = 1; i < headers.length; i++) {
        headers[i].classList.add('dup-hidden');
      }
    }
    
    // 중복된 푸터 정리
    const footers = document.querySelectorAll('footer');
    if (footers.length > 1) {
      for (let i = 1; i < footers.length; i++) {
        footers[i].classList.add('dup-hidden');
      }
    }
    
    // 중복 스타일시트 제거
    const styles = document.querySelectorAll('style');
    const styleTexts = new Set();
    styles.forEach(style => {
      const text = style.textContent;
      if (styleTexts.has(text)) {
        style.remove();
      } else {
        styleTexts.add(text);
      }
    });
    
    // 컨테이너 마진 수정
    const containers = document.querySelectorAll('.MuiContainer-root');
    containers.forEach(container => {
      // 상단 마진 제거
      container.style.marginTop = '0';
      // 내부 패딩 추가
      container.style.paddingTop = '16px';
      container.style.paddingBottom = '16px';
    });
  }

  // 페이지 로드 후 실행
  window.addEventListener('load', () => {
    console.log('Fixing UI styles and layout...');
    cleanupDuplicates();
    
    // 100ms 후 다시 실행 (동적 컨텐츠 로딩 후)
    setTimeout(cleanupDuplicates, 100);
  });

  // MutationObserver를 사용하여 DOM 변경 감지 및 처리
  const styleObserver = new MutationObserver((mutations) => {
    let needsFixing = false;
    
    for (const mutation of mutations) {
      if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
        // 헤더나 푸터가 추가된 경우 확인
        for (const node of mutation.addedNodes) {
          if (node.tagName === 'HEADER' || node.tagName === 'FOOTER' || 
              (node.querySelector && (node.querySelector('header') || node.querySelector('footer')))) {
            needsFixing = true;
            break;
          }
        }
      }
      
      if (needsFixing) break;
    }
    
    if (needsFixing) {
      console.log('DOM changes detected, fixing styles...');
      cleanupDuplicates();
    }
  });

  // 문서 변경 감시 시작
  styleObserver.observe(document.body, { 
    childList: true, 
    subtree: true 
  });
}
