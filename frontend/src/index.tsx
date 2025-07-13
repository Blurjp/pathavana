import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { handleGlobalError, handleUnhandledRejection } from './utils/errorHandler';
import './styles/index.css';

// Set up global error handlers
window.addEventListener('error', handleGlobalError);
window.addEventListener('unhandledrejection', handleUnhandledRejection);

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Performance monitoring
if (process.env.NODE_ENV === 'development') {
  import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
    getCLS(console.log);
    getFID(console.log);
    getFCP(console.log);
    getLCP(console.log);
    getTTFB(console.log);
  });
}