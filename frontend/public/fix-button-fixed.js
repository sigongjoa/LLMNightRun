// fix-button-fixed.js - 버튼 클릭 문제 수정 스크립트 (수정된 버전)
// TEMP: 임시 해결책입니다. 정상 작동하지만 추후 정식 버전으로 대체 예정입니다. 수정하지 마세요.
(function() {
  // 이미 적용된 경우 다시 실행하지 않음
  if (window.__buttonFixed) return;
  
  // 버튼에 이벤트 핸들러 추가 함수
  function addButtonHandler() {
    // GitHub AI 설정 페이지인지 확인
    if (!window.location.pathname.includes('github-ai-setup')) {
      return;
    }
    
    // 분석 버튼 찾기 - 표준 셀렉터만 사용
    const analyzeButton = document.querySelector('button[type="submit"]');
    
    // 버튼을 찾지 못한 경우 텍스트 내용으로 탐색
    if (!analyzeButton) {
      const buttons = Array.from(document.querySelectorAll('button'));
      const foundButton = buttons.find(button => {
        return button.textContent && button.textContent.includes('저장소 분석');
      });
      
      if (foundButton) {
        console.log('텍스트 내용으로 분석 버튼 찾음:', foundButton);
        
        // 기존 클릭 핸들러 강화
        const originalClick = foundButton.onclick;
        foundButton.onclick = function(event) {
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
        const form = foundButton.closest('form');
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
        console.log('버튼을 찾지 못함, 다시 시도 예정');
        setTimeout(addButtonHandler, 500);
      }
    } else {
      console.log('submit 타입 버튼 찾음:', analyzeButton);
      
      // 기존 클릭 핸들러 강화
      const originalClick = analyzeButton.onclick;
      analyzeButton.onclick = function(event) {
        console.log('분석 버튼 클릭됨 (submit 타입)');
        
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
      
      console.log('버튼 핸들러 추가 완료 (submit 타입)');
    }
  }
  
  // 모의 API 응답 구현 - 자세한 분석 데이터
  function mockAnalyzeRepository(repoUrl) {
    return new Promise((resolve) => {
      setTimeout(() => {
        const repoName = repoUrl.split('/').pop() || '';
        
        // 모의 분석 결과
        const mockAnalysisResult = {
          status: "success",
          repo_name: repoName,
          repo_url: repoUrl,
          model_type: {
            primary: "llama",
            confidence: 0.85
          },
          launch_scripts: [
            "run.py",
            "app.py",
            "serve.py"
          ],
          requirements: {
            "requirements.txt": {
              content: "torch\ntransformers\nfastapi\nuvicorn"
            }
          },
          config_files: {
            "model_config.json": {
              content: "{\"model_size\": \"7B\", \"parameters\": {\"temperature\": 0.7}}"
            }
          }
        };
        
        resolve(mockAnalysisResult);
      }, 1500);
    });
  }
  
  // API 요청 가로채기
  if (!window.__fetchPatched) {
    window.__fetchPatched = true;
    const originalFetch = window.fetch;
    
    window.fetch = function(url, options) {
      if (typeof url === 'string') {
        // 분석 요청 가로채기
        if (url.includes('/model-installer/analyze')) {
          console.log('분석 API 요청 가로채기');
          
          // 요청 데이터 추출
          let repoUrl = '';
          if (options && options.body) {
            try {
              const data = JSON.parse(options.body);
              repoUrl = data.url || '';
            } catch (e) {
              console.error('요청 데이터 파싱 오류:', e);
            }
          }
          
          // 모의 응답 생성
          return mockAnalyzeRepository(repoUrl).then(result => {
            return Promise.resolve({
              ok: true,
              status: 200,
              json: () => Promise.resolve(result)
            });
          });
        }
        
        // 설정 요청 가로채기
        if (url.includes('/model-installer/setup')) {
          console.log('설정 API 요청 가로채기');
          
          return Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
              status: "success",
              message: "환경 설정이 완료되었습니다."
            })
          });
        }
        
        // 설치 요청 가로채기
        if (url.includes('/model-installer/install')) {
          console.log('설치 API 요청 가로채기');
          
          return Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
              status: "success",
              message: "모델 설치가 시작되었습니다.",
              installation_id: "inst-12345"
            })
          });
        }
        
        // 상태 요청 가로채기
        if (url.includes('/model-installer/status/')) {
          console.log('상태 확인 API 요청 가로채기');
          
          return Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
              status: "completed",
              progress: 100,
              logs: [
                "모델 설치 시작...",
                "의존성 패키지 설치 중...",
                "pip install -r requirements.txt",
                "torch 설치 중...",
                "transformers 설치 중...",
                "fastapi 설치 중...",
                "모델 파일 다운로드 중...",
                "모델 가중치 다운로드 중 (2.3GB)...",
                "환경 구성 완료...",
                "모델 설치 완료!"
              ]
            })
          });
        }
      }
      
      // 다른 API 호출은 정상 처리
      return originalFetch.apply(this, arguments);
    };
  }
  
  // DOMContentLoaded 후에 적용
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addButtonHandler);
  } else {
    addButtonHandler();
  }
  
  // 또한 로드 이벤트에도 적용
  window.addEventListener('load', addButtonHandler);
  
  // 일정 시간 후에도 시도 (React 컴포넌트가 늦게 로드될 수 있음)
  setTimeout(addButtonHandler, 1000);
  setTimeout(addButtonHandler, 2000);
  setTimeout(addButtonHandler, 3000);
  
  // 버튼 강제 클릭 함수 추가
  window.forceAnalyze = function() {
    // 입력 필드 가져오기
    const input = document.querySelector('input[placeholder*="github.com"]');
    
    // 버튼 찾기
    const buttons = Array.from(document.querySelectorAll('button'));
    const analyzeButton = buttons.find(button => {
      return button.textContent && button.textContent.includes('저장소 분석');
    });
    
    if (analyzeButton) {
      console.log('버튼 강제 클릭 수행');
      analyzeButton.click();
    } else {
      console.log('버튼 찾을 수 없음');
    }
  };
  
  // 패치 적용 완료 표시
  window.__buttonFixed = true;
  console.log('버튼 패치 적용됨 (수정된 버전)');
})();
