import { Link, useNavigate } from 'react-router-dom';

const Navbar = () => {
    const navigate = useNavigate();
    const token = localStorage.getItem('authToken');

    const handleLogout = () => {
        localStorage.removeItem('authToken');
        // We use navigate and then force a reload to ensure the state is cleared everywhere
        navigate('/login');
    };

    return (
        <nav className="navbar">
            <Link to="/" className="nav-brand">Mini Drive</Link>
            <ul className="nav-links">
                {token ? (
                    <li>
                        <button onClick={handleLogout} className="nav-logout">Logout</button>
                    </li>
                ) : (
                    <>
                        <li><Link to="/login">Login</Link></li>
                        <li><Link to="/register">Register</Link></li>
                    </>
                )}
            </ul>
        </nav>
    );
};

export default Navbar;
