import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Navbar from './components/Navbar';
import { useEffect, useState } from 'react';

const App = () => {
    // We use a state that updates on location change to re-render correctly
    const [token, setToken] = useState(localStorage.getItem('authToken'));
    const location = useLocation();

    useEffect(() => {
        setToken(localStorage.getItem('authToken'));
    }, [location]);

    return (
        <>
            <Navbar />
            <main className="container">
                <Routes>
                    <Route path="/login" element={!token ? <Login /> : <Navigate to="/dashboard" />} />
                    <Route path="/register" element={!token ? <Register /> : <Navigate to="/dashboard" />} />
                    <Route 
                        path="/dashboard" 
                        element={token ? <Dashboard /> : <Navigate to="/login" />} 
                    />
                    <Route 
                        path="/" 
                        element={token ? <Navigate to="/dashboard" /> : <Navigate to="/login" />} 
                    />
                </Routes>
            </main>
        </>
    );
};

export default App;
