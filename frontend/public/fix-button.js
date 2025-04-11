// fix-button.js - 버튼 클릭 문제 수정 스크립트
(function() {
  // 이미 적용된 경우 다시 실행하지 않음
  if (window.__buttonFixed) return;
  
  // 버튼에 이벤트 핸들러 추가 함수
  function addButtonHandler() {
    // GitHub AI 설정 페이지인지 확인
    if (!window.location.pathname.includes('github-ai-setup')) {
      return;
    }
    
    // 분석 버튼 찾기
    const analyzeButton = document.querySelector('button[type="submit"], button:contains("저장소 분석")');
    if (analyzeButton) {
      console.log('분석 버튼 찾음:', analyzeButton);
      
      // 기존 클릭 핸들러 강화
      const originalClick = analyzeButton.onclick;
      analyzeButton.onclick = function(event) {
        console.log('분석 버튼 클릭됨');
        
        // 입력 필드 가져오기
        const input = document.querySelector('input[placeholder*="github.com"]');
        if (!input || !input.value.trim()) {
          alert('GitHub 저장소 URL을 입력해주세요.');
          event.preventDefault();
          return false;
        }
        
        // 기존 클릭 핸들러 실행 (있는 경우)
        if (typeof originalClick === 'function') {
          return originalClick.call(this, event);
        }
      };
      
      // 폼 제출 이벤트도 처리
      const form = analyzeButton.closest('form');
      if (form) {
        const originalSubmit = form.onsubmit;
        form.onsubmit = function(event) {
          console.log('폼 제출됨');
          
          // 입력 필드 가져오기
          const input = document.querySelector('input[placeholder*="github.com"]');
          if (!input || !input.value.trim()) {
            alert('GitHub 저장소 URL을 입력해주세요.');
            event.preventDefault();
            return false;
          }
          
          // 기존 제출 핸들러 실행 (있는 경우)
          if (typeof originalSubmit === 'function') {
            return originalSubmit.call(this, event);
          }
        };
      }
      
      console.log('버튼 핸들러 추가 완료');
    } else {
      // 버튼을 찾지 못한 경우 다시 시도
      setTimeout(addButtonHandler, 500);
    }
  }
  
  // DOMContentLoaded 후에 적용
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addButtonHandler);
  } else {
    addButtonHandler();
  }
  
  // 또한 로드 이벤트에도 적용
  window.addEventListener('load', addButtonHandler);
  
  // 패치 적용 완료 표시
  window.__buttonFixed = true;
  console.log('버튼 패치 적용됨');
})();
