import React, { useState, useRef } from 'react';
import { X, UploadCloud, FileText, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';

const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.txt'];
const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10MB

export default function UploadResumeModal({ isOpen, onClose, onUploaded, jobs, defaultJobId, token }) {
  const [file, setFile] = useState(null);
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [selectedJobId, setSelectedJobId] = useState(defaultJobId || '');
  const [dragOver, setDragOver] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const fileInputRef = useRef(null);

  if (!isOpen) return null;

  const validateFile = (selectedFile) => {
    setError(null);
    if (!selectedFile) return false;

    const ext = '.' + selectedFile.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setError(`Unsupported file type '${ext}'. Only PDF, DOCX, and TXT files are accepted.`);
      return false;
    }

    if (selectedFile.size > MAX_FILE_SIZE_BYTES) {
      setError(`File size (${(selectedFile.size / (1024 * 1024)).toFixed(2)}MB) exceeds maximum limit of 10MB.`);
      return false;
    }

    if (selectedFile.size === 0) {
      setError('Selected file is empty (0 bytes).');
      return false;
    }

    return true;
  };

  const handleFileChange = (e) => {
    const selected = e.target.files?.[0];
    if (selected && validateFile(selected)) {
      setFile(selected);
      // Auto-suggest name if empty
      if (!fullName) {
        const rawName = selected.name.replace(/\.[^/.]+$/, '');
        const clean = rawName.replace(/[_-]/g, ' ').replace(/(resume|cv)/gi, '').trim();
        if (clean) {
          setFullName(clean.replace(/\b\w/g, (c) => c.toUpperCase()));
        }
      }
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped && validateFile(dropped)) {
      setFile(dropped);
      if (!fullName) {
        const rawName = dropped.name.replace(/\.[^/.]+$/, '');
        const clean = rawName.replace(/[_-]/g, ' ').replace(/(resume|cv)/gi, '').trim();
        if (clean) {
          setFullName(clean.replace(/\b\w/g, (c) => c.toUpperCase()));
        }
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!file) {
      setError('Please select a resume file to upload.');
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (fullName.trim()) formData.append('full_name', fullName.trim());
      if (email.trim()) formData.append('email', email.trim());
      if (selectedJobId) formData.append('job_id', selectedJobId);

      const res = await fetch('/api/candidates/upload', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Resume upload failed.');
      }

      const candidateData = await res.json();
      setUploadSuccess(candidateData);
      onUploaded(candidateData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResetAndClose = () => {
    setFile(null);
    setFullName('');
    setEmail('');
    setError(null);
    setUploadSuccess(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-surface-1 border border-surface-2 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl my-8">
        <div className="px-6 py-4 border-b border-surface-2 flex items-center justify-between">
          <div className="flex items-center gap-2 text-text-primary font-display font-semibold">
            <UploadCloud className="w-5 h-5 text-brand-cyan" />
            <span>Upload Candidate Resume</span>
          </div>
          <button
            onClick={handleResetAndClose}
            className="p-1 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-2 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {uploadSuccess ? (
          <div className="p-8 flex flex-col items-center text-center gap-4">
            <div className="w-14 h-14 rounded-full bg-status-success/20 text-status-success flex items-center justify-center shadow-lg shadow-status-success/10">
              <CheckCircle2 className="w-8 h-8" />
            </div>
            <div>
              <h3 className="text-base font-bold text-text-primary">Resume Ingested Successfully</h3>
              <p className="text-xs text-text-secondary mt-1">
                Candidate profile created for <span className="text-text-primary font-semibold">{uploadSuccess.full_name}</span>.
              </p>
            </div>

            <div className="w-full p-4 rounded-xl bg-surface-2/60 border border-surface-2 text-left flex flex-col gap-2 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-text-muted">Document:</span>
                <span className="text-text-primary truncate max-w-[200px]">{uploadSuccess.resumes?.[0]?.file_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Size:</span>
                <span className="text-text-primary">
                  {((uploadSuccess.resumes?.[0]?.file_size_bytes || 0) / 1024).toFixed(1)} KB
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Parsing Status:</span>
                <span className="text-brand-cyan px-2 py-0.5 rounded bg-brand-cyan/10 border border-brand-cyan/20">
                  {uploadSuccess.resumes?.[0]?.parsing_status || 'pending'} (Pre-processing)
                </span>
              </div>
            </div>

            <button
              onClick={handleResetAndClose}
              className="w-full py-2.5 rounded-xl bg-brand-cyan hover:bg-brand-cyan/90 text-canvas text-xs font-bold transition shadow-lg shadow-brand-cyan/20"
            >
              Done & Return
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="p-6 flex flex-col gap-4">
            {error && (
              <div className="p-3 rounded-lg bg-status-danger/10 border border-status-danger/20 text-status-danger text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Dropzone */}
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`p-6 border-2 border-dashed rounded-xl flex flex-col items-center justify-center gap-2 cursor-pointer transition ${
                dragOver
                  ? 'border-brand-cyan bg-brand-cyan/10'
                  : file
                  ? 'border-brand-cyan/60 bg-surface-2/40'
                  : 'border-surface-3 hover:border-surface-2 bg-surface-2/20'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleFileChange}
                className="hidden"
              />
              <div className="w-10 h-10 rounded-full bg-surface-2 flex items-center justify-center text-brand-cyan">
                {file ? <FileText className="w-5 h-5" /> : <UploadCloud className="w-5 h-5" />}
              </div>
              <div className="text-center">
                {file ? (
                  <>
                    <p className="text-xs font-semibold text-text-primary">{file.name}</p>
                    <p className="text-[10px] text-text-muted">{(file.size / 1024).toFixed(1)} KB — Click to change</p>
                  </>
                ) : (
                  <>
                    <p className="text-xs font-medium text-text-primary">
                      Drag & drop resume here, or <span className="text-brand-cyan">browse</span>
                    </p>
                    <p className="text-[10px] text-text-muted mt-0.5">Supports PDF, DOCX, TXT up to 10MB</p>
                  </>
                )}
              </div>
            </div>

            {/* Target Job Selector */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-text-secondary">Associate with Job Requisition</label>
              <select
                value={selectedJobId}
                onChange={(e) => setSelectedJobId(e.target.value)}
                className="px-3 py-2 rounded-lg bg-surface-2 border border-surface-3 text-text-primary text-sm focus:outline-none focus:border-brand-cyan"
              >
                <option value="">-- General Ingestion (No specific job) --</option>
                {jobs &&
                  jobs.map((j) => (
                    <option key={j.id} value={j.id}>
                      {j.title} ({j.department})
                    </option>
                  ))}
              </select>
            </div>

            {/* Optional Metadata */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-medium text-text-secondary">Candidate Name (Optional)</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Auto-extracted if blank"
                  className="px-3 py-2 rounded-lg bg-surface-2 border border-surface-3 text-text-primary text-xs focus:outline-none focus:border-brand-cyan"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-medium text-text-secondary">Email (Optional)</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Auto-generated if blank"
                  className="px-3 py-2 rounded-lg bg-surface-2 border border-surface-3 text-text-primary text-xs focus:outline-none focus:border-brand-cyan"
                />
              </div>
            </div>

            <div className="pt-3 border-t border-surface-2 flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={handleResetAndClose}
                className="px-4 py-2 rounded-xl bg-surface-2 hover:bg-surface-3 text-text-secondary text-xs font-medium transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading || !file}
                className="px-5 py-2 rounded-xl bg-brand-cyan hover:bg-brand-cyan/90 text-canvas text-xs font-bold flex items-center gap-2 shadow-lg shadow-brand-cyan/20 transition disabled:opacity-50"
              >
                {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                {loading ? 'Uploading...' : 'Upload & Ingest'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
