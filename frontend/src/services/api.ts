import axios from 'axios';

// Create an Axios instance with a base URL that points to our API backend.
// Vite's proxy will handle forwarding these requests to http://127.0.0.1:8000
const api = axios.create({
    baseURL: '/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add a request interceptor to automatically attach the JWT access token to requests.
api.interceptors.request.use(
    config => {
        // Retrieve the token from local storage
        const token = localStorage.getItem('authToken');
        
        // If the token exists, add it to the Authorization header
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        
        return config;
    },
    error => {
        // Handle request errors
        return Promise.reject(error);
    }
);

export default api;
