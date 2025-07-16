import React, { useState, useEffect } from 'react';
import { useUnifiedSession } from '../hooks/useUnifiedSession';
import { sessionDebugger } from '../utils/sessionDebugger';
import './DebugSession.css';

const DebugSession: React.FC = () => {
  const [forceNew, setForceNew] = useState(false);
  const [testMessage, setTestMessage] = useState('Test message');
  const [logs, setLogs] = useState<string[]>([]);

  const {
    sessionId,
    messages,
    sendMessage,
    createNewSession,
    isMessageLoading,
    messageError
  } = useUnifiedSession(undefined, forceNew);

  // Log all important changes
  useEffect(() => {
    const log = `SessionId changed: ${sessionId || 'empty'}`;
    console.log(`🔵 ${log}`);
    setLogs(prev => [...prev, `[${new Date().toISOString()}] ${log}`]);
  }, [sessionId]);

  const handleSendMessage = async () => {
    const log = `Sending message with sessionId: ${sessionId || 'empty'}`;
    console.log(`🟡 ${log}`);
    setLogs(prev => [...prev, `[${new Date().toISOString()}] ${log}`]);
    
    try {
      await sendMessage(testMessage);
      const successLog = 'Message sent successfully';
      console.log(`✅ ${successLog}`);
      setLogs(prev => [...prev, `[${new Date().toISOString()}] ${successLog}`]);
    } catch (error) {
      const errorLog = `Error: ${error}`;
      console.error(`❌ ${errorLog}`);
      setLogs(prev => [...prev, `[${new Date().toISOString()}] ${errorLog}`]);
    }
  };

  const handleCreateNewSession = async () => {
    const log = 'Creating new session manually';
    console.log(`🟢 ${log}`);
    setLogs(prev => [...prev, `[${new Date().toISOString()}] ${log}`]);
    
    await createNewSession();
  };

  const clearDebugData = () => {
    sessionDebugger.clear();
    setLogs([]);
    localStorage.removeItem('currentSessionId');
    window.location.reload();
  };

  return (
    <div className="debug-session-page">
      <h1>Session Debugging Tool</h1>
      
      <div className="debug-controls">
        <div className="control-group">
          <h3>Current State</h3>
          <div className="state-info">
            <div>
              <strong>Session ID:</strong> 
              <code>{sessionId || 'empty'}</code>
            </div>
            <div>
              <strong>LocalStorage SessionId:</strong> 
              <code>{localStorage.getItem('currentSessionId') || 'empty'}</code>
            </div>
            <div>
              <strong>Messages Count:</strong> {messages.length}
            </div>
            <div>
              <strong>Loading:</strong> {isMessageLoading ? 'Yes' : 'No'}
            </div>
            {messageError && (
              <div className="error">
                <strong>Error:</strong> {messageError}
              </div>
            )}
          </div>
        </div>

        <div className="control-group">
          <h3>Configuration</h3>
          <label>
            <input
              type="checkbox"
              checked={forceNew}
              onChange={(e) => setForceNew(e.target.checked)}
            />
            Force New Session
          </label>
        </div>

        <div className="control-group">
          <h3>Actions</h3>
          <input
            type="text"
            value={testMessage}
            onChange={(e) => setTestMessage(e.target.value)}
            placeholder="Enter test message"
          />
          <div className="button-group">
            <button onClick={handleSendMessage} disabled={isMessageLoading}>
              Send Message
            </button>
            <button onClick={handleCreateNewSession}>
              Create New Session
            </button>
            <button onClick={() => sessionDebugger.printSummary()}>
              Print Debug Summary
            </button>
            <button onClick={() => sessionDebugger.exportToFile()}>
              Export Debug Log
            </button>
            <button onClick={clearDebugData} className="danger">
              Clear All & Reload
            </button>
          </div>
        </div>

        <div className="control-group">
          <h3>Activity Log</h3>
          <div className="log-viewer">
            {logs.map((log, index) => (
              <div key={index} className="log-entry">
                {log}
              </div>
            ))}
          </div>
        </div>

        <div className="control-group">
          <h3>Messages</h3>
          <div className="messages-viewer">
            {messages.map((msg, index) => (
              <div key={msg.id} className={`message ${msg.type}`}>
                <strong>[{index}] {msg.type}:</strong> {msg.content}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="debug-instructions">
        <h3>How to Debug Session Issues:</h3>
        <ol>
          <li>Open Chrome DevTools (F12)</li>
          <li>Go to Sources tab and set breakpoints in:
            <ul>
              <li><code>unifiedTravelApi.ts</code> - sendChatMessage method</li>
              <li><code>useChatManager.ts</code> - sendMessage function</li>
              <li><code>useUnifiedSession.ts</code> - sessionId state updates</li>
            </ul>
          </li>
          <li>Click "Send Message" and watch:
            <ul>
              <li>What's the value of sessionId when sendChatMessage is called?</li>
              <li>Is it creating a new session (POST /sessions) or using existing (POST /sessions/id/chat)?</li>
            </ul>
          </li>
          <li>Check Network tab for API calls</li>
          <li>Use "Print Debug Summary" to see all session events</li>
        </ol>
      </div>
    </div>
  );
};

export default DebugSession;