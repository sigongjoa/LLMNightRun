// 스타일 및 레이아웃 문제 수정 스크립트

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
  
  // 중복된 Material-UI 스타일시트 찾기 및 제거
  const styleSheets = document.styleSheets;
  const cssRules = new Map();
  
  for (let i = 0; i < styleSheets.length; i++) {
    try {
      const sheet = styleSheets[i];
      const rules = sheet.cssRules;
      if (!rules) continue;
      
      let cssText = '';
      for (let j = 0; j < rules.length; j++) {
        cssText += rules[j].cssText;
      }
      
      if (cssRules.has(cssText)) {
        // 중복된 스타일시트 제거
        sheet.disabled = true;
      } else {
        cssRules.set(cssText, sheet);
      }
    } catch (e) {
      // CORS 오류 무시 (외부 스타일시트는 접근할 수 없음)
      console.warn('Stylesheet access error:', e);
    }
  }
  
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

// Next.js의 route 변경 이벤트에도 대응
if (typeof window !== 'undefined' && window.next) {
  window.next.router.events.on('routeChangeComplete', () => {
    console.log('Route changed, fixing UI styles...');
    setTimeout(cleanupDuplicates, 50);
  });
}
