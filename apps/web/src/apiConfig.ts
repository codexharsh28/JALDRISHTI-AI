const isLocal = typeof window !== 'undefined' && 
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

export const API_BASE = (import.meta.env.VITE_API_URL as string) || 
  (isLocal ? '' : 'https://jaldrishti-api-ixj8.onrender.com');

export const getWebSocketUrl = (path: string = '/ws/v1/live'): string => {
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  if (isLocal) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host || '127.0.0.1:8000';
    return `${protocol}//${host}${cleanPath}`;
  }
  return `wss://jaldrishti-api-ixj8.onrender.com${cleanPath}`;
};
