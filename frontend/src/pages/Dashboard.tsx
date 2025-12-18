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
    const [loading, setLoading] = useState(false);

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

    const blobDownload = (blob: Blob, filename: string) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    };

    const handleDownload = async (file: ApiFile) => {
        const pwd = window.prompt('Enter your login password to decrypt and download:');
        if (!pwd) return;
        try {
            setLoading(true);
            const resp = await api.get(`/files/${file.id}/download`, { params: { password: pwd }, responseType: 'blob' });
            blobDownload(resp.data, file.filename);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Download failed.');
        } finally {
            setLoading(false);
        }
    };

    const handlePreview = async (file: ApiFile) => {
        const pwd = window.prompt('Enter your login password to decrypt and preview:');
        if (!pwd) return;
        try {
            setLoading(true);
            const resp = await api.get(`/files/${file.id}/preview`, { params: { password: pwd }, responseType: 'blob' });
            const blob = resp.data as Blob;
            const url = window.URL.createObjectURL(blob);
            window.open(url, '_blank');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Preview failed.');
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (file: ApiFile) => {
        if (!window.confirm(`Delete ${file.filename}? This cannot be undone.`)) return;
        try {
            setLoading(true);
            await api.delete(`/files/${file.id}`);
            setMessage('File deleted successfully');
            fetchFiles();
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Delete failed.');
        } finally {
            setLoading(false);
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
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {files.map(file => (
                                <tr key={file.id}>
                                    <td>{file.filename}</td>
                                    <td>{new Date(file.created_at).toLocaleString()}</td>
                                    <td>
                                        <button onClick={() => handlePreview(file)}>Preview</button>
                                        <button onClick={() => handleDownload(file)}>Download</button>
                                        <button onClick={() => handleDelete(file)} className="danger">Delete</button>
                                    </td>
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
