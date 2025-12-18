import React, { useState, useEffect } from 'react';
import api from '../services/api';

// Renamed to avoid collision with the browser's built-in File type
interface ApiFile {
    id: number;
    filename: string;
    created_at: string;
}

const Dashboard = () => {
    const [files, setFiles] = useState<ApiFile[]>([]);
    // This state holds the file selected from the input, which is the browser's File object
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [message, setMessage] = useState('');

    const fetchFiles = async () => {
        try {
            const response = await api.get('/files');
            setFiles(response.data);
        } catch (err) {
            setError('Failed to fetch files. Your session might have expired. Please log in again.');
        }
    };

    useEffect(() => {
        fetchFiles();
    }, []);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            setSelectedFile(e.target.files[0]);
        }
    };

    const handleUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedFile || !password) {
            setError('Please select a file and enter your password.');
            return;
        }

        const formData = new FormData();
        // selectedFile is now the correct type for formData
        formData.append('file', selectedFile);
        formData.append('password', password);

        setError('');
        setMessage('');

        try {
            await api.post('/files/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            setMessage('File uploaded successfully!');
            setSelectedFile(null);
            setPassword('');
            const fileInput = document.getElementById('file-input') as HTMLInputElement;
            if(fileInput) fileInput.value = '';
            
            fetchFiles(); // Refresh file list
        } catch (err: any) {
            setError(err.response?.data?.detail || 'File upload failed.');
        }
    };

    return (
        <div>
            <h2>Dashboard</h2>
            
            <div className="upload-section card">
                <h3>Upload New File</h3>
                {error && <p className="error">{error}</p>}
                {message && <p className="message">{message}</p>}
                <form onSubmit={handleUpload}>
                    <div className="form-group">
                        <label htmlFor="file-input">Select File</label>
                        <input id="file-input" type="file" onChange={handleFileChange} required />
                    </div>
                    <div className="form-group">
                        <label htmlFor="password-input">Your Password (for encryption)</label>
                        <input
                            id="password-input"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Enter login password to encrypt file"
                            required
                        />
                    </div>
                    <button type="submit">Upload File</button>
                </form>
            </div>

            <div className="file-list-section card">
                <h3>Your Files</h3>
                {files.length === 0 ? (
                    <p>You have no files uploaded.</p>
                ) : (
                    <table>
                        <thead>
                            <tr>
                                <th>Filename</th>
                                <th>Upload Date</th>
                            </tr>
                        </thead>
                        <tbody>
                            {files.map(file => (
                                <tr key={file.id}>
                                    <td>{file.filename}</td>
                                    <td>{new Date(file.created_at).toLocaleString()}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
};

export default Dashboard;
