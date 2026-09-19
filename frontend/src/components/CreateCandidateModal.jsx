import React, { useState } from 'react';
import { X, UserPlus, AlertCircle, Loader2 } from 'lucide-react';
import { apiUrl } from '../api';

export default function CreateCandidateModal({ isOpen, onClose, onCandidateCreated, jobs, defaultJobId, token }) {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [location, setLocation] = useState('');
  const [currentTitle, setCurrentTitle] = useState('');
  const [currentCompany, setCurrentCompany] = useState('');
  const [yearsOfExperience, setYearsOfExperience] = useState('');
  const [linkedinUrl, setLinkedinUrl] = useState('');
  const [githubUrl, setGithubUrl] = useState('');
  const [portfolioUrl, setPortfolioUrl] = useState('');
  const [selectedJobId, setSelectedJobId] = useState(defaultJobId || '');
  const [skillsString, setSkillsString] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!fullName.trim()) {
      setError('Candidate full name is required.');
      return;
    }
    if (!email.trim()) {
      setError('Email address is required.');
      return;
    }

    setLoading(true);
    try {
      // Parse skills string separated by comma
      const parsedSkills = skillsString
        .split(',')
        .map((s) => s.trim())
        .filter((s) => s.length > 0)
        .map((name) => ({
          skill_name: name,
          category: 'technical',
          verification_status: 'unverified',
        }));

      const payload = {
        full_name: fullName.trim(),
        email: email.trim(),
        phone: phone.trim() || null,
        location: location.trim() || null,
        current_title: currentTitle.trim() || null,
        current_company: currentCompany.trim() || null,
        years_of_experience: yearsOfExperience ? parseFloat(yearsOfExperience) : null,
        linkedin_url: linkedinUrl.trim() || null,
        github_url: githubUrl.trim() || null,
        portfolio_url: portfolioUrl.trim() || null,
        job_id: selectedJobId || null,
        skills: parsedSkills,
      };

      const res = await fetch(apiUrl('/api/candidates'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to create candidate.');
      }

      const created = await res.json();
      onCandidateCreated(created);
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-surface-1 border border-surface-2 rounded-2xl w-full max-w-xl overflow-hidden shadow-2xl my-8">
        <div className="px-6 py-4 border-b border-surface-2 flex items-center justify-between">
          <div className="flex items-center gap-2 text-text-primary font-display font-semibold">
            <UserPlus className="w-5 h-5 text-brand-indigo" />
            <span>Add Candidate Profile</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-2 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 flex flex-col gap-4 max-h-[80vh] overflow-y-auto">
          {error && (
            <div className="p-3 rounded-lg bg-status-danger/10 border border-status-danger/20 text-status-danger text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-text-secondary">Full Name *</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Elena Rostova"
                className="px-3 py-2 rounded-lg bg-surface-2 border border-surface-3 text-text-primary text-sm focus:outline-none focus:border-brand-indigo"
                required
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-text-secondary">Email Address *</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="elena.rostova@engineer.dev"
                className="px-3 py-2 rounded-lg bg-surface-2 border border-surface-3 text-text-primary text-sm focus:outline-none focus:border-brand-indigo"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-text-secondary">Current Job Title</label>
              <input
                type="text"
                value={currentTitle}
                onChange={(e) => setCurrentTitle(e.target.value)}
                placeholder="Senior Systems Engineer"
                className="px-3 py-2 rounded-lg bg-surface-2 border border-surface-3 text-text-primary text-sm focus:outline-none focus:border-brand-indigo"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-text-secondary">Current Company</label>
              <input
                type="text"
                value={currentCompany}
                onChange={(e) => setCurrentCompany(e.target.value)}
                placeholder="OpenScale Labs"
                className="px-3 py-2 rounded-lg bg-surface-2 border border-surface-3 text-text-primary text-sm focus:outline-none focus:border-brand-indigo"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-text-secondary">Years of Experience</label>
              <input
                type="number"
                step="0.5"
                min="0"
                max="50"
                value={yearsOfExperience}
                onChange={(e) => setYearsOfExperience(e.target.value)}
                placeholder="6.5"
                className="px-3 py-2 rounded-lg bg-surface-2 border border-surface-3 text-text-primary text-sm focus:outline-none focus:border-brand-indigo"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-text-secondary">Location</label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="San Francisco, CA"
                className="px-3 py-2 rounded-lg bg-surface-2 border border-surface-3 text-text-primary text-sm focus:outline-none focus:border-brand-indigo"
              />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-text-secondary">Associate with Job Requisition</label>
            <select
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
              className="px-3 py-2 rounded-lg bg-surface-2 border border-surface-3 text-text-primary text-sm focus:outline-none focus:border-brand-indigo"
            >
              <option value="">-- No Immediate Job Association --</option>
              {jobs &&
                jobs.map((j) => (
                  <option key={j.id} value={j.id}>
                    {j.title} ({j.department})
                  </option>
                ))}
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-text-secondary">Primary Skills (comma separated)</label>
            <input
              type="text"
              value={skillsString}
              onChange={(e) => setSkillsString(e.target.value)}
              placeholder="Python, PostgreSQL, Docker, FastAPI, Kubernetes"
              className="px-3 py-2 rounded-lg bg-surface-2 border border-surface-3 text-text-primary text-sm focus:outline-none focus:border-brand-indigo"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-text-secondary">LinkedIn Profile URL</label>
              <input
                type="url"
                value={linkedinUrl}
                onChange={(e) => setLinkedinUrl(e.target.value)}
                placeholder="https://linkedin.com/in/..."
                className="px-3 py-2 rounded-lg bg-surface-2 border border-surface-3 text-text-primary text-sm focus:outline-none focus:border-brand-indigo"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-text-secondary">GitHub Profile URL</label>
              <input
                type="url"
                value={githubUrl}
                onChange={(e) => setGithubUrl(e.target.value)}
                placeholder="https://github.com/..."
                className="px-3 py-2 rounded-lg bg-surface-2 border border-surface-3 text-text-primary text-sm focus:outline-none focus:border-brand-indigo"
              />
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
              className="px-5 py-2 rounded-xl bg-brand-indigo hover:bg-brand-indigo/90 text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-brand-indigo/20 transition disabled:opacity-50"
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              {loading ? 'Adding Candidate...' : 'Add Candidate'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
