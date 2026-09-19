import React, { useState, useEffect } from 'react';
import {
  MessageSquare,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Play,
  Clock,
  ShieldAlert,
  ChevronRight,
  Brain,
  Target,
  Eye
} from 'lucide-react';

export default function InterviewPanel({
  jobId,
  candidateId,
  matchId,
  candidateName,
  jobTitle,
  token,
  onStartInterview
}) {
  const [interviews, setInterviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [preparing, setPreparing] = useState(false);
  const [error, setError] = useState(null);

  const fetchInterviews = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (jobId) params.set('job_id', jobId);
      if (candidateId) params.set('candidate_id', candidateId);

      const res = await fetch(`/api/interviews?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setInterviews(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token && (jobId || candidateId)) {
      fetchInterviews();
    }
  }, [token, jobId, candidateId]);

  const handlePrepareInterview = async () => {
    setPreparing(true);
    setError(null);
    try {
      const res = await fetch('/api/interviews/prepare', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_id: jobId,
          candidate_id: candidateId,
          match_id: matchId || null,
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to prepare interview');
      }

      const data = await res.json();
      // Navigate to the interview workspace
      if (onStartInterview) {
        onStartInterview(data.interview.id);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setPreparing(false);
    }
  };

  const STATUS_STYLES = {
    scheduled: 'bg-surface-3/50 border-surface-3 text-text-secondary',
    in_progress: 'bg-brand-cyan/15 border-brand-cyan/30 text-brand-cyan',
    completed: 'bg-status-success/15 border-status-success/30 text-status-success',
    cancelled: 'bg-surface-3/50 border-surface-3 text-text-muted',
    aborted: 'bg-status-danger/15 border-status-danger/30 text-status-danger',
  };

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-semibold text-text-primary flex items-center gap-1.5">
          <MessageSquare className="w-3.5 h-3.5 text-brand-cyan" />
          Interview Sessions
        </h4>
        <button
          onClick={handlePrepareInterview}
          disabled={preparing}
          className="px-3 py-1.5 rounded-lg bg-gradient-to-r from-brand-cyan to-brand-blue text-canvas text-[10px] font-bold hover:shadow-lg hover:shadow-brand-cyan/20 transition disabled:opacity-50 flex items-center gap-1.5"
        >
          {preparing ? (
            <>
              <Loader2 className="w-3 h-3 animate-spin" />
              Preparing...
            </>
          ) : (
            <>
              <Brain className="w-3 h-3" />
              Prepare Interview
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="p-2.5 rounded-lg bg-status-danger/10 border border-status-danger/20 text-status-danger text-[10px] flex items-center gap-1.5">
          <AlertCircle className="w-3 h-3 shrink-0" />
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-6 text-text-muted">
          <Loader2 className="w-4 h-4 animate-spin mr-2" />
          <span className="text-[10px]">Loading interviews...</span>
        </div>
      ) : interviews.length === 0 ? (
        <div className="p-4 rounded-lg bg-surface-2/40 border border-surface-2 text-center text-[10px] text-text-muted">
          No interview sessions yet. Click "Prepare Interview" to generate a 5-question roadmap.
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {interviews.map((iv) => (
            <div
              key={iv.id}
              className="p-3 rounded-lg bg-surface-2/40 border border-surface-2 hover:border-surface-3 transition cursor-pointer group"
              onClick={() => onStartInterview && onStartInterview(iv.id)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${STATUS_STYLES[iv.status] || STATUS_STYLES.scheduled}`}>
                    {iv.status?.toUpperCase()}
                  </span>
                  {iv.tamper_flag && (
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-status-danger/15 border border-status-danger/30 text-status-danger flex items-center gap-0.5">
                      <ShieldAlert className="w-2.5 h-2.5" />
                      TAMPER
                    </span>
                  )}
                  <span className="text-[10px] text-text-muted">
                    {iv.current_question_index}/{iv.total_questions} questions
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-text-muted">
                    {new Date(iv.created_at).toLocaleDateString()}
                  </span>
                  {iv.status === 'in_progress' || iv.status === 'scheduled' ? (
                    <Play className="w-3.5 h-3.5 text-brand-cyan opacity-0 group-hover:opacity-100 transition" />
                  ) : (
                    <Eye className="w-3.5 h-3.5 text-text-muted opacity-0 group-hover:opacity-100 transition" />
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
