document.addEventListener('DOMContentLoaded', function() {
  // 버전 표시
  const versionElement = document.createElement('div');
  versionElement.className = 'info';
  versionElement.textContent = 'Claude Conversation Extractor v1.1';
  document.body.appendChild(versionElement);
  
  // 버튼 이벤트 리스너 설정
  document.getElementById('extractBtn').addEventListener('click', function() {
    extractConversation(false);
  });
  
  document.getElementById('extractCurrentBtn').addEventListener('click', function() {
    extractConversation(true);
  });
  
  document.getElementById('autoSaveBtn').addEventListener('click', function() {
    openAutoSaveSettings();
  });
  
  // 진단 버튼 추가
  const diagnosticBtn = document.createElement('button');
  diagnosticBtn.textContent = '문제 진단 실행';
  diagnosticBtn.id = 'diagnosticBtn';
  diagnosticBtn.style.marginTop = '10px';
  document.getElementById('autoSaveBtn').after(diagnosticBtn);
  
  document.getElementById('diagnosticBtn').addEventListener('click', function() {
    runDiagnostics();
  });
  
  // 재시도 버튼 추가
  const retryBtn = document.createElement('button');
  retryBtn.textContent = '스크립트 재시도';
  retryBtn.id = 'retryBtn';
  retryBtn.style.marginTop = '5px';
  retryBtn.style.backgroundColor = '#5b9bd5';
  document.getElementById('diagnosticBtn').after(retryBtn);
  
  document.getElementById('retryBtn').addEventListener('click', function() {
    retryScriptInjection();
  });
  
  // 초기 진단 실행
  setTimeout(checkScriptStatus, 500);

  // 스크립트 상태 확인 함수
  function checkScriptStatus() {
    const statusText = document.getElementById('statusText');
    statusText.className = 'status';
    statusText.innerHTML = '<p>스크립트 상태 확인 중...</p>';
    
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      if (!tabs || tabs.length === 0) {
        statusText.innerHTML = '<p class="error">활성화된 탭을 찾을 수 없습니다.</p>';
        return;
      }
      
      const currentTab = tabs[0];
      
      // 먼저 스크립트가 살아있는지 확인
      chrome.tabs.sendMessage(currentTab.id, { action: "checkAlive" }, function(response) {
        if (chrome.runtime.lastError || !response) {
          statusText.innerHTML = `
            <p class="error">스크립트가 현재 로드되지 않았거나 응답하지 않습니다.</p>
            <p>"스크립트 재시도" 버튼을 클릭하여 다시 시도하세요.</p>
          `;
        } else {
          statusText.innerHTML = `
            <p class="success">스크립트가 정상적으로 로드되었습니다!</p>
            <p><strong>스크립트 ID:</strong> ${response.scriptId}</p>
            <p><strong>타임스탬프:</strong> ${response.timestamp}</p>
            <p>"대화 추출하기" 버튼을 클릭하여 대화를 추출하세요.</p>
          `;
        }
      });
    });
  }
  
  // 스크립트 재주입 시도 함수
  function retryScriptInjection() {
    const statusText = document.getElementById('statusText');
    statusText.className = 'status';
    statusText.innerHTML = '<p>스크립트 재주입 중...</p>';
    
    // 백그라운드 스크립트에게 재주입 요청
    chrome.runtime.sendMessage({ action: "reinjectContentScript" }, function(response) {
      if (chrome.runtime.lastError) {
        statusText.innerHTML = `
          <p class="error">스크립트 재주입 중 오류 발생: ${chrome.runtime.lastError.message}</p>
        `;
        return;
      }
      
      if (response && response.success) {
        statusText.innerHTML = `
          <p class="success">스크립트가 재주입되었습니다!</p>
          <p>잠시 후 "진단 실행" 버튼을 클릭하여 확인하세요.</p>
        `;
        
        // 2초 후 상태 확인
        setTimeout(checkScriptStatus, 2000);
      } else {
        statusText.innerHTML = `
          <p class="error">스크립트 재주입 실패: ${response ? response.error : '알 수 없는 오류'}</p>
          <p>페이지를 새로고침한 후 다시 시도해 보세요.</p>
        `;
      }
    });
  }
  
  // 진단 실행 함수
  function runDiagnostics() {
    const statusText = document.getElementById('statusText');
    statusText.className = 'status';
    statusText.innerHTML = '<p>진단을 실행 중입니다...</p>';
    
    // 백그라운드 스크립트에서 활성 탭 정보 가져오기
    chrome.runtime.sendMessage({ action: "getActiveTabInfo" }, function(tabInfo) {
      if (chrome.runtime.lastError || !tabInfo || !tabInfo.success) {
        statusText.innerHTML = '<p class="error">활성화된 탭 정보를 가져올 수 없습니다.</p>';
        return;
      }
      
      const url = tabInfo.url || '알 수 없음';
      const tabId = tabInfo.id;
      
      // 기본 진단 정보 표시
      statusText.innerHTML = `
        <h3>기본 진단 정보</h3>
        <p><strong>URL:</strong> ${url}</p>
        <p><strong>탭 ID:</strong> ${tabId}</p>
      `;
      
      // 확장 프로그램 설치 확인
      chrome.management.getSelf(function(info) {
        statusText.innerHTML += `
          <p><strong>확장 프로그램 버전:</strong> ${info.version}</p>
          <p><strong>설치 상태:</strong> ${info.enabled ? '활성화됨' : '비활성화됨'}</p>
        `;
        
        // 스크립트 상태 확인
        chrome.tabs.sendMessage(tabId, { action: "checkAlive" }, function(response) {
          if (chrome.runtime.lastError) {
            statusText.innerHTML += `
              <h3 class="error">콘텐츠 스크립트 오류</h3>
              <p>콘텐츠 스크립트와 통신할 수 없습니다. 오류: ${chrome.runtime.lastError.message}</p>
              <p>이 문제를 해결하려면:</p>
              <ol>
                <li>"스크립트 재시도" 버튼을 클릭하여 스크립트 재주입을 시도하세요.</li>
                <li>페이지를 새로고침하세요.</li>
                <li>확장 프로그램을 비활성화했다가 다시 활성화해 보세요.</li>
                <li>브라우저를 재시작해 보세요.</li>
                <li>개발자 도구(F12)를 열고 콘솔 탭에 오류가 있는지 확인하세요.</li>
              </ol>
            `;
          } else {
            statusText.innerHTML += `
              <h3>콘텐츠 스크립트 상태</h3>
              <p class="success">콘텐츠 스크립트가 정상적으로 로드되었습니다!</p>
              <p><strong>스크립트 ID:</strong> ${response.scriptId}</p>
              <p><strong>타임스탬프:</strong> ${response.timestamp}</p>
              <p>자세한 디버그 정보는 개발자 도구(F12) 콘솔 탭에서 확인할 수 있습니다.</p>
            `;
            
            // 페이지 디버깅 정보 요청
            chrome.tabs.sendMessage(tabId, { action: "debugPageStructure" });
          }
          
          // 페이지가 Claude 도메인인지 확인
          if (url.includes('claude.ai') || url.includes('anthropic.com')) {
            statusText.innerHTML += `
              <p class="success">유효한 Claude 도메인에서 실행 중입니다.</p>
            `;
          } else {
            statusText.innerHTML += `
              <p class="error">이 페이지는 Claude 도메인이 아닙니다. Claude 대화 페이지에서만 이 확장 프로그램을 사용할 수 있습니다.</p>
            `;
          }
          
          // 권한 확인
          try {
            chrome.permissions.contains({ origins: [new URL(url).origin + "/*"] }, function(result) {
              if (result) {
                statusText.innerHTML += `<p class="success">현재 페이지에 대한 접근 권한이 있습니다.</p>`;
              } else {
                statusText.innerHTML += `<p class="error">현재 페이지에 대한 접근 권한이 없습니다.</p>`;
              }
              
              // 완료 메시지
              statusText.innerHTML += `
                <h3>진단 완료</h3>
                <p>문제가 계속되면 "스크립트 재시도" 버튼을 클릭하거나, 확장 프로그램을 재설치하거나 브라우저를 업데이트해 보세요.</p>
              `;
            });
          } catch (e) {
            statusText.innerHTML += `
              <p class="error">권한 확인 중 오류: ${e.message}</p>
              <h3>진단 완료</h3>
              <p>문제가 계속되면 "스크립트 재시도" 버튼을 클릭하거나, 확장 프로그램을 재설치하거나 브라우저를 업데이트해 보세요.</p>
            `;
          }
        });
      });
    });
  }
  
  // 페이지 디버깅 정보 가져오기
  function getDebugInfo() {
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      if (!tabs || tabs.length === 0) {
        const statusText = document.getElementById('statusText');
        statusText.classList.add('error');
        statusText.innerHTML = `<p>활성화된 탭을 찾을 수 없습니다.</p>`;
        return;
      }
      
      chrome.tabs.sendMessage(tabs[0].id, { action: "debugPageStructure" }, function(response) {
        if (chrome.runtime.lastError) {
          const statusText = document.getElementById('statusText');
          statusText.classList.add('error');
          statusText.innerHTML = `<p>디버그 정보를 가져올 수 없습니다. 오류: ${chrome.runtime.lastError.message}</p>
                                 <p>현재 URL: ${tabs[0].url}</p>
                                 <p>F12를 눌러 개발자 도구를 열고 콘솔 탭을 확인하세요.</p>`;
          return;
        }
        
        // 특별한 처리는 필요 없음 - 디버그 정보는 콘솔에 출력됨
        const statusText = document.getElementById('statusText');
        statusText.innerHTML = '<p>디버그 정보가 개발자 도구 콘솔에 출력되었습니다. F12 키를 눌러 확인하세요.</p>';
      });
    });
  }
  
  // 대화 추출 함수
  function extractConversation(currentOnly) {
    const statusText = document.getElementById('statusText');
    statusText.className = 'status';
    statusText.innerHTML = '<p>대화 추출 중...</p>';
    
    // 먼저 스크립트가 로드되었는지 확인
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      if (!tabs || tabs.length === 0) {
        statusText.innerHTML = '<p class="error">활성화된 탭을 찾을 수 없습니다.</p>';
        return;
      }
      
      // 스크립트 상태 확인
      chrome.tabs.sendMessage(tabs[0].id, { action: "checkAlive" }, function(aliveResponse) {
        if (chrome.runtime.lastError || !aliveResponse) {
          statusText.innerHTML = `
            <p class="error">콘텐츠 스크립트가 로드되지 않았거나 응답하지 않습니다.</p>
            <p>"스크립트 재시도" 버튼을 클릭하여 스크립트를 다시 로드한 후 시도하세요.</p>
          `;
          
          // 자동으로 재주입 시도
          retryScriptInjection();
          return;
        }
        
        // 스크립트가 로드되었으므로 대화 추출 시도
        const format = document.getElementById('formatSelect').value;
        
        chrome.tabs.sendMessage(tabs[0].id, {
          action: "extractConversation", 
          currentOnly: currentOnly,
          format: format
        }, function(response) {
          if (chrome.runtime.lastError) {
            statusText.classList.add('error');
            statusText.innerHTML = `<p>오류: 대화 추출 중 문제가 발생했습니다.</p>
                                  <p>오류 메시지: ${chrome.runtime.lastError.message}</p>
                                  <p>"스크립트 재시도" 버튼을 클릭한 후 다시 시도하세요.</p>`;
            return;
          }
          
          if (response && response.success) {
            statusText.className = 'status';
            statusText.innerHTML = `
              <p class="success">추출 완료! 파일이 다운로드됩니다.</p>
              <p><strong>메시지 수:</strong> ${response.conversations ? response.conversations.length : '알 수 없음'}</p>
              <p><strong>형식:</strong> ${format}</p>
            `;
          } else {
            statusText.classList.add('error');
            statusText.innerHTML = `
              <p class="error">추출 실패: ${response ? response.error : '알 수 없는 오류'}</p>
              <p>다음을 시도해 보세요:</p>
              <ol>
                <li>페이지가 완전히 로드될 때까지 기다리세요.</li>
                <li>"진단 실행" 버튼을 클릭하여 문제를 진단하세요.</li>
                <li>페이지를 새로고침한 후 다시 시도하세요.</li>
                <li>"스크립트 재시도" 버튼을 클릭한 후 다시 시도하세요.</li>
              </ol>
              <p>개발자 도구(F12)를 열고 콘솔 탭에서 자세한 오류 정보를 확인하세요.</p>
            `;
            
            // 디버그 정보 자동 수집
            chrome.tabs.sendMessage(tabs[0].id, { action: "debugPageStructure" });
          }
        });
      });
    });
  }
  
  // 자동 저장 설정 화면 열기
  function openAutoSaveSettings() {
    // 저장된 설정 불러오기
    chrome.storage.sync.get(['autoSaveEnabled', 'autoSaveInterval'], function(data) {
      const enabled = data.autoSaveEnabled || false;
      const interval = data.autoSaveInterval || 5;
      
      const settingsUI = `
        <div style="margin-top: 15px;">
          <label>
            <input type="checkbox" id="autoSaveCheckbox" ${enabled ? 'checked' : ''}>
            자동 저장 활성화
          </label>
          <div style="margin-top: 10px;">
            <label>저장 간격 (분):</label>
            <input type="number" id="intervalInput" value="${interval}" min="1" max="60" style="width: 60px; margin-left: 5px;">
          </div>
          <button id="saveSettingsBtn" style="margin-top: 10px;">설정 저장</button>
        </div>
      `;
      
      document.getElementById('statusText').innerHTML = settingsUI;
      
      document.getElementById('saveSettingsBtn').addEventListener('click', function() {
        const newEnabled = document.getElementById('autoSaveCheckbox').checked;
        const newInterval = parseInt(document.getElementById('intervalInput').value) || 5;
        
        // 설정 저장
        chrome.storage.sync.set({
          autoSaveEnabled: newEnabled,
          autoSaveInterval: newInterval
        }, function() {
          // 저장 후 콘텐츠 스크립트에 설정 변경 알림
          chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            chrome.tabs.sendMessage(tabs[0].id, {
              action: "updateAutoSaveSettings", 
              enabled: newEnabled,
              interval: newInterval
            });
            
            document.getElementById('statusText').textContent = '설정이 저장되었습니다!';
          });
        });
      });
    });
  }
});
