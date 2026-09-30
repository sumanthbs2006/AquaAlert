import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// Automatically route relative /api calls to Render backend if VITE_API_URL is configured on Vercel
const API_BASE = import.meta.env.VITE_API_URL;
if (API_BASE && typeof window !== 'undefined') {
  const originalFetch = window.fetch.bind(window);
  window.fetch = (url, options) => {
    if (typeof url === 'string' && url.startsWith('/api')) {
      return originalFetch(`${API_BASE.replace(/\/$/, '')}${url}`, options);
    }
    return originalFetch(url, options);
  };
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

