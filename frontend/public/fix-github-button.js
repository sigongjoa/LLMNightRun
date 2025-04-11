// Fix for the GitHub AI setup button
(function() {
  console.log('GitHub AI setup button fix script loaded');
  
  function addButtonClickHandler() {
    // Look for the button on the page
    console.log('Searching for GitHub analyze button...');
    
    // Find the button by its content text
    const buttons = Array.from(document.querySelectorAll('button'));
    const analyzeButton = buttons.find(btn => {
      const btnText = btn.textContent.trim();
      return btnText.includes('저장소 분석');
    });
    
    if (analyzeButton) {
      console.log('Found 저장소 분석 button:', analyzeButton);
      
      // Check if it already has a click handler
      const clickEvents = window.getEventListeners?.(analyzeButton)?.click || [];
      if (clickEvents.length > 0) {
        console.log('Button already has click handlers, skipping');
        return;
      }
      
      // Add our own click handler
      analyzeButton.addEventListener('click', function(event) {
        console.log('GitHub analyze button clicked!');
        
        // Prevent default action if needed
        event.preventDefault();
        event.stopPropagation();
        
        // Get the URL input
        const urlInput = document.querySelector('input[placeholder*="github.com"]');
        if (!urlInput) {
          console.error('Could not find GitHub URL input');
          return;
        }
        
        const repoUrl = urlInput.value.trim();
        if (!repoUrl) {
          alert('GitHub 저장소 URL을 입력해주세요.');
          return;
        }
        
        console.log('Analyzing repository:', repoUrl);
        
        // Show loading state
        analyzeButton.disabled = true;
        const originalContent = analyzeButton.innerHTML;
        analyzeButton.innerHTML = '분석 중... <span style="display:inline-block;width:20px;height:20px;border:2px solid rgba(255,255,255,.3);border-radius:50%;border-top-color:white;animation:spin 1s linear infinite;margin-left:10px;"></span>';
        
        // Add animation style if not already in document
        if (!document.getElementById('loading-animation-style')) {
          const style = document.createElement('style');
          style.id = 'loading-animation-style';
          style.textContent = `
            @keyframes spin {
              to { transform: rotate(360deg); }
            }
          `;
          document.head.appendChild(style);
        }
        
        // Make API request
        fetch('/model-installer/analyze', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ url: repoUrl })
        })
        .then(response => {
          if (!response.ok) {
            throw new Error(`Server responded with status ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log('Analysis result:', data);
          
          // Store in global scope for debugging
          window.repoAnalysisResult = data;
          
          // Progress to the next step
          const steps = document.querySelectorAll('.MuiStepLabel-root');
          if (steps && steps.length >= 2) {
            const activeStepIndicator = document.querySelector('.Mui-active');
            if (activeStepIndicator) {
              activeStepIndicator.classList.remove('Mui-active');
            }
            steps[1].classList.add('Mui-active');
            
            // Update active step in stepper
            const stepper = document.querySelector('.MuiStepper-root');
            if (stepper) {
              stepper.setAttribute('data-active-step', '1');
            }
          }
          
          // Display the analysis result
          showAnalysisResult(data);
          
          // Show success message
          showNotification('저장소 분석이 완료되었습니다.', 'success');
        })
        .catch(error => {
          console.error('Analysis error:', error);
          showNotification(`저장소 분석 중 오류가 발생했습니다: ${error.message}`, 'error');
        })
        .finally(() => {
          // Reset button state
          analyzeButton.disabled = false;
          analyzeButton.innerHTML = originalContent;
        });
      });
      
      console.log('Click handler added to GitHub analyze button');
    } else {
      console.log('GitHub analyze button not found yet, will retry');
      setTimeout(addButtonClickHandler, 500);
    }
  }
  
  function showAnalysisResult(data) {
    // Create a results container
    const resultsContainer = document.createElement('div');
    resultsContainer.className = 'analysis-results';
    resultsContainer.style.marginTop = '20px';
    resultsContainer.style.padding = '15px';
    resultsContainer.style.backgroundColor = '#f5f5f5';
    resultsContainer.style.borderRadius = '4px';
    resultsContainer.style.border = '1px solid #ddd';
    
    // Heading
    const heading = document.createElement('h2');
    heading.textContent = '분석 결과';
    heading.style.marginBottom = '15px';
    resultsContainer.appendChild(heading);
    
    // Model type section
    if (data.model_type) {
      const modelTypeSection = document.createElement('div');
      modelTypeSection.style.marginBottom = '15px';
      
      const modelTypeTitle = document.createElement('h3');
      modelTypeTitle.textContent = '식별된 모델 유형:';
      modelTypeSection.appendChild(modelTypeTitle);
      
      const modelTypeChip = document.createElement('div');
      modelTypeChip.style.display = 'inline-block';
      modelTypeChip.style.backgroundColor = '#1976d2';
      modelTypeChip.style.color = 'white';
      modelTypeChip.style.padding = '5px 10px';
      modelTypeChip.style.borderRadius = '16px';
      modelTypeChip.style.margin = '5px';
      modelTypeChip.textContent = data.model_type.primary;
      modelTypeSection.appendChild(modelTypeChip);
      
      resultsContainer.appendChild(modelTypeSection);
    }
    
    // Launch scripts section
    const scriptsSection = document.createElement('div');
    scriptsSection.style.marginBottom = '15px';
    
    const scriptsTitle = document.createElement('h3');
    scriptsTitle.textContent = '발견된 실행 스크립트:';
    scriptsSection.appendChild(scriptsTitle);
    
    const scriptsList = document.createElement('ul');
    scriptsList.style.paddingLeft = '20px';
    
    if (data.launch_scripts && data.launch_scripts.length > 0) {
      data.launch_scripts.forEach(script => {
        const scriptItem = document.createElement('li');
        scriptItem.textContent = script;
        scriptsList.appendChild(scriptItem);
      });
    } else {
      const noScriptsItem = document.createElement('li');
      noScriptsItem.textContent = '실행 스크립트를 찾을 수 없습니다.';
      scriptsList.appendChild(noScriptsItem);
    }
    
    scriptsSection.appendChild(scriptsList);
    resultsContainer.appendChild(scriptsSection);
    
    // Requirements section
    const reqSection = document.createElement('div');
    
    const reqTitle = document.createElement('h3');
    reqTitle.textContent = '요구사항 파일:';
    reqSection.appendChild(reqTitle);
    
    const reqList = document.createElement('ul');
    reqList.style.paddingLeft = '20px';
    
    if (data.requirements && Object.keys(data.requirements).length > 0) {
      Object.keys(data.requirements).forEach(reqFile => {
        const reqItem = document.createElement('li');
        reqItem.textContent = reqFile;
        reqList.appendChild(reqItem);
      });
    } else {
      const noReqsItem = document.createElement('li');
      noReqsItem.textContent = '요구사항 파일을 찾을 수 없습니다.';
      reqList.appendChild(noReqsItem);
    }
    
    reqSection.appendChild(reqList);
    resultsContainer.appendChild(reqSection);
    
    // Navigation buttons
    const navButtons = document.createElement('div');
    navButtons.style.display = 'flex';
    navButtons.style.justifyContent = 'space-between';
    navButtons.style.marginTop = '20px';
    
    const backButton = document.createElement('button');
    backButton.textContent = '이전';
    backButton.style.padding = '8px 16px';
    backButton.style.cursor = 'pointer';
    backButton.addEventListener('click', () => {
      // Go back to previous step
      const steps = document.querySelectorAll('.MuiStepLabel-root');
      if (steps && steps.length >= 1) {
        const activeStepIndicator = document.querySelector('.Mui-active');
        if (activeStepIndicator) {
          activeStepIndicator.classList.remove('Mui-active');
        }
        steps[0].classList.add('Mui-active');
        
        // Update active step in stepper
        const stepper = document.querySelector('.MuiStepper-root');
        if (stepper) {
          stepper.setAttribute('data-active-step', '0');
        }
        
        // Remove results container
        if (resultsContainer.parentNode) {
          resultsContainer.parentNode.removeChild(resultsContainer);
        }
      }
    });
    navButtons.appendChild(backButton);
    
    const nextButton = document.createElement('button');
    nextButton.textContent = '다음';
    nextButton.style.padding = '8px 16px';
    nextButton.style.backgroundColor = '#1976d2';
    nextButton.style.color = 'white';
    nextButton.style.border = 'none';
    nextButton.style.borderRadius = '4px';
    nextButton.style.cursor = 'pointer';
    nextButton.addEventListener('click', () => {
      // Go to next step
      const steps = document.querySelectorAll('.MuiStepLabel-root');
      if (steps && steps.length >= 3) {
        const activeStepIndicator = document.querySelector('.Mui-active');
        if (activeStepIndicator) {
          activeStepIndicator.classList.remove('Mui-active');
        }
        steps[2].classList.add('Mui-active');
        
        // Update active step in stepper
        const stepper = document.querySelector('.MuiStepper-root');
        if (stepper) {
          stepper.setAttribute('data-active-step', '2');
        }
        
        // Show environment setup UI
        showEnvironmentSetup(data);
      }
    });
    navButtons.appendChild(nextButton);
    
    resultsContainer.appendChild(navButtons);
    
    // Find the paper container to add our results
    const paperContainer = document.querySelector('.MuiPaper-root');
    if (paperContainer) {
      // Clear existing content (except the stepper)
      const existingContent = paperContainer.querySelectorAll(':scope > *:not(.MuiStepper-root)');
      existingContent.forEach(el => el.remove());
      
      // Append our results
      paperContainer.appendChild(resultsContainer);
    } else {
      console.error('Could not find paper container for results');
    }
  }
  
  function showEnvironmentSetup(data) {
    // Create an environment setup container
    const setupContainer = document.createElement('div');
    setupContainer.className = 'environment-setup';
    setupContainer.style.marginTop = '20px';
    setupContainer.style.padding = '15px';
    setupContainer.style.backgroundColor = '#f5f5f5';
    setupContainer.style.borderRadius = '4px';
    setupContainer.style.border = '1px solid #ddd';
    
    // Heading
    const heading = document.createElement('h2');
    heading.textContent = '환경 설정';
    heading.style.marginBottom = '15px';
    setupContainer.appendChild(heading);
    
    // Description
    const description = document.createElement('p');
    description.textContent = '분석된 결과를 바탕으로 AI 환경을 자동으로 설정합니다.';
    setupContainer.appendChild(description);
    
    // Info alert
    const infoAlert = document.createElement('div');
    infoAlert.style.backgroundColor = '#e3f2fd';
    infoAlert.style.color = '#0d47a1';
    infoAlert.style.padding = '10px 15px';
    infoAlert.style.borderRadius = '4px';
    infoAlert.style.marginBottom = '20px';
    infoAlert.textContent = '필요한 패키지와 종속성이 자동으로 설치됩니다. 환경 설정 파일이 생성됩니다.';
    setupContainer.appendChild(infoAlert);
    
    // Navigation buttons
    const navButtons = document.createElement('div');
    navButtons.style.display = 'flex';
    navButtons.style.justifyContent = 'space-between';
    navButtons.style.marginTop = '20px';
    
    const backButton = document.createElement('button');
    backButton.textContent = '이전';
    backButton.style.padding = '8px 16px';
    backButton.style.cursor = 'pointer';
    backButton.addEventListener('click', () => {
      // Go back to previous step
      const steps = document.querySelectorAll('.MuiStepLabel-root');
      if (steps && steps.length >= 2) {
        const activeStepIndicator = document.querySelector('.Mui-active');
        if (activeStepIndicator) {
          activeStepIndicator.classList.remove('Mui-active');
        }
        steps[1].classList.add('Mui-active');
        
        // Update active step in stepper
        const stepper = document.querySelector('.MuiStepper-root');
        if (stepper) {
          stepper.setAttribute('data-active-step', '1');
        }
        
        // Show analysis result again
        showAnalysisResult(data);
      }
    });
    navButtons.appendChild(backButton);
    
    const setupButton = document.createElement('button');
    setupButton.textContent = '환경 설정 적용';
    setupButton.style.padding = '8px 16px';
    setupButton.style.backgroundColor = '#1976d2';
    setupButton.style.color = 'white';
    setupButton.style.border = 'none';
    setupButton.style.borderRadius = '4px';
    setupButton.style.cursor = 'pointer';
    setupButton.addEventListener('click', () => {
      // Apply environment setup
      setupButton.disabled = true;
      const originalText = setupButton.textContent;
      setupButton.innerHTML = '설정 중... <span style="display:inline-block;width:20px;height:20px;border:2px solid rgba(255,255,255,.3);border-radius:50%;border-top-color:white;animation:spin 1s linear infinite;margin-left:10px;"></span>';
      
      // Get the URL input
      const urlInput = document.querySelector('input[placeholder*="github.com"]');
      const repoUrl = urlInput ? urlInput.value.trim() : '';
      
      // Make API request
      fetch('/model-installer/setup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          url: repoUrl,
          analysis: data
        })
      })
      .then(response => {
        if (!response.ok) {
          throw new Error(`Server responded with status ${response.status}`);
        }
        return response.json();
      })
      .then(setupData => {
        console.log('Setup completed:', setupData);
        
        // Progress to the next step
        const steps = document.querySelectorAll('.MuiStepLabel-root');
        if (steps && steps.length >= 4) {
          const activeStepIndicator = document.querySelector('.Mui-active');
          if (activeStepIndicator) {
            activeStepIndicator.classList.remove('Mui-active');
          }
          steps[3].classList.add('Mui-active');
          
          // Update active step in stepper
          const stepper = document.querySelector('.MuiStepper-root');
          if (stepper) {
            stepper.setAttribute('data-active-step', '3');
          }
          
          // Show installation step
          showInstallationStep(data);
        }
        
        // Show success message
        showNotification('환경 설정이 완료되었습니다.', 'success');
      })
      .catch(error => {
        console.error('Setup error:', error);
        showNotification(`환경 설정 중 오류가 발생했습니다: ${error.message}`, 'error');
      })
      .finally(() => {
        // Reset button state
        setupButton.disabled = false;
        setupButton.textContent = originalText;
      });
    });
    navButtons.appendChild(setupButton);
    
    setupContainer.appendChild(navButtons);
    
    // Find the paper container to add our setup UI
    const paperContainer = document.querySelector('.MuiPaper-root');
    if (paperContainer) {
      // Clear existing content (except the stepper)
      const existingContent = paperContainer.querySelectorAll(':scope > *:not(.MuiStepper-root)');
      existingContent.forEach(el => el.remove());
      
      // Append our setup UI
      paperContainer.appendChild(setupContainer);
    } else {
      console.error('Could not find paper container for setup UI');
    }
  }
  
  function showInstallationStep(data) {
    // Create an installation container
    const installContainer = document.createElement('div');
    installContainer.className = 'model-installation';
    installContainer.style.marginTop = '20px';
    installContainer.style.padding = '15px';
    installContainer.style.backgroundColor = '#f5f5f5';
    installContainer.style.borderRadius = '4px';
    installContainer.style.border = '1px solid #ddd';
    
    // Heading
    const heading = document.createElement('h2');
    heading.textContent = '모델 설치';
    heading.style.marginBottom = '15px';
    installContainer.appendChild(heading);
    
    // Description
    const description = document.createElement('p');
    description.textContent = '환경 설정이 완료되었습니다. 모델을 설치합니다.';
    installContainer.appendChild(description);
    
    // Info alert
    const infoAlert = document.createElement('div');
    infoAlert.style.backgroundColor = '#e3f2fd';
    infoAlert.style.color = '#0d47a1';
    infoAlert.style.padding = '10px 15px';
    infoAlert.style.borderRadius = '4px';
    infoAlert.style.marginBottom = '20px';
    infoAlert.textContent = '모델 설치는 시간이 소요될 수 있습니다. 설치가 완료될 때까지 기다려주세요.';
    installContainer.appendChild(infoAlert);
    
    // Log container
    const logContainer = document.createElement('div');
    logContainer.style.display = 'none';
    logContainer.style.backgroundColor = '#000';
    logContainer.style.color = '#fff';
    logContainer.style.fontFamily = 'monospace';
    logContainer.style.padding = '10px';
    logContainer.style.borderRadius = '4px';
    logContainer.style.height = '200px';
    logContainer.style.overflow = 'auto';
    logContainer.style.marginBottom = '20px';
    installContainer.appendChild(logContainer);
    
    // Navigation buttons
    const navButtons = document.createElement('div');
    navButtons.style.display = 'flex';
    navButtons.style.justifyContent = 'space-between';
    navButtons.style.marginTop = '20px';
    
    const backButton = document.createElement('button');
    backButton.textContent = '이전';
    backButton.style.padding = '8px 16px';
    backButton.style.cursor = 'pointer';
    backButton.addEventListener('click', () => {
      // Go back to previous step
      const steps = document.querySelectorAll('.MuiStepLabel-root');
      if (steps && steps.length >= 3) {
        const activeStepIndicator = document.querySelector('.Mui-active');
        if (activeStepIndicator) {
          activeStepIndicator.classList.remove('Mui-active');
        }
        steps[2].classList.add('Mui-active');
        
        // Update active step in stepper
        const stepper = document.querySelector('.MuiStepper-root');
        if (stepper) {
          stepper.setAttribute('data-active-step', '2');
        }
        
        // Show environment setup again
        showEnvironmentSetup(data);
      }
    });
    navButtons.appendChild(backButton);
    
    const installButton = document.createElement('button');
    installButton.textContent = '모델 설치';
    installButton.style.padding = '8px 16px';
    installButton.style.backgroundColor = '#1976d2';
    installButton.style.color = 'white';
    installButton.style.border = 'none';
    installButton.style.borderRadius = '4px';
    installButton.style.cursor = 'pointer';
    installButton.addEventListener('click', () => {
      // Apply installation
      installButton.disabled = true;
      const originalText = installButton.textContent;
      installButton.innerHTML = '설치 중... <span style="display:inline-block;width:20px;height:20px;border:2px solid rgba(255,255,255,.3);border-radius:50%;border-top-color:white;animation:spin 1s linear infinite;margin-left:10px;"></span>';
      
      // Get the URL input
      const urlInput = document.querySelector('input[placeholder*="github.com"]');
      const repoUrl = urlInput ? urlInput.value.trim() : '';
      
      // Show log container
      logContainer.style.display = 'block';
      logContainer.innerHTML = '<div>모델 설치 시작...</div>';
      
      // Make API request
      fetch('/model-installer/install', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: repoUrl })
      })
      .then(response => {
        if (!response.ok) {
          throw new Error(`Server responded with status ${response.status}`);
        }
        return response.json();
      })
      .then(installData => {
        console.log('Installation started:', installData);
        
        // Get installation ID
        const installationId = installData.installation_id;
        
        // Start polling for installation status
        pollInstallationStatus(installationId, logContainer, installButton, originalText);
      })
      .catch(error => {
        console.error('Installation error:', error);
        showNotification(`모델 설치 중 오류가 발생했습니다: ${error.message}`, 'error');
        
        // Reset button state
        installButton.disabled = false;
        installButton.textContent = originalText;
      });
    });
    navButtons.appendChild(installButton);
    
    installContainer.appendChild(navButtons);
    
    // Find the paper container to add our installation UI
    const paperContainer = document.querySelector('.MuiPaper-root');
    if (paperContainer) {
      // Clear existing content (except the stepper)
      const existingContent = paperContainer.querySelectorAll(':scope > *:not(.MuiStepper-root)');
      existingContent.forEach(el => el.remove());
      
      // Append our installation UI
      paperContainer.appendChild(installContainer);
    } else {
      console.error('Could not find paper container for installation UI');
    }
  }
  
  function pollInstallationStatus(installationId, logContainer, button, originalButtonText) {
    // Poll the installation status
    fetch(`/model-installer/status/${installationId}`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`Server responded with status ${response.status}`);
        }
        return response.json();
      })
      .then(statusData => {
        console.log('Installation status:', statusData);
        
        // Update logs
        if (statusData.logs && statusData.logs.length > 0) {
          logContainer.innerHTML = '';
          statusData.logs.forEach(log => {
            const logLine = document.createElement('div');
            logLine.textContent = log;
            logContainer.appendChild(logLine);
          });
          
          // Scroll to bottom
          logContainer.scrollTop = logContainer.scrollHeight;
        }
        
        // Check status
        if (statusData.status === 'completed') {
          // Installation completed
          showNotification('모델 설치가 완료되었습니다.', 'success');
          
          // Reset button state
          button.disabled = false;
          button.textContent = originalButtonText;
          
          // Show completion UI
          showCompletionStep();
        } else if (statusData.status === 'failed') {
          // Installation failed
          showNotification('모델 설치에 실패했습니다.', 'error');
          
          // Reset button state
          button.disabled = false;
          button.textContent = originalButtonText;
        } else {
          // Continue polling
          setTimeout(() => {
            pollInstallationStatus(installationId, logContainer, button, originalButtonText);
          }, 3000);
        }
      })
      .catch(error => {
        console.error('Status check error:', error);
        
        // Continue polling despite error
        setTimeout(() => {
          pollInstallationStatus(installationId, logContainer, button, originalButtonText);
        }, 3000);
      });
  }
  
  function showCompletionStep() {
    // Create a completion container
    const completionContainer = document.createElement('div');
    completionContainer.className = 'installation-complete';
    completionContainer.style.marginTop = '20px';
    completionContainer.style.padding = '15px';
    completionContainer.style.backgroundColor = '#f5f5f5';
    completionContainer.style.borderRadius = '4px';
    completionContainer.style.border = '1px solid #ddd';
    
    // Success alert
    const successAlert = document.createElement('div');
    successAlert.style.backgroundColor = '#e8f5e9';
    successAlert.style.color = '#2e7d32';
    successAlert.style.padding = '10px 15px';
    successAlert.style.borderRadius = '4px';
    successAlert.style.marginBottom = '20px';
    successAlert.textContent = '모델 설치가 완료되었습니다. 이제 모델을 사용할 수 있습니다.';
    completionContainer.appendChild(successAlert);
    
    // Button container
    const buttonContainer = document.createElement('div');
    buttonContainer.style.display = 'flex';
    buttonContainer.style.justifyContent = 'center';
    
    const finishButton = document.createElement('button');
    finishButton.textContent = '모델 관리로 이동';
    finishButton.style.padding = '8px 16px';
    finishButton.style.backgroundColor = '#4caf50';
    finishButton.style.color = 'white';
    finishButton.style.border = 'none';
    finishButton.style.borderRadius = '4px';
    finishButton.style.cursor = 'pointer';
    finishButton.addEventListener('click', () => {
      // Navigate to models page
      window.location.href = '/models';
    });
    buttonContainer.appendChild(finishButton);
    
    completionContainer.appendChild(buttonContainer);
    
    // Find the paper container to add our completion UI
    const paperContainer = document.querySelector('.MuiPaper-root');
    if (paperContainer) {
      // Clear existing content (except the stepper)
      const existingContent = paperContainer.querySelectorAll(':scope > *:not(.MuiStepper-root)');
      existingContent.forEach(el => el.remove());
      
      // Append our completion UI
      paperContainer.appendChild(completionContainer);
    } else {
      console.error('Could not find paper container for completion UI');
    }
  }
  
  function showNotification(message, type = 'info') {
    // Create snackbar for notifications
    let snackbar = document.getElementById('custom-snackbar');
    
    if (!snackbar) {
      snackbar = document.createElement('div');
      snackbar.id = 'custom-snackbar';
      snackbar.style.position = 'fixed';
      snackbar.style.bottom = '20px';
      snackbar.style.left = '50%';
      snackbar.style.transform = 'translateX(-50%)';
      snackbar.style.padding = '12px 24px';
      snackbar.style.borderRadius = '4px';
      snackbar.style.color = 'white';
      snackbar.style.zIndex = '9999';
      snackbar.style.minWidth = '300px';
      snackbar.style.textAlign = 'center';
      snackbar.style.boxShadow = '0 3px 6px rgba(0,0,0,0.16), 0 3px 6px rgba(0,0,0,0.23)';
      document.body.appendChild(snackbar);
    }
    
    // Set style based on type
    switch(type) {
      case 'success':
        snackbar.style.backgroundColor = '#4caf50';
        break;
      case 'error':
        snackbar.style.backgroundColor = '#f44336';
        break;
      case 'warning':
        snackbar.style.backgroundColor = '#ff9800';
        break;
      default:
        snackbar.style.backgroundColor = '#2196f3';
    }
    
    // Set message
    snackbar.textContent = message;
    
    // Show snackbar
    snackbar.style.display = 'block';
    
    // Hide after 3 seconds
    setTimeout(() => {
      snackbar.style.display = 'none';
    }, 3000);
  }
  
  // When the page is loaded, add the click handler
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addButtonClickHandler);
  } else {
    // DOM already loaded
    addButtonClickHandler();
  }
  
  // Also try on window load (more reliable for complex pages)
  window.addEventListener('load', addButtonClickHandler);
  
  // And a fallback timer just in case
  setTimeout(addButtonClickHandler, 1000);
})();
