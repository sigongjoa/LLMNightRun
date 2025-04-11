import React, { useEffect } from 'react';
import GitHubAISetupPage from './github-ai-setup';

// This is a debug wrapper around the GitHub AI setup page
const GitHubAISetupDebugPage = () => {
  useEffect(() => {
    // Load our fix script
    const script = document.createElement('script');
    script.src = '/fix-github-button.js';
    script.async = true;
    document.head.appendChild(script);
    
    // Clean up on unmount
    return () => {
      document.head.removeChild(script);
    };
  }, []);
  
  // Render the original page with an added debug element
  return (
    <>
      <div style={{ 
        position: 'fixed', 
        top: '10px', 
        right: '10px', 
        backgroundColor: '#f50057', 
        color: 'white',
        padding: '5px 10px',
        borderRadius: '4px',
        zIndex: 9999,
        fontSize: '12px',
        fontWeight: 'bold'
      }}>
        DEBUG MODE
      </div>
      <GitHubAISetupPage />
    </>
  );
};

export default GitHubAISetupDebugPage;
