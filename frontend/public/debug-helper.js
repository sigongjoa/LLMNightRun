// debug-helper.js - 콘솔에서 수동으로 문제 해결에 도움이 되는 스크립트
// TEMP: 임시 디버깅 도구입니다. 개발/테스트용으로만 사용되어야 하며 추후 제거 예정입니다. 수정하지 마세요.

// 1. 버튼 강제 클릭 함수
function forceClickButton() {
  // 모든 버튼 찾기
  const buttons = Array.from(document.querySelectorAll('button'));
  console.log('페이지의 모든 버튼:', buttons);
  
  // 분석 버튼 찾기
  const analyzeButton = buttons.find(btn => {
    return btn.textContent && btn.textContent.includes('저장소 분석');
  });
  
  if (analyzeButton) {
    console.log('저장소 분석 버튼을 찾았습니다:', analyzeButton);
    console.log('버튼을 강제로 클릭합니다...');
    analyzeButton.click();
    return true;
  } else {
    console.error('저장소 분석 버튼을 찾을 수 없습니다.');
    return false;
  }
}

// 2. 모든 입력 필드 검사
function checkInputs() {
  const inputs = Array.from(document.querySelectorAll('input'));
  console.log('페이지의 모든 입력 필드:', inputs);
  
  // GitHub 입력 필드 찾기
  const githubInput = inputs.find(input => {
    return input.placeholder && input.placeholder.includes('github.com');
  });
  
  if (githubInput) {
    console.log('GitHub 입력 필드를 찾았습니다:', githubInput);
    console.log('현재 값:', githubInput.value);
    
    // 입력 필드가 비어있으면 값 설정
    if (!githubInput.value.trim()) {
      githubInput.value = 'https://github.com/suksham11/MLTradingbot';
      console.log('입력 필드에 값을 설정했습니다.');
    }
    
    return true;
  } else {
    console.error('GitHub 입력 필드를 찾을 수 없습니다.');
    return false;
  }
}

// 3. 단계 강제 진행
function forceNextStep() {
  // 현재 활성 단계 찾기
  const activeStep = document.querySelector('.Mui-active');
  if (!activeStep) {
    console.error('활성 단계를 찾을 수 없습니다.');
    return false;
  }
  
  // 모든 단계 가져오기
  const steps = Array.from(document.querySelectorAll('.MuiStepLabel-root'));
  console.log('스텝퍼의 모든 단계:', steps);
  
  // 현재 활성 단계 인덱스 찾기
  const currentIndex = steps.findIndex(step => step.querySelector('.Mui-active'));
  if (currentIndex === -1) {
    console.error('현재 단계 인덱스를 찾을 수 없습니다.');
    return false;
  }
  
  console.log('현재 단계:', currentIndex + 1);
  
  // 다음 단계가 있는지 확인
  if (currentIndex < steps.length - 1) {
    // 다음 단계 버튼 찾기
    const nextButton = document.querySelector('button');
    if (nextButton) {
      console.log('다음 버튼을 찾았습니다:', nextButton);
      console.log('다음 단계로 강제 이동합니다...');
      nextButton.click();
      return true;
    } else {
      console.error('다음 버튼을 찾을 수 없습니다.');
      return false;
    }
  } else {
    console.log('이미 마지막 단계입니다.');
    return false;
  }
}

// 4. 모든 페이지 버튼 검사
function checkAllButtons() {
  // 모든 버튼 찾기
  const buttons = Array.from(document.querySelectorAll('button'));
  console.log('페이지의 모든 버튼:', buttons);
  
  // 버튼 텍스트 목록 출력
  console.log('버튼 텍스트:');
  buttons.forEach((btn, index) => {
    console.log(`버튼 ${index + 1}: "${btn.textContent.trim()}"`);
  });
  
  return buttons.length;
}

