import React, { useState, useEffect } from 'react';
import { 
  ArrowLeft, 
  Briefcase, 
  Users, 
  UploadCloud, 
  CheckCircle2, 
  Calendar, 
  Clock, 
  Layers, 
  AlertCircle,
  Loader2,
  ChevronRight,
  Sparkles,
  Award,
  BarChart3,
  Check,
  X,
  Quote,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  Target,
  FileText,
  MessageSquare
} from 'lucide-react';

const STATUS_COLORS = {
  active: 'bg-status-success/15 border-status-success/30 text-status-success',
  draft: 'bg-surface-3/50 border-surface-3 text-text-secondary',
  paused: 'bg-status-warning/15 border-status-warning/30 text-status-warning',
  closed: 'bg-status-danger/15 border-status-danger/30 text-status-danger',
};

export default function JobDetailView({ 
  jobId, 
  onBack, 
  token, 
  onOpenUpload, 
  onSelectCandidate,
  onStartInterview 
}) {
  const [job, setJob] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [activeTab, setActiveTab] = useState('matches'); // Default to matches in Phase 4
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [isExtractingCriteria, setIsExtractingCriteria] = useState(false);
  const [criteriaError, setCriteriaError] = useState(null);

  // Phase 4 Matching states
  const [matchResults, setMatchResults] = useState([]);
  const [isRunningMatching, setIsRunningMatching] = useState(false);
  const [matchError, setMatchError] = useState(null);
  const [expandedMatchId, setExpandedMatchId] = useState(null);
  const [preparingInterviewFor, setPreparingInterviewFor] = useState(null);

  const fetchJobDetails = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/jobs/${jobId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        throw new Error('Failed to load job details.');
      }
      const data = await res.json();
      setJob(data);

      // Fetch candidates for this job
      const candRes = await fetch(`/api/candidates?job_id=${jobId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (candRes.ok) {
        const candData = await candRes.json();
        setCandidates(candData);
      }

      // Fetch existing match results
      await fetchMatchResults();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchMatchResults = async () => {
    try {
      const res = await fetch(`/api/matching/${jobId}/results`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setMatchResults(data);
      }
    } catch (err) {
      // Non-blocking
    }
  };

  useEffect(() => {
    if (jobId) {
      fetchJobDetails();
    }
  }, [jobId]);

  const handleStatusChange = async (newStatus) => {
    setUpdatingStatus(true);
    try {
      const res = await fetch(`/api/jobs/${jobId}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ status: newStatus }),
      });
      if (res.ok) {
        const updated = await res.json();
        setJob(updated);
      }
    } catch (err) {
      // Ignore
    } finally {
      setUpdatingStatus(false);
    }
  };

  const handleExtractCriteria = async () => {
    setCriteriaError(null);
    setIsExtractingCriteria(true);
    try {
      const res = await fetch(`/api/jobs/${jobId}/parse-jd`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to extract criteria.');
      }
      await fetchJobDetails();
    } catch (err) {
      setCriteriaError(err.message);
    } finally {
      setIsExtractingCriteria(false);
    }
  };

  const handleRunMatching = async () => {
    setMatchError(null);
    setIsRunningMatching(true);
    try {
      const res = await fetch(`/api/matching/${jobId}/run`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to execute matching engine.');
      }
      const data = await res.json();
      setMatchResults(data.matches || []);
      // Refresh candidates to sync pipeline stages
      const candRes = await fetch(`/api/candidates?job_id=${jobId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (candRes.ok) {
        setCandidates(await candRes.json());
      }
      setActiveTab('matches');
    } catch (err) {
      setMatchError(err.message);
    } finally {
      setIsRunningMatching(false);
    }
  };

  const toggleExpand = (matchId) => {
    setExpandedMatchId(expandedMatchId === matchId ? null : matchId);
  };

  const handlePrepareInterview = async (match) => {
    setPreparingInterviewFor(match.match_id);
    try {
      const res = await fetch('/api/interviews/prepare', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_id: jobId,
          candidate_id: match.candidate_id,
          match_id: match.match_id,
        }),
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to prepare interview');
      }
      const data = await res.json();
      if (onStartInterview) {
        onStartInterview(data.interview.id);
      }
    } catch (err) {
      setMatchError(err.message);
    } finally {
      setPreparingInterviewFor(null);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-20 text-text-muted gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-brand-cyan" />
        <span className="text-xs font-mono">Loading job requisition...</span>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="p-8 flex flex-col items-center justify-center gap-4 text-center">
        <AlertCircle className="w-10 h-10 text-status-danger" />
        <p className="text-sm text-status-danger">{error || 'Job not found'}</p>
        <button
          onClick={onBack}
          className="px-4 py-2 rounded-xl bg-surface-2 hover:bg-surface-3 text-xs font-medium text-text-primary flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" /> Return to Jobs
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 w-full">
      {/* Top Bar with Back button, Status switcher, and Actions */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <button
          onClick={onBack}
          className="px-3 py-1.5 rounded-lg bg-surface-2 hover:bg-surface-3 border border-surface-3 text-xs font-medium text-text-secondary hover:text-text-primary flex items-center gap-1.5 transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Jobs</span>
        </button>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs">
            <span className="text-text-muted font-mono">Status:</span>
            <select
              value={job.status}
              disabled={updatingStatus}
              onChange={(e) => handleStatusChange(e.target.value)}
              className={`px-3 py-1 rounded-lg border text-xs font-mono capitalize cursor-pointer focus:outline-none ${
                STATUS_COLORS[job.status] || STATUS_COLORS.draft
              }`}
            >
              <option value="draft">Draft</option>
              <option value="active">Active</option>
              <option value="paused">Paused</option>
              <option value="closed">Closed</option>
            </select>
          </div>

          <button
            onClick={handleRunMatching}
            disabled={isRunningMatching}
            className="px-3.5 py-1.5 rounded-lg bg-brand-cyan/20 hover:bg-brand-cyan/30 border border-brand-cyan/40 text-brand-cyan text-xs font-bold flex items-center gap-1.5 shadow-sm transition disabled:opacity-50"
          >
            {isRunningMatching ? (
              <Loader2 className="w-4 h-4 animate-spin text-brand-cyan" />
            ) : (
              <Sparkles className="w-4 h-4 text-brand-cyan" />
            )}
            <span>{isRunningMatching ? 'Evaluating...' : 'Run Match Analysis'}</span>
          </button>

          <button
            onClick={() => onOpenUpload(job.id)}
            className="px-4 py-1.5 rounded-lg bg-brand-cyan hover:bg-brand-cyan/90 text-canvas text-xs font-bold flex items-center gap-1.5 shadow-md shadow-brand-cyan/20 transition"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Upload Resume</span>
          </button>
        </div>
      </div>

      {/* Job Header Card */}
      <div className="p-6 rounded-2xl bg-surface-1 border border-surface-2 flex flex-col gap-4 shadow-xl">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-surface-2 text-brand-cyan border border-surface-3">
                {job.department}
              </span>
              <span className="text-text-muted text-[11px] font-mono">ID: {job.id.slice(0, 8)}</span>
            </div>
            <h1 className="text-xl md:text-2xl font-bold font-display text-text-primary tracking-tight">
              {job.title}
            </h1>
          </div>

          <div className="flex items-center gap-4 text-xs font-mono text-text-muted">
            <div className="flex items-center gap-1.5">
              <Calendar className="w-4 h-4 text-text-secondary" />
              <span>Created {new Date(job.created_at).toLocaleDateString()}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Users className="w-4 h-4 text-brand-indigo" />
              <span className="text-text-primary font-bold">{candidates.length}</span> candidates
            </div>
            {matchResults.length > 0 && (
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-brand-cyan/10 border border-brand-cyan/30 text-brand-cyan font-bold">
                <Award className="w-3.5 h-3.5" />
                <span>Top Match: {matchResults[0].overall_match_score}%</span>
              </div>
            )}
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex border-b border-surface-2 pt-2 gap-6 text-xs font-medium">
          <button
            onClick={() => setActiveTab('matches')}
            className={`pb-3 flex items-center gap-2 border-b-2 transition ${
              activeTab === 'matches'
                ? 'border-brand-cyan text-brand-cyan font-bold'
                : 'border-transparent text-text-muted hover:text-text-secondary'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Match Intelligence & Rankings ({matchResults.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('overview')}
            className={`pb-3 flex items-center gap-2 border-b-2 transition ${
              activeTab === 'overview'
                ? 'border-brand-cyan text-brand-cyan font-bold'
                : 'border-transparent text-text-muted hover:text-text-secondary'
            }`}
          >
            <Briefcase className="w-4 h-4" />
            <span>Overview & Requirements</span>
          </button>
          <button
            onClick={() => setActiveTab('candidates')}
            className={`pb-3 flex items-center gap-2 border-b-2 transition ${
              activeTab === 'candidates'
                ? 'border-brand-cyan text-brand-cyan font-bold'
                : 'border-transparent text-text-muted hover:text-text-secondary'
            }`}
          >
            <Users className="w-4 h-4" />
            <span>All Linked Candidates ({candidates.length})</span>
          </button>
        </div>
      </div>

      {/* Match Error Alert */}
      {matchError && (
        <div className="p-4 rounded-xl bg-status-danger/10 border border-status-danger/30 text-status-danger text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{matchError}</span>
        </div>
      )}

      {/* Tab Content: MATCH INTELLIGENCE (Phase 4) */}
      {activeTab === 'matches' && (
        <div className="flex flex-col gap-6">
          {/* Header Action Banner */}
          <div className="p-5 rounded-2xl bg-gradient-to-r from-surface-1 via-surface-2/40 to-surface-1 border border-surface-2 flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-brand-cyan" />
                <h3 className="text-sm font-bold font-display text-text-primary">
                  Two-Stage Candidate Intelligence & Matching Engine
                </h3>
              </div>
              <p className="text-xs text-text-secondary">
                Combines Stage 1 cosine vector semantic similarity with Stage 2 deterministic heuristic re-ranking (50% skill overlap, 25% experience fit, 25% vector similarity).
              </p>
            </div>

            <button
              onClick={handleRunMatching}
              disabled={isRunningMatching}
              className="px-4 py-2 rounded-xl bg-brand-cyan hover:bg-brand-cyan/90 text-canvas text-xs font-bold flex items-center gap-2 shadow-lg shadow-brand-cyan/20 transition disabled:opacity-50"
            >
              {isRunningMatching ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Target className="w-4 h-4" />
              )}
              <span>{matchResults.length > 0 ? 'Re-Run Match Evaluation' : 'Run Match Analysis'}</span>
            </button>
          </div>

          {/* Ranked Candidate Match Cards */}
          {matchResults.length > 0 ? (
            <div className="flex flex-col gap-4">
              {matchResults.map((match, idx) => {
                const isExpanded = expandedMatchId === match.match_id;
                const score = match.overall_match_score;
                const scoreColor =
                  score >= 75
                    ? 'text-status-success border-status-success/30 bg-status-success/10'
                    : score >= 50
                    ? 'text-status-warning border-status-warning/30 bg-status-warning/10'
                    : 'text-status-danger border-status-danger/30 bg-status-danger/10';

                return (
                  <div
                    key={match.match_id}
                    className="rounded-2xl bg-surface-1 border border-surface-2 overflow-hidden shadow-lg transition hover:border-surface-3"
                  >
                    {/* Card Header Summary */}
                    <div className="p-5 flex flex-wrap items-start justify-between gap-4">
                      <div className="flex items-start gap-3.5">
                        <div className="w-8 h-8 rounded-xl bg-surface-2 border border-surface-3 flex items-center justify-center font-mono font-bold text-xs text-brand-cyan shrink-0">
                          #{idx + 1}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="text-base font-bold text-text-primary">{match.candidate_name}</h4>
                            <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-surface-2 text-text-secondary border border-surface-3">
                              {match.pipeline_stage}
                            </span>
                          </div>
                          <p className="text-xs text-text-secondary mt-0.5">
                            {match.current_title || 'Software Engineer'} {match.current_company ? `• ${match.current_company}` : ''}
                            {match.years_of_experience !== null ? ` • ${match.years_of_experience} yrs exp` : ''}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-4">
                        {/* Overall Score Badge */}
                        <div className={`px-4 py-2 rounded-xl border flex flex-col items-center justify-center ${scoreColor}`}>
                          <span className="text-lg font-mono font-bold">{score}%</span>
                          <span className="text-[9px] font-mono uppercase tracking-wider opacity-80">Match Score</span>
                        </div>

                        <button
                          onClick={() => toggleExpand(match.match_id)}
                          className="px-3 py-2 rounded-xl bg-surface-2 hover:bg-surface-3 border border-surface-3 text-xs font-medium text-text-secondary hover:text-text-primary flex items-center gap-1.5 transition"
                        >
                          <span>{isExpanded ? 'Hide Details' : 'View Audit'}</span>
                          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </button>

                        <button
                          onClick={(e) => { e.stopPropagation(); handlePrepareInterview(match); }}
                          disabled={preparingInterviewFor === match.match_id}
                          className="px-3 py-2 rounded-xl bg-gradient-to-r from-brand-cyan to-brand-blue text-canvas text-xs font-bold flex items-center gap-1.5 hover:shadow-lg hover:shadow-brand-cyan/20 transition disabled:opacity-50"
                        >
                          {preparingInterviewFor === match.match_id ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <MessageSquare className="w-3.5 h-3.5" />
                          )}
                          <span>Interview</span>
                        </button>
                      </div>
                    </div>

                    {/* Score Formula Breakdown Pills */}
                    <div className="px-5 py-2.5 bg-surface-2/30 border-t border-b border-surface-2/60 flex flex-wrap items-center gap-3 text-xs font-mono">
                      <div className="flex items-center gap-1.5">
                        <span className="text-text-muted">Skill Overlap (50%):</span>
                        <span className="font-bold text-brand-cyan">{match.skill_overlap_score}%</span>
                      </div>
                      <span className="text-surface-3">•</span>
                      <div className="flex items-center gap-1.5">
                        <span className="text-text-muted">Experience Fit (25%):</span>
                        <span className="font-bold text-brand-indigo">{match.experience_fit_score}%</span>
                      </div>
                      <span className="text-surface-3">•</span>
                      <div className="flex items-center gap-1.5">
                        <span className="text-text-muted">Vector Cosine Sim (25%):</span>
                        <span className="font-bold text-text-primary">{(match.vector_similarity * 100).toFixed(1)}%</span>
                      </div>
                    </div>

                    {/* Matched & Missing Skills Snapshot */}
                    <div className="p-5 flex flex-col gap-3">
                      {/* Grounded Reasoning Callout */}
                      <div className="p-3.5 rounded-xl bg-surface-2/40 border border-surface-2 flex items-start gap-2.5 text-xs">
                        <ShieldCheck className="w-4 h-4 text-brand-cyan shrink-0 mt-0.5" />
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted font-mono">
                            Grounded Match Intelligence Reasoning
                          </span>
                          <p className="text-text-secondary leading-relaxed font-sans">{match.reasoning}</p>
                        </div>
                      </div>

                      {/* Skills Badges */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                        {/* Confirmed Matched Skills */}
                        <div className="flex flex-col gap-1.5">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-status-success font-mono flex items-center gap-1">
                            <Check className="w-3 h-3" /> Confirmed Matched Requirements ({match.matched_skills?.length || 0})
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {match.matched_skills && match.matched_skills.length > 0 ? (
                              match.matched_skills.map((m, idx) => (
                                <span
                                  key={idx}
                                  className="px-2.5 py-1 rounded-lg bg-status-success/10 border border-status-success/20 text-status-success text-xs font-mono flex items-center gap-1"
                                >
                                  <span>✓</span>
                                  <span>{m.skill}</span>
                                </span>
                              ))
                            ) : (
                              <span className="text-xs text-text-muted italic">No verified matches.</span>
                            )}
                          </div>
                        </div>

                        {/* Missing Gaps */}
                        <div className="flex flex-col gap-1.5">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-status-danger font-mono flex items-center gap-1">
                            <X className="w-3 h-3" /> Missing Requirement Gaps ({match.missing_skills?.length || 0})
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {match.missing_skills && match.missing_skills.length > 0 ? (
                              match.missing_skills.map((m, idx) => (
                                <span
                                  key={idx}
                                  className="px-2.5 py-1 rounded-lg bg-status-danger/10 border border-status-danger/20 text-status-danger text-xs font-mono flex items-center gap-1"
                                >
                                  <span>✕</span>
                                  <span>{m.skill}</span>
                                </span>
                              ))
                            ) : (
                              <span className="text-xs text-text-muted italic">No gaps detected.</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Detailed Requirement Breakdown Drawer */}
                    {isExpanded && (
                      <div className="p-5 bg-surface-2/20 border-t border-surface-2 flex flex-col gap-3 animate-in fade-in duration-200">
                        <div className="flex items-center justify-between">
                          <h5 className="text-xs font-bold uppercase tracking-wider text-text-primary font-mono flex items-center gap-1.5">
                            <Layers className="w-3.5 h-3.5 text-brand-cyan" />
                            <span>Audit Trail: Requirement-by-Requirement Evidence Provenance</span>
                          </h5>
                          <span className="text-[10px] font-mono text-text-muted">
                            {match.requirements_breakdown?.length || 0} Criteria Evaluated
                          </span>
                        </div>

                        <div className="flex flex-col gap-2.5">
                          {match.requirements_breakdown && match.requirements_breakdown.length > 0 ? (
                            match.requirements_breakdown.map((item, idx) => {
                              const isMatched = item.status === 'MATCHED';
                              const isMissing = item.status === 'MISSING';
                              return (
                                <div
                                  key={idx}
                                  className={`p-3 rounded-xl border flex flex-col gap-1.5 text-xs ${
                                    isMatched
                                      ? 'bg-surface-1 border-status-success/30'
                                      : isMissing
                                      ? 'bg-surface-1 border-status-danger/30'
                                      : 'bg-surface-1 border-status-warning/30'
                                  }`}
                                >
                                  <div className="flex items-center justify-between">
                                    <span className="font-bold text-text-primary flex items-center gap-1.5">
                                      {isMatched ? (
                                        <CheckCircle2 className="w-3.5 h-3.5 text-status-success shrink-0" />
                                      ) : (
                                        <AlertCircle className="w-3.5 h-3.5 text-status-danger shrink-0" />
                                      )}
                                      <span>{item.requirement_text}</span>
                                    </span>
                                    <div className="flex items-center gap-2">
                                      <span className="text-[10px] font-mono text-text-muted">wt: {item.weight}</span>
                                      <span
                                        className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                                          isMatched
                                            ? 'bg-status-success/15 text-status-success'
                                            : isMissing
                                            ? 'bg-status-danger/15 text-status-danger'
                                            : 'bg-status-warning/15 text-status-warning'
                                        }`}
                                      >
                                        {item.status}
                                      </span>
                                    </div>
                                  </div>

                                  {item.evidence_quote && (
                                    <div className="p-2 rounded-lg bg-surface-2/50 border border-surface-2 text-[11px] text-text-secondary flex items-start gap-1.5">
                                      <Quote className="w-3 h-3 text-brand-cyan shrink-0 mt-0.5" />
                                      <span className="italic font-sans">"{item.evidence_quote}"</span>
                                    </div>
                                  )}
                                </div>
                              );
                            })
                          ) : (
                            <p className="text-xs text-text-muted italic">No requirement items recorded.</p>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="p-14 rounded-2xl bg-surface-1 border border-dashed border-surface-2 flex flex-col items-center justify-center text-center gap-3">
              <Target className="w-12 h-12 text-text-muted opacity-40" />
              <div>
                <h4 className="text-sm font-bold text-text-primary">No Match Analysis Run Yet</h4>
                <p className="text-xs text-text-muted mt-1 max-w-md">
                  Click "Run Match Analysis" to execute the two-stage vector semantic similarity and deterministic heuristic re-ranking across all candidates.
                </p>
              </div>
              <button
                onClick={handleRunMatching}
                disabled={isRunningMatching}
                className="mt-2 px-5 py-2 rounded-xl bg-brand-cyan hover:bg-brand-cyan/90 text-canvas text-xs font-bold shadow-lg shadow-brand-cyan/20 transition flex items-center gap-2"
              >
                {isRunningMatching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                <span>Execute AI Matching</span>
              </button>
            </div>
          )}
        </div>
      )}

      {/* Tab Content: OVERVIEW */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left 2 Cols: Raw Job Description */}
          <div className="lg:col-span-2 p-6 rounded-2xl bg-surface-1 border border-surface-2 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold font-display text-text-primary">Job Description</h3>
              <span className="text-[10px] font-mono px-2.5 py-0.5 rounded bg-surface-2 text-text-muted border border-surface-3">
                {job.department} • {job.employment_type || 'Full-time'}
              </span>
            </div>
            <div className="p-4 rounded-xl bg-surface-2/30 border border-surface-2/60 text-xs text-text-secondary leading-relaxed whitespace-pre-wrap font-sans">
              {job.raw_description}
            </div>
          </div>

          {/* Right Col: Atomic Requirements & Extracted Criteria */}
          <div className="p-6 rounded-2xl bg-surface-1 border border-surface-2 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold font-display text-text-primary flex items-center gap-2">
                <Layers className="w-4 h-4 text-brand-cyan" />
                <span>Job Criteria & Skills</span>
              </h3>
              <button
                onClick={handleExtractCriteria}
                disabled={isExtractingCriteria}
                className="px-2.5 py-1 rounded-lg bg-brand-cyan/15 hover:bg-brand-cyan/25 border border-brand-cyan/30 text-brand-cyan text-xs font-bold flex items-center gap-1.5 transition disabled:opacity-50 cursor-pointer shadow-sm shadow-brand-cyan/10"
              >
                {isExtractingCriteria ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <Sparkles className="w-3 h-3" />
                )}
                <span>{isExtractingCriteria ? 'Extracting...' : 'Extract Criteria'}</span>
              </button>
            </div>

            {criteriaError && (
              <div className="p-3 rounded-lg bg-status-danger/10 border border-status-danger/20 text-status-danger text-xs flex items-center gap-2">
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                <span>{criteriaError}</span>
              </div>
            )}

            {/* Extracted Structured Competencies & Seniority */}
            {job.parsed_criteria && (job.parsed_criteria.required_skills?.length > 0 || job.parsed_criteria.preferred_skills?.length > 0 || job.parsed_criteria.seniority) && (
              <div className="p-4 rounded-xl bg-surface-2/40 border border-surface-2 flex flex-col gap-3 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10px] text-text-muted uppercase font-bold tracking-wider">
                    Target Profile
                  </span>
                  {job.parsed_criteria.seniority && (
                    <span className="px-2.5 py-0.5 rounded-full bg-brand-cyan/15 text-brand-cyan border border-brand-cyan/30 font-mono text-[10px] font-bold">
                      {job.parsed_criteria.seniority}
                    </span>
                  )}
                </div>

                {/* Required Tech Skills */}
                {job.parsed_criteria.required_skills?.length > 0 && (
                  <div className="flex flex-col gap-1.5">
                    <span className="text-[10px] font-mono text-text-muted">Core Required Skills:</span>
                    <div className="flex flex-wrap gap-1.5">
                      {job.parsed_criteria.required_skills.map((s, idx) => (
                        <span
                          key={idx}
                          className="px-2.5 py-0.5 rounded-lg bg-brand-cyan/10 border border-brand-cyan/20 text-brand-cyan font-mono text-[11px] font-medium"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Preferred Tech Skills */}
                {job.parsed_criteria.preferred_skills?.length > 0 && (
                  <div className="flex flex-col gap-1.5 pt-1 border-t border-surface-3/50">
                    <span className="text-[10px] font-mono text-text-muted">Preferred / Nice-to-Have:</span>
                    <div className="flex flex-wrap gap-1.5">
                      {job.parsed_criteria.preferred_skills.map((s, idx) => (
                        <span
                          key={idx}
                          className="px-2.5 py-0.5 rounded-lg bg-brand-indigo/10 border border-brand-indigo/20 text-brand-indigo font-mono text-[11px] font-medium"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Atomic Criteria Cards */}
            {job.requirements && job.requirements.length > 0 ? (
              <div className="flex flex-col gap-2.5">
                <div className="flex items-center justify-between font-mono text-[10px] text-text-muted uppercase">
                  <span>Atomic Criteria ({job.requirements.length})</span>
                  <span>Weighted Scoring</span>
                </div>

                {job.requirements.map((req) => {
                  const isMust = req.requirement_type === 'must_have';
                  const isNice = req.requirement_type === 'nice_to_have';
                  const typeLabel = isMust ? 'Must Have' : isNice ? 'Preferred' : 'Responsibility';
                  const typeBadgeColor = isMust
                    ? 'bg-status-success/15 text-status-success border-status-success/30'
                    : isNice
                    ? 'bg-brand-indigo/15 text-brand-indigo border-brand-indigo/30'
                    : 'bg-brand-cyan/15 text-brand-cyan border-brand-cyan/30';

                  const categoryLabel = req.category ? req.category.replace('_', ' ') : 'requirement';

                  return (
                    <div
                      key={req.id}
                      className="p-3 rounded-xl bg-surface-2/40 border border-surface-2 hover:border-surface-3 transition flex flex-col gap-2 text-xs"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1.5">
                          <span className={`text-[10px] font-mono px-2 py-0.5 rounded-md uppercase font-bold border ${typeBadgeColor}`}>
                            {typeLabel}
                          </span>
                          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-surface-1 text-text-muted border border-surface-3 capitalize">
                            {categoryLabel}
                          </span>
                        </div>
                        <span className="text-[10px] font-mono text-text-muted">
                          wt: {Number(req.weight).toFixed(1)}x
                        </span>
                      </div>
                      <p className="text-text-primary leading-snug">{req.requirement_text}</p>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="p-6 rounded-xl bg-surface-2/20 border border-dashed border-surface-3 flex flex-col items-center justify-center text-center gap-2">
                <Layers className="w-8 h-8 text-text-muted opacity-40" />
                <p className="text-xs text-text-muted">
                  No criteria extracted yet. Click <span className="font-bold text-brand-cyan">"Extract Criteria"</span> to parse requirements, tech stack, and responsibilities.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab Content: CANDIDATES */}
      {activeTab === 'candidates' && (
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold font-display text-text-primary">
              Candidates Linked to {job.title}
            </h3>
            <button
              onClick={() => onOpenUpload(job.id)}
              className="px-3 py-1.5 rounded-lg bg-surface-2 hover:bg-surface-3 border border-surface-3 text-xs font-medium text-brand-cyan flex items-center gap-1.5"
            >
              <UploadCloud className="w-3.5 h-3.5" />
              <span>Upload New Resume</span>
            </button>
          </div>

          {candidates.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {candidates.map((cand) => (
                <div
                  key={cand.id}
                  onClick={() => onSelectCandidate(cand)}
                  className="p-4 rounded-xl bg-surface-1 border border-surface-2 hover:border-brand-cyan/50 cursor-pointer transition flex flex-col gap-3 group shadow-lg"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="text-sm font-bold text-text-primary group-hover:text-brand-cyan transition">
                        {cand.full_name}
                      </h4>
                      <p className="text-xs text-text-secondary mt-0.5">
                        {cand.current_title || 'Software Engineer'} • {cand.current_company || 'Independent'}
                      </p>
                    </div>
                    <ChevronRight className="w-4 h-4 text-text-muted group-hover:text-brand-cyan transition" />
                  </div>

                  {cand.skills && cand.skills.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {cand.skills.slice(0, 4).map((s) => (
                        <span
                          key={s.id}
                          className="px-2 py-0.5 rounded bg-surface-2 text-[10px] font-mono text-text-secondary"
                        >
                          {s.skill_name}
                        </span>
                      ))}
                      {cand.skills.length > 4 && (
                        <span className="text-[10px] text-text-muted self-center">
                          +{cand.skills.length - 4} more
                        </span>
                      )}
                    </div>
                  )}

                  <div className="flex items-center justify-between text-[11px] font-mono text-text-muted pt-2 border-t border-surface-2">
                    <span>{cand.years_of_experience ? `${cand.years_of_experience} yrs exp` : 'Exp unset'}</span>
                    <span className="text-brand-cyan">
                      {cand.resumes?.length || 0} resume doc{cand.resumes?.length === 1 ? '' : 's'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-12 rounded-2xl bg-surface-1 border border-dashed border-surface-2 flex flex-col items-center justify-center text-center gap-3">
              <Users className="w-10 h-10 text-text-muted opacity-40" />
              <div>
                <h4 className="text-sm font-bold text-text-primary">No candidates linked to this requisition yet</h4>
                <p className="text-xs text-text-muted mt-1 max-w-sm">
                  Upload resumes to automatically associate candidates with this job role.
                </p>
              </div>
              <button
                onClick={() => onOpenUpload(job.id)}
                className="mt-2 px-4 py-2 rounded-xl bg-brand-cyan text-canvas text-xs font-bold shadow-md shadow-brand-cyan/20 transition"
              >
                Upload First Resume
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
