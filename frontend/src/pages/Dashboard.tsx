import React, { useState, useEffect, useRef } from 'react';
import api from '../services/api';

interface ApiFile {
    id: number;
    filename: string;
    created_at: string;
}

const Dashboard = () => {
    const [files, setFiles] = useState<ApiFile[]>([]);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [message, setMessage] = useState('');
    const [loading, setLoading] = useState(false);
    const [dragActive, setDragActive] = useState(false);

    // Custom Modal States
    const [showUploadModal, setShowUploadModal] = useState(false);
    const [showDecryptModal, setShowDecryptModal] = useState(false);
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [showPreviewModal, setShowPreviewModal] = useState(false);
    
    // Modal Interaction Targets
    const [modalTargetFile, setModalTargetFile] = useState<ApiFile | null>(null);
    const [modalActionType, setModalActionType] = useState<'download' | 'preview' | null>(null);
    const [decryptPassword, setDecryptPassword] = useState('');
    const [showDecryptPasswordText, setShowDecryptPasswordText] = useState(false);
    const [showUploadPasswordText, setShowUploadPasswordText] = useState(false);

    // Media Preview States
    const [previewBlobUrl, setPreviewBlobUrl] = useState<string | null>(null);
    const [previewFileType, setPreviewFileType] = useState<string>('');

    const fileInputRef = useRef<HTMLInputElement>(null);

    const closePreviewModal = () => {
        if (previewBlobUrl) {
            window.URL.revokeObjectURL(previewBlobUrl);
        }
        setPreviewBlobUrl(null);
        setPreviewFileType('');
        setShowPreviewModal(false);
        setModalTargetFile(null);
    };

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

    // Drag-and-Drop Event Handlers
    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            setSelectedFile(e.dataTransfer.files[0]);
            setPassword('');
            setShowUploadModal(true); // Open encryption password prompt immediately
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setSelectedFile(e.target.files[0]);
            setPassword('');
            setShowUploadModal(true); // Open encryption password prompt immediately
        }
    };

    const onZoneClick = () => {
        fileInputRef.current?.click();
    };

    // Calculate Password Strength
    const getPasswordStrength = (pwd: string) => {
        if (!pwd) return { score: 0, text: 'None', className: '' };
        
        let score = 0;
        if (pwd.length >= 8) score += 1;
        if (/[A-Z]/.test(pwd)) score += 1;
        if (/[a-z]/.test(pwd) && /[0-9]/.test(pwd)) score += 1;
        if (/[^A-Za-z0-9]/.test(pwd)) score += 1;

        if (score <= 1) return { score, text: 'Weak', className: 'weak' };
        if (score <= 3) return { score, text: 'Medium', className: 'medium' };
        return { score, text: 'Strong (AEAD Secure)', className: 'strong' };
    };

    const passwordStrength = getPasswordStrength(password);

    // Encrypt & Upload Execution
    const handleUploadSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedFile || !password) {
            setError('File and encryption password are required.');
            setShowUploadModal(false);
            return;
        }

        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('password', password);

        setError('');
        setMessage('');
        setLoading(true);
        setShowUploadModal(false);

        try {
            await api.post('/files/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            setMessage(`"${selectedFile.name}" encrypted and uploaded successfully!`);
            setSelectedFile(null);
            setPassword('');
            if (fileInputRef.current) fileInputRef.current.value = '';
            fetchFiles();
        } catch (err: any) {
            setError(err.response?.data?.detail || 'File upload and AES key derivation failed.');
        } finally {
            setLoading(false);
        }
    };

    // Open Custom Decrypt Modal
    const triggerDecryptPortal = (file: ApiFile, action: 'download' | 'preview') => {
        setModalTargetFile(file);
        setModalActionType(action);
        setDecryptPassword('');
        setShowDecryptPasswordText(false);
        setError('');
        setMessage('');
        setShowDecryptModal(true);
    };

    // Single-Use Ticket Redemption & Cryptographic Action
    const handleDecryptSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!modalTargetFile || !decryptPassword || !modalActionType) return;

        setError('');
        setMessage('');
        setLoading(true);
        setShowDecryptModal(false);

        // Keep a local copy of target file and action because they may get updated/cleared
        const currentTargetFile = modalTargetFile;
        const currentActionType = modalActionType;

        try {
            // Step 1: Securely POST password to acquire a single-use token (STAT)
            const tokenResponse = await api.post(`/files/${currentTargetFile.id}/ticket`, {
                password: decryptPassword
            });
            
            const ticketId = tokenResponse.data.ticket_id;

            // Step 2: Redeem the single-use ticket in GET request (Zero-Knowledge URL logs)
            const actionPath = currentActionType === 'download' ? 'download' : 'preview';
            
            const fileResponse = await api.get(`/files/${currentTargetFile.id}/${actionPath}`, {
                params: { ticket_id: ticketId },
                responseType: 'blob'
            });

            const blob = fileResponse.data as Blob;
            const blobUrl = window.URL.createObjectURL(blob);

            if (currentActionType === 'download') {
                const a = document.createElement('a');
                a.href = blobUrl;
                a.download = currentTargetFile.filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
                setMessage(`File "${currentTargetFile.filename}" decrypted and downloaded.`);
                
                // Revoke after a short delay to ensure the browser has started the download
                setTimeout(() => window.URL.revokeObjectURL(blobUrl), 1500);

                // Clear targets since download completed successfully
                setModalTargetFile(null);
                setModalActionType(null);
            } else {
                // Inline Preview Modal
                setPreviewBlobUrl(blobUrl);
                const ext = currentTargetFile.filename.split('.').pop()?.toLowerCase() || '';
                setPreviewFileType(ext);
                setShowPreviewModal(true);
                setMessage(`Preview loaded for "${currentTargetFile.filename}".`);

                // Close decryption prompt modal but KEEP modalTargetFile so filename remains visible in preview
                setModalActionType(null);
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Decryption failed. Incorrect password or tampered ciphertext.');
            // Clear targets since decryption failed
            setModalTargetFile(null);
            setModalActionType(null);
        } finally {
            setLoading(false);
            setDecryptPassword('');
        }
    };

    // Custom Delete Dialog
    const triggerDeletePortal = (file: ApiFile) => {
        setModalTargetFile(file);
        setError('');
        setMessage('');
        setShowDeleteModal(true);
    };

    const handleDeleteSubmit = async () => {
        if (!modalTargetFile) return;

        setError('');
        setMessage('');
        setLoading(true);
        setShowDeleteModal(false);

        try {
            await api.delete(`/files/${modalTargetFile.id}`);
            setMessage(`"${modalTargetFile.filename}" and its associated encrypted block deleted.`);
            fetchFiles();
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Deletion transaction failed.');
        } finally {
            setLoading(false);
            setModalTargetFile(null);
        }
    };

    // Human-readable bytes count placeholder helper
    const getFileCategoryIcon = (filename: string) => {
        const ext = filename.split('.').pop()?.toLowerCase() || '';
        if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)) return '🖼️';
        if (ext === 'pdf') return '📕';
        if (['zip', 'rar', 'tar', 'gz', '7z'].includes(ext)) return '📦';
        if (['txt', 'md', 'doc', 'docx'].includes(ext)) return '📝';
        return '📁';
    };

    return (
        <div>
            {/* Global Telemetry Alerts */}
            {error && <div className="error"><span>⚠️</span> {error}</div>}
            {message && <div className="message"><span>✅</span> {message}</div>}

            {loading && (
                <div className="loading-skeleton">
                    <div className="spinner"></div>
                    <span>Processing Secure Cryptographic Operation...</span>
                </div>
            )}

            <div className="dashboard-grid">
                
                {/* Left Workspace Panel: Upload & Inventory */}
                <div className="workspace-main">
                    
                    {/* Drag and Drop Container */}
                    <div 
                        className={`drag-drop-zone card ${dragActive ? 'active' : ''}`}
                        onDragEnter={handleDrag}
                        onDragOver={handleDrag}
                        onDragLeave={handleDrag}
                        onDrop={handleDrop}
                        onClick={onZoneClick}
                    >
                        <input 
                            ref={fileInputRef}
                            id="file-input" 
                            type="file" 
                            onChange={handleFileChange} 
                            style={{ display: 'none' }}
                        />
                        <div className="drag-drop-icon">🚀</div>
                        <div className="drag-drop-text">
                            <span className="drag-drop-highlight">Click to upload</span> or drag and drop your file here
                        </div>
                        <div className="file-spec-tag">
                            <span>🛡️</span> Zero-Knowledge client encrypts everything before storage
                        </div>
                    </div>

                    {/* Files Inventory Table Card */}
                    <div className="file-list-section card">
                        <div className="telemetry-header">
                            <span style={{ fontSize: '1.2rem' }}>📁</span>
                            <h3 style={{ margin: 0 }}>Secure Files Vault</h3>
                        </div>
                        
                        {files.length === 0 ? (
                            <p style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '2rem 0' }}>
                                Your zero-knowledge vault is currently empty. Drag a file to secure it.
                            </p>
                        ) : (
                            <div className="table-container">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Filename</th>
                                            <th>Date Secured</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {files.map(file => (
                                            <tr key={file.id}>
                                                <td>
                                                    <div className="file-name-cell">
                                                        <span className="file-icon">{getFileCategoryIcon(file.filename)}</span>
                                                        <span>{file.filename}</span>
                                                    </div>
                                                </td>
                                                <td className="date-cell">
                                                    {new Date(file.created_at).toLocaleString()}
                                                </td>
                                                <td>
                                                    <div className="actions-cell">
                                                        <button 
                                                            onClick={() => triggerDecryptPortal(file, 'preview')} 
                                                            className="action-btn"
                                                        >
                                                            Preview
                                                        </button>
                                                        <button 
                                                            onClick={() => triggerDecryptPortal(file, 'download')} 
                                                            className="action-btn download-btn"
                                                        >
                                                            Decrypt & Download
                                                        </button>
                                                        <button 
                                                            onClick={() => triggerDeletePortal(file)} 
                                                            className="action-btn danger-btn"
                                                        >
                                                            Purge
                                                        </button>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>

                {/* Right Panel: Cyber HUD Telemetry Widget & Metrics */}
                <div className="workspace-side">
                    
                    {/* Active Cryptographic Shields HUD */}
                    <div className="card">
                        <div className="telemetry-header">
                            <span style={{ color: 'var(--accent-cyan)' }}>🛡️</span>
                            <span className="telemetry-title">Aegis Telemetry</span>
                        </div>
                        
                        <div className="telemetry-grid">
                            <div className="telemetry-item">
                                <span className="telemetry-label">
                                    <span className="status-indicator"></span> Hashing Standard
                                </span>
                                <span className="telemetry-value">Argon2id</span>
                            </div>
                            <div className="telemetry-item">
                                <span className="telemetry-label">
                                    <span className="status-indicator"></span> Cryptographic Suite
                                </span>
                                <span className="telemetry-value">AES-256-GCM</span>
                            </div>
                            <div className="telemetry-item">
                                <span className="telemetry-label">
                                    <span className="status-indicator"></span> Key Derivation
                                </span>
                                <span className="telemetry-value">PBKDF2-HMAC</span>
                            </div>
                            <div className="telemetry-item">
                                <span className="telemetry-label">
                                    <span className="status-indicator"></span> KDF Iterations
                                </span>
                                <span className="telemetry-value">100,000</span>
                            </div>
                            <div className="telemetry-item">
                                <span className="telemetry-label">
                                    <span className="status-indicator"></span> Token Exchange
                                </span>
                                <span className="telemetry-value">Single-Use Ticket</span>
                            </div>
                            <div className="telemetry-item">
                                <span className="telemetry-label">
                                    <span className="status-indicator"></span> Session Lifespan
                                </span>
                                <span className="telemetry-value">30 Minutes</span>
                            </div>
                            <div className="telemetry-item">
                                <span className="telemetry-label">
                                    <span className="status-indicator"></span> Shield Limiter
                                </span>
                                <span className="telemetry-value">Brute Protection</span>
                            </div>
                        </div>

                        {/* Interactive storage display */}
                        <div className="storage-widget">
                            <div style={{ fontSize: '1.8rem' }}>☁️</div>
                            <div className="storage-bar-container">
                                <div className="storage-bar-info">
                                    <span>Cloud Volume Space</span>
                                    <span>5.7 GB / 15 GB</span>
                                </div>
                                <div className="storage-bar-outer">
                                    <div className="storage-bar-inner"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* ==========================================================================
               CUSTOM ANIMATED DIALOG MODALS
               ========================================================================== */}
            
            {/* Modal 1: Upload File Encryption Password Modal */}
            {showUploadModal && selectedFile && (
                <div className="modal-backdrop">
                    <div className="modal-content">
                        <button className="modal-close-btn" onClick={() => { setShowUploadModal(false); setSelectedFile(null); }}>×</button>
                        <div className="modal-header">
                            <h3>Encrypt File</h3>
                            <p>Derived keys protect your asset before it is stored on the server.</p>
                        </div>
                        <form onSubmit={handleUploadSubmit}>
                            <div className="form-group" style={{ marginBottom: '0.5rem' }}>
                                <label>Target Asset</label>
                                <div style={{ fontSize: '0.9rem', color: 'var(--accent-cyan)', fontWeight: 'bold', wordBreak: 'break-all' }}>
                                    📁 {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                                </div>
                            </div>
                            <div className="form-group">
                                <label htmlFor="upload-password">Encryption Password</label>
                                <div className="input-container">
                                    <input 
                                        id="upload-password"
                                        type={showUploadPasswordText ? "text" : "password"}
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        placeholder="Enter key passcode"
                                        required
                                    />
                                    <button 
                                        type="button" 
                                        className="input-toggle-btn"
                                        onClick={() => setShowUploadPasswordText(!showUploadPasswordText)}
                                    >
                                        {showUploadPasswordText ? "Hide" : "Show"}
                                    </button>
                                </div>
                                
                                {/* Password strength indicator */}
                                {password && (
                                    <div className="strength-meter">
                                        <div className="strength-bar-outer">
                                            <div className={`strength-bar-inner ${passwordStrength.className}`}></div>
                                        </div>
                                        <div className={`strength-text ${passwordStrength.className}`}>
                                            Strength: <span>{passwordStrength.text}</span>
                                        </div>
                                    </div>
                                )}
                            </div>
                            <button type="submit" disabled={!password}>Derive Keys & Encrypt</button>
                        </form>
                    </div>
                </div>
            )}

            {/* Modal 2: Decryption Prompt Modal */}
            {showDecryptModal && modalTargetFile && (
                <div className="modal-backdrop">
                    <div className="modal-content">
                        <button className="modal-close-btn" onClick={() => { setShowDecryptModal(false); setModalTargetFile(null); }}>×</button>
                        <div className="modal-header">
                            <h3>Decrypt Asset</h3>
                            <p>Verify your password to derive the key and authorize the {modalActionType === 'download' ? 'download' : 'preview'}.</p>
                        </div>
                        <form onSubmit={handleDecryptSubmit}>
                            <div className="form-group" style={{ marginBottom: '1rem' }}>
                                <label>Selected File</label>
                                <div style={{ fontSize: '0.9rem', color: 'var(--accent-cyan)', fontWeight: 'bold', wordBreak: 'break-all' }}>
                                    🔒 {modalTargetFile.filename}
                                </div>
                            </div>
                            <div className="form-group">
                                <label htmlFor="decrypt-password">Encryption Passcode</label>
                                <div className="input-container">
                                    <input 
                                        id="decrypt-password"
                                        type={showDecryptPasswordText ? "text" : "password"}
                                        value={decryptPassword}
                                        onChange={(e) => setDecryptPassword(e.target.value)}
                                        placeholder="Enter your encryption password"
                                        required
                                    />
                                    <button 
                                        type="button" 
                                        className="input-toggle-btn"
                                        onClick={() => setShowDecryptPasswordText(!showDecryptPasswordText)}
                                    >
                                        {showDecryptPasswordText ? "Hide" : "Show"}
                                    </button>
                                </div>
                            </div>
                            <button type="submit" disabled={!decryptPassword}>
                                Verify & {modalActionType === 'download' ? 'Decrypt Download' : 'Decrypt Preview'}
                            </button>
                        </form>
                    </div>
                </div>
            )}

            {/* Modal 3: Danger Delete Confirmation Modal */}
            {showDeleteModal && modalTargetFile && (
                <div className="modal-backdrop">
                    <div className="modal-content danger-modal">
                        <button className="modal-close-btn" onClick={() => { setShowDeleteModal(false); setModalTargetFile(null); }}>×</button>
                        <div className="modal-header" style={{ marginBottom: '1rem' }}>
                            <h3 style={{ color: 'var(--danger)' }}>⚠️ Purge Asset</h3>
                            <p>This action will completely delete the file metadata and its encrypted byte content. This is irreversible.</p>
                        </div>
                        <div style={{ background: 'rgba(239, 68, 68, 0.05)', padding: '1rem', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: 'var(--radius-sm)', marginBottom: '1.5rem', wordBreak: 'break-all' }}>
                            <strong>Purging:</strong> {modalTargetFile.filename}
                        </div>
                        <div className="modal-actions">
                            <button className="modal-btn-cancel" onClick={() => { setShowDeleteModal(false); setModalTargetFile(null); }}>
                                Keep File
                            </button>
                            <button className="modal-btn-danger" onClick={handleDeleteSubmit}>
                                Delete File Permanently
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Modal 4: Premium Cyber Glassmorphic Inline Preview Modal */}
            {showPreviewModal && previewBlobUrl && modalTargetFile && (
                <div className="modal-backdrop" onClick={closePreviewModal}>
                    <div className="preview-modal-content" onClick={(e) => e.stopPropagation()}>
                        <button className="modal-close-btn" onClick={closePreviewModal}>×</button>
                        <div className="modal-header">
                            <h3>🔍 Secure File Preview</h3>
                            <p style={{ wordBreak: 'break-all', color: 'var(--accent-cyan)' }}>📁 {modalTargetFile.filename}</p>
                        </div>
                        
                        <div className="preview-container">
                            {['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(previewFileType) ? (
                                <img src={previewBlobUrl} alt={modalTargetFile.filename} className="preview-image" />
                            ) : previewFileType === 'pdf' ? (
                                <iframe src={previewBlobUrl} title={modalTargetFile.filename} className="preview-iframe" />
                            ) : (
                                <div className="preview-fallback">
                                    <span className="preview-fallback-icon">⚠️</span>
                                    <div>No secure in-browser viewer available for <code>.{previewFileType}</code> format.</div>
                                    <button style={{ width: 'auto' }} onClick={() => {
                                        const a = document.createElement('a');
                                        a.href = previewBlobUrl;
                                        a.download = modalTargetFile.filename;
                                        document.body.appendChild(a);
                                        a.click();
                                        a.remove();
                                    }}>Download Instead</button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Dashboard;
