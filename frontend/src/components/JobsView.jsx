import React, { useState, useEffect } from 'react';
import { 
  Briefcase, 
  Plus, 
  Search, 
  Users, 
  ArrowUpRight, 
  Layers, 
  Filter,
  Loader2,
  TrendingUp,
  Award,
  Clock,
  CheckCircle2,
  Sparkles
} from 'lucide-react';
import { apiUrl } from '../api';

const STATUS_COLORS = {
  active: 'bg-status-success/15 border-status-success/30 text-status-success',
  draft: 'bg-surface-3/50 border-surface-3 text-text-secondary',
  paused: 'bg-status-warning/15 border-status-warning/30 text-status-warning',
  closed: 'bg-status-danger/15 border-status-danger/30 text-status-danger',
};

export default function JobsView({ 
  jobs, 
  loading, 
  onSelectJob, 
  onOpenCreateJob,
  token
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [stats, setStats] = useState(null);
  const [loadingStats, setLoadingStats] = useState(false);

  useEffect(() => {
    if (!token) return;
    setLoadingStats(true);
    fetch(apiUrl('/api/stats/dashboard'), {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) setStats(data);
      })
      .catch((err) => console.error('Failed to load stats:', err))
      .finally(() => setLoadingStats(false));
  }, [token, jobs]);

  const filteredJobs = jobs.filter((job) => {
    const matchesSearch = 
      job.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      job.department.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || job.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const activeJobsCount = stats?.active_requisitions ?? jobs.filter((j) => j.status === 'active').length;
  const topMatchesCount = stats?.top_match_candidates ?? 0;
  const avgFidelity = stats?.avg_match_fidelity ?? 0.0;
  const hoursSaved = stats?.hours_saved ?? 0.0;

  return (
    <div className="flex flex-col gap-6 w-full">
      {/* KPI Stats Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-surface-1 border border-surface-2 flex items-center gap-3.5 shadow-sm">
          <div className="w-11 h-11 rounded-xl bg-brand-cyan/10 border border-brand-cyan/20 flex items-center justify-center text-brand-cyan">
            <Briefcase className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-mono text-text-muted uppercase block">Active Requisitions</span>
            <span className="text-xl font-bold font-display text-text-primary">{activeJobsCount}</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-surface-1 border border-surface-2 flex items-center gap-3.5 shadow-sm">
          <div className="w-11 h-11 rounded-xl bg-status-success/10 border border-status-success/20 flex items-center justify-center text-status-success">
            <Award className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-mono text-text-muted uppercase block">Top Matches (≥80%)</span>
            <span className="text-xl font-bold font-display text-text-primary">{topMatchesCount}</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-surface-1 border border-surface-2 flex items-center gap-3.5 shadow-sm">
          <div className="w-11 h-11 rounded-xl bg-brand-indigo/10 border border-brand-indigo/20 flex items-center justify-center text-brand-indigo">
            <TrendingUp className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-mono text-text-muted uppercase block">Avg Match Fidelity</span>
            <span className="text-xl font-bold font-display text-text-primary">{avgFidelity}%</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-surface-1 border border-surface-2 flex items-center gap-3.5 shadow-sm">
          <div className="w-11 h-11 rounded-xl bg-brand-cyan/10 border border-brand-cyan/20 flex items-center justify-center text-brand-cyan">
            <Clock className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-mono text-text-muted uppercase block">Recruiter Hours Saved</span>
            <span className="text-xl font-bold font-display text-text-primary">{hoursSaved} hrs</span>
          </div>
        </div>
      </div>

      {/* View Header & Action Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold font-display text-text-primary tracking-tight flex items-center gap-2.5">
            <Briefcase className="w-5 h-5 text-brand-cyan" />
            <span>Job Requisitions</span>
            <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-surface-2 text-text-muted border border-surface-3">
              {jobs.length}
            </span>
          </h2>
          <p className="text-xs text-text-secondary mt-1">
            Manage open roles, job descriptions, atomic requirements, and candidate pipelines.
          </p>
        </div>

        <button
          onClick={onOpenCreateJob}
          className="px-4 py-2 rounded-xl bg-brand-cyan hover:bg-brand-cyan/90 text-canvas text-xs font-bold flex items-center gap-2 shadow-lg shadow-brand-cyan/20 transition cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>Create New Job</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-surface-1 border border-surface-2">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by job title or department..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 rounded-lg bg-surface-2 border border-surface-3 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-cyan transition"
          />
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto">
          <Filter className="w-3.5 h-3.5 text-text-muted mr-1" />
          {['all', 'active', 'draft', 'paused', 'closed'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1 rounded-lg text-xs font-mono capitalize transition ${
                statusFilter === st
                  ? 'bg-surface-3 text-text-primary border border-surface-3 font-semibold'
                  : 'text-text-muted hover:text-text-secondary hover:bg-surface-2/60'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Jobs Grid */}
      {loading ? (
        <div className="flex flex-col items-center justify-center p-20 text-text-muted gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-brand-cyan" />
          <span className="text-xs font-mono">Loading job requisitions...</span>
        </div>
      ) : filteredJobs.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredJobs.map((job) => (
            <div
              key={job.id}
              onClick={() => onSelectJob(job.id)}
              className="p-5 rounded-2xl bg-surface-1 border border-surface-2 hover:border-brand-cyan/40 cursor-pointer transition flex flex-col justify-between gap-4 group shadow-xl hover:shadow-2xl hover:shadow-brand-cyan/5"
            >
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface-2 text-brand-cyan border border-surface-3">
                    {job.department}
                  </span>
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono border capitalize ${
                      STATUS_COLORS[job.status] || STATUS_COLORS.draft
                    }`}
                  >
                    {job.status}
                  </span>
                </div>

                <h3 className="text-base font-bold font-display text-text-primary group-hover:text-brand-cyan transition line-clamp-1">
                  {job.title}
                </h3>

                <p className="text-xs text-text-secondary line-clamp-2 leading-relaxed">
                  {job.raw_description}
                </p>
              </div>

              <div className="pt-3 border-t border-surface-2 flex items-center justify-between text-xs text-text-muted font-mono">
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1">
                    <Users className="w-3.5 h-3.5 text-brand-indigo" />
                    <span className="text-text-primary font-bold">{job.candidate_count}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Layers className="w-3.5 h-3.5 text-text-muted" />
                    <span>{job.requirements?.length || 0} reqs</span>
                  </div>
                </div>

                <div className="flex items-center gap-1 text-text-muted group-hover:text-brand-cyan transition font-sans text-[11px]">
                  <span>View Role</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-16 rounded-2xl bg-surface-1 border border-dashed border-surface-2 flex flex-col items-center justify-center text-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-surface-2 flex items-center justify-center text-text-muted">
            <Briefcase className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-text-primary">No job requisitions found</h3>
            <p className="text-xs text-text-muted mt-1 max-w-sm">
              {searchTerm || statusFilter !== 'all'
                ? 'Try adjusting your search query or status filter.'
                : 'Create your first job requisition or seed demo data to begin uploading resumes and managing candidates.'}
            </p>
          </div>
          {!searchTerm && statusFilter === 'all' && (
            <button
              onClick={onOpenCreateJob}
              className="mt-2 px-5 py-2 rounded-xl bg-brand-cyan hover:bg-brand-cyan/90 text-canvas text-xs font-bold shadow-lg shadow-brand-cyan/20 transition"
            >
              Create First Job
            </button>
          )}
        </div>
      )}
    </div>
  );
}
