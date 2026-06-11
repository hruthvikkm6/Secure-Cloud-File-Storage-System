import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';

const Register = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (password.length < 8) {
            setError('For cryptographic strength, your passcode must be at least 8 characters long.');
            return;
        }

        setLoading(true);
        try {
            await api.post('/register', { email, password });
            navigate('/login');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Account registration failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-form">
            <h2>Initialize Vault</h2>
            <div className="auth-subtitle">Create a zero-knowledge cloud container to secure your assets</div>
            
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
                    <label htmlFor="password">Zero-Knowledge Passcode</label>
                    <div className="input-container">
                        <input
                            id="password"
                            type={showPassword ? "text" : "password"}
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Min 8 chars (used for AES key)"
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
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                        💡 This password hashes your session (Argon2) and derives your file keys (PBKDF2). Keep it safe!
                    </div>
                </div>
                <button type="submit" disabled={loading}>
                    {loading ? "Generating Safe Keys..." : "Initialize Aegis Account"}
                </button>
            </form>
            <p>
                Already have a vault? <Link to="/login">Open Vault</Link>
            </p>
        </div>
    );
};

export default Register;
