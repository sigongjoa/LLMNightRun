// Fix for LLMNightRun app
(function() {
  console.log('LLMNightRun Fix Script Loading');
  
  // Load the fix-connection.js script
  const script = document.createElement('script');
  script.src = '/fix-connection.js';
  document.head.appendChild(script);
  
  // Add a visual indicator that fixes are applied
  const fixIndicator = document.createElement('div');
  fixIndicator.style.position = 'fixed';
  fixIndicator.style.bottom = '10px';
  fixIndicator.style.right = '10px';
  fixIndicator.style.backgroundColor = 'rgba(0, 150, 0, 0.7)';
  fixIndicator.style.color = 'white';
  fixIndicator.style.padding = '5px 10px';
  fixIndicator.style.borderRadius = '4px';
  fixIndicator.style.fontSize = '12px';
  fixIndicator.style.zIndex = 9999;
  fixIndicator.textContent = 'Fixed Mode';
  
  // Add to body when DOM is ready
  if (document.body) {
    document.body.appendChild(fixIndicator);
  } else {
    document.addEventListener('DOMContentLoaded', function() {
      document.body.appendChild(fixIndicator);
    });
  }
})();
