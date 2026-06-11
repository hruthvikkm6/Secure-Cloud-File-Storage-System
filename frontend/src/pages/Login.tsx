import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        const params = new URLSearchParams();
        params.append('username', email); // Form username parameter mapping
        params.append('password', password);

        try {
            const response = await api.post('/login', params, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            });
            localStorage.setItem('authToken', response.data.access_token);
            navigate('/dashboard', { replace: true });
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Authentication failed. Please check your credentials.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-form">
            <h2>Access Vault</h2>
            <div className="auth-subtitle">Verify identity to unlock the Aegis zero-knowledge portal</div>
            
            {error && <div className="error"><span>⚠️</span> {error}</div>}
            
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label htmlFor="email">Email Address</label>
                    <input
                        id="email"
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="your@email.com"
                        required
                        disabled={loading}
                    />
                </div>
                <div className="form-group">
                    <label htmlFor="password">Security Passcode</label>
                    <div className="input-container">
                        <input
                            id="password"
                            type={showPassword ? "text" : "password"}
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Enter password"
                            required
                            disabled={loading}
                        />
                        <button 
                            type="button" 
                            className="input-toggle-btn"
                            onClick={() => setShowPassword(!showPassword)}
                            disabled={loading}
                        >
                            {showPassword ? "Hide" : "Show"}
                        </button>
                    </div>
                </div>
                <button type="submit" disabled={loading}>
                    {loading ? "Decrypting Session..." : "Authorize Login"}
                </button>
            </form>
            <p>
                Unauthorized identity? <Link to="/register">Create Aegis Account</Link>
            </p>
        </div>
    );
};

export default Login;
