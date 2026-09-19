import React, { useState } from 'react';
import { X, Briefcase, Plus, Trash2, AlertCircle, Loader2 } from 'lucide-react';
import { apiUrl } from '../api';

export default function CreateJobModal({ isOpen, onClose, onJobCreated, token }) {
  const [title, setTitle] = useState('');
  const [department, setDepartment] = useState('Engineering');
  const [status, setStatus] = useState('active');
  const [rawDescription, setRawDescription] = useState('');
  const [requirements, setRequirements] = useState([
    { requirement_text: '', requirement_type: 'must_have', category: 'skill', weight: 1.0 },
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleAddRequirement = () => {
    setRequirements([
      ...requirements,
      { requirement_text: '', requirement_type: 'must_have', category: 'skill', weight: 1.0 },
    ]);
  };

  const handleRemoveRequirement = (index) => {
    setRequirements(requirements.filter((_, i) => i !== index));
  };

  const handleRequirementChange = (index, field, value) => {
    const updated = [...requirements];
    updated[index][field] = value;
    setRequirements(updated);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!title.trim()) {
      setError('Job title is required.');
      return;
    }
    if (rawDescription.trim().length < 10) {
      setError('Job description must be at least 10 characters.');
      return;
    }

    setLoading(true);
    try {
      const validRequirements = requirements
        .filter((r) => r.requirement_text.trim().length > 0)
        .map((r) => ({
          requirement_text: r.requirement_text.trim(),
          requirement_type: r.requirement_type,
          category: r.category,
          weight: Number(r.weight) || 1.0,
        }));

      const res = await fetch(apiUrl('/api/jobs'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          title: title.trim(),
          department: department.trim(),
          status,
          raw_description: rawDescription.trim(),
          requirements: validRequirements,
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to create job.');
      }

      const createdJob = await res.json();
      onJobCreated(createdJob);
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-surface-1 border border-surface-2 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl my-8">
        <div className="px-6 py-4 border-b border-surface-2 flex items-center justify-between">
          <div className="flex items-center gap-2 text-text-primary font-display font-semibold">
            <Briefcase className="w-5 h-5 text-brand-cyan" />
            <span>Create New Job Requisition</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-2 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 flex flex-col gap-5 max-h-[80vh] overflow-y-auto">
          {error && (
            <div className="p-3 rounded-lg bg-status-danger/10 border border-status-danger/20 text-status-danger text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="sm:col-span-2 flex flex-col gap-1.5">
              <label className="text-xs font-medium text-text-secondary">Job Title *</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Senior Backend Engineer"
                className="px-3 py-2 rounded-lg bg-surface-2 border border-surface-3 text-text-primary text-sm focus:outline-none focus:border-brand-cyan transition"
                required
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-text-secondary">Department *</label>
              <input
                type="text"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                placeholder="Engineering"
                className="px-3 py-2 rounded-lg bg-surface-2 border border-surface-3 text-text-primary text-sm focus:outline-none focus:border-brand-cyan transition"
                required
              />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-text-secondary">Initial Status</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="px-3 py-2 rounded-lg bg-surface-2 border border-surface-3 text-text-primary text-sm focus:outline-none focus:border-brand-cyan transition"
            >
              <option value="draft">Draft (Private)</option>
              <option value="active">Active (Open for Ingestion)</option>
              <option value="paused">Paused</option>
              <option value="closed">Closed</option>
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <div className="flex justify-between items-center">
              <label className="text-xs font-medium text-text-secondary">Raw Job Description *</label>
              <span className="text-[10px] text-text-muted">{rawDescription.length} characters</span>
            </div>
            <textarea
              rows={5}
              value={rawDescription}
              onChange={(e) => setRawDescription(e.target.value)}
              placeholder="Paste raw job description, requirements, responsibilities, and qualifications..."
              className="px-3 py-2 rounded-lg bg-surface-2 border border-surface-3 text-text-primary text-sm focus:outline-none focus:border-brand-cyan transition resize-y font-sans"
              required
            />
          </div>

          {/* Requirements Builder */}
          <div className="flex flex-col gap-3 pt-2 border-t border-surface-2">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-xs font-semibold text-text-primary">Key Requirements (Optional)</h4>
                <p className="text-[11px] text-text-muted">Atomic criteria extracted for candidate screening</p>
              </div>
              <button
                type="button"
                onClick={handleAddRequirement}
                className="px-2.5 py-1 rounded-lg bg-surface-2 hover:bg-surface-3 border border-surface-3 text-xs font-medium text-brand-cyan flex items-center gap-1 transition"
              >
                <Plus className="w-3.5 h-3.5" />
                Add Requirement
              </button>
            </div>

            <div className="flex flex-col gap-2">
              {requirements.map((req, index) => (
                <div key={index} className="flex items-center gap-2 bg-surface-2/40 p-2 rounded-lg border border-surface-2">
                  <input
                    type="text"
                    placeholder="e.g. 5+ years Python and async programming"
                    value={req.requirement_text}
                    onChange={(e) => handleRequirementChange(index, 'requirement_text', e.target.value)}
                    className="flex-1 px-2.5 py-1.5 rounded bg-surface-1 border border-surface-3 text-xs text-text-primary focus:outline-none focus:border-brand-cyan"
                  />
                  <select
                    value={req.requirement_type}
                    onChange={(e) => handleRequirementChange(index, 'requirement_type', e.target.value)}
                    className="px-2 py-1.5 rounded bg-surface-1 border border-surface-3 text-xs text-text-secondary"
                  >
                    <option value="must_have">Must Have</option>
                    <option value="nice_to_have">Nice to Have</option>
                    <option value="preferred">Preferred</option>
                  </select>
                  <button
                    type="button"
                    onClick={() => handleRemoveRequirement(index)}
                    className="p-1.5 text-text-muted hover:text-status-danger rounded transition"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t border-surface-2 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-surface-2 hover:bg-surface-3 text-text-secondary text-xs font-medium transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 rounded-xl bg-brand-cyan hover:bg-brand-cyan/90 text-canvas text-xs font-bold flex items-center gap-2 shadow-lg shadow-brand-cyan/20 transition disabled:opacity-50"
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              {loading ? 'Creating Job...' : 'Create Job'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
