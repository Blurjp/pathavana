import React, { useState } from 'react';

export const TestOAuth: React.FC = () => {
  const [result, setResult] = useState<string>('');

  const testDirectOAuth = async () => {
    try {
      const url = 'http://localhost:8001/api/v1/auth/oauth-url/google?redirect_uri=http://localhost:3000/auth/callback';
      setResult(`Testing: ${url}\n\n`);
      
      const response = await fetch(url);
      const statusText = `Status: ${response.status} ${response.statusText}\n\n`;
      
      if (response.ok) {
        const data = await response.json();
        setResult(prev => prev + statusText + 'Success:\n' + JSON.stringify(data, null, 2));
      } else {
        const errorText = await response.text();
        setResult(prev => prev + statusText + 'Error:\n' + errorText);
      }
    } catch (error: any) {
      setResult(prev => prev + 'Fetch Error:\n' + error.message);
    }
  };

  const testConfig = async () => {
    try {
      const url = 'http://localhost:8001/api/v1/frontend-config';
      setResult(`Testing: ${url}\n\n`);
      
      const response = await fetch(url);
      const data = await response.json();
      setResult(prev => prev + 'Config:\n' + JSON.stringify(data, null, 2));
    } catch (error: any) {
      setResult(prev => prev + 'Error:\n' + error.message);
    }
  };

  return (
    <div style={{ position: 'fixed', bottom: 20, right: 20, background: 'white', padding: 20, border: '1px solid #ccc', zIndex: 9999 }}>
      <h3>OAuth Test</h3>
      <button onClick={testConfig} style={{ marginRight: 10 }}>Test Config</button>
      <button onClick={testDirectOAuth}>Test OAuth URL</button>
      <pre style={{ marginTop: 10, maxWidth: 400, overflow: 'auto' }}>{result}</pre>
    </div>
  );
};