// 5. 모든 단계 진행 (자동화)
function autoProgressAllSteps() {
  // 1단계: 입력 필드 설정 및 분석 버튼 클릭
  checkInputs();
  setTimeout(() => {
    forceClickButton();
    
    // 2단계: 다음 버튼 클릭 (분석 -> 설정)
    setTimeout(() => {
      const nextButtons = Array.from(document.querySelectorAll('button')).filter(
        btn => btn.textContent.trim() === '다음'
      );
      if (nextButtons.length > 0) {
        console.log('다음 버튼을 찾았습니다:', nextButtons[0]);
        nextButtons[0].click();
        
        // 3단계: 환경 설정 적용 버튼 클릭
        setTimeout(() => {
          const setupButtons = Array.from(document.querySelectorAll('button')).filter(
            btn => btn.textContent.includes('환경 설정 적용')
          );
          if (setupButtons.length > 0) {
            console.log('환경 설정 적용 버튼을 찾았습니다:', setupButtons[0]);
            setupButtons[0].click();
            
            // 4단계: 모델 설치 버튼 클릭
            setTimeout(() => {
              const installButtons = Array.from(document.querySelectorAll('button')).filter(
                btn => btn.textContent.includes('모델 설치')
              );
              if (installButtons.length > 0) {
                console.log('모델 설치 버튼을 찾았습니다:', installButtons[0]);
                installButtons[0].click();
                
                console.log('모든 단계를 자동으로 진행했습니다.');
              } else {
                console.error('모델 설치 버튼을 찾을 수 없습니다.');
              }
            }, 3000);
          } else {
            console.error('환경 설정 적용 버튼을 찾을 수 없습니다.');
          }
        }, 3000);
      } else {
        console.error('다음 버튼을 찾을 수 없습니다.');
      }
    }, 3000);
  }, 1000);
  
  console.log('자동 진행을 시작합니다... 콘솔 메시지를 확인하세요.');
}

// 6. 수동 스텝 진행 헬퍼
function goToStep(stepNumber) {
  // 모든 단계 가져오기
  const steps = Array.from(document.querySelectorAll('.MuiStepLabel-root'));
  console.log('스텝퍼의 모든 단계:', steps);
  
  if (stepNumber < 1 || stepNumber > steps.length) {
    console.error(`잘못된 단계 번호입니다. 1에서 ${steps.length} 사이의 값이어야 합니다.`);
    return false;
  }
  
  // 단계 컨텐츠 요소 찾기
  const stepContents = [
    document.querySelector('form'), // 1단계
    document.querySelectorAll('.MuiCard-root')[0], // 2단계
    document.querySelector('.MuiAlert-root'), // 3단계
    document.querySelectorAll('.MuiAlert-root')[1] // 4단계
  ];
  
  // 각 단계 숨기기
  stepContents.forEach((content, index) => {
    if (content && content.parentElement) {
      if (index + 1 === stepNumber) {
        content.parentElement.style.display = 'block';
      } else {
        content.parentElement.style.display = 'none';
      }
    }
  });
  
  // 단계 표시기 업데이트
  steps.forEach((step, index) => {
    const stepIcon = step.querySelector('.MuiStepIcon-root');
    if (stepIcon) {
      if (index + 1 === stepNumber) {
        stepIcon.classList.add('Mui-active');
        stepIcon.classList.remove('Mui-completed');
      } else if (index + 1 < stepNumber) {
        stepIcon.classList.remove('Mui-active');
        stepIcon.classList.add('Mui-completed');
      } else {
        stepIcon.classList.remove('Mui-active');
        stepIcon.classList.remove('Mui-completed');
      }
    }
  });
  
  console.log(`단계 ${stepNumber}으로 이동했습니다.`);
  return true;
}

// 메인 디버그 함수 (콘솔에서 호출)
function debugGitHubSetup() {
  console.log('GitHub AI 설정 페이지 디버깅 도구');
  console.log('===========================');
  console.log('');
  console.log('다음 함수를 호출하여 페이지를 디버깅할 수 있습니다:');
  console.log('1. forceClickButton() - 분석 버튼 강제 클릭');
  console.log('2. checkInputs() - 입력 필드 검사 및 값 설정');
  console.log('3. forceNextStep() - 다음 단계로 강제 이동');
  console.log('4. checkAllButtons() - 모든 버튼 검사');
  console.log('5. autoProgressAllSteps() - 모든 단계 자동 진행');
  console.log('6. goToStep(stepNumber) - 지정된 단계로 직접 이동');
  console.log('');
  console.log('먼저 checkInputs()를 호출하여 입력 필드를 확인하세요.');
  
  return {
    forceClickButton,
    checkInputs,
    forceNextStep,
    checkAllButtons,
    autoProgressAllSteps,
    goToStep
  };
}

// 전역 객체에 함수 노출
window.debugGitHubSetup = debugGitHubSetup;
window.forceClickButton = forceClickButton;
window.checkInputs = checkInputs;
window.forceNextStep = forceNextStep;
window.checkAllButtons = checkAllButtons;
window.autoProgressAllSteps = autoProgressAllSteps;
window.goToStep = goToStep;

console.log('GitHub AI 설정 페이지 디버그 헬퍼가 로드되었습니다.');
console.log('debugGitHubSetup() 함수를 호출하여 사용 가능한 디버깅 도구를 확인하세요.');
