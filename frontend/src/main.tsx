import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import './index.css';
import { SessionProvider } from './context/SessionContext';
import { ThemeProvider } from './context/ThemeContext';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <ThemeProvider>
        <SessionProvider>
          <App />
        </SessionProvider>
      </ThemeProvider>
    </BrowserRouter>
  </React.StrictMode>
);
