import React, { useState, useEffect } from 'react';
import {
  MessageSquare,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Play,
  Eye,
  Clock,
  ShieldAlert,
  Users,
  Briefcase
} from 'lucide-react';
import { apiUrl } from '../api';

export default function InterviewListView({ token, onSelectInterview }) {
  const [interviews, setInterviews] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchInterviews = async () => {
      try {
        const res = await fetch(apiUrl('/api/interviews'), {
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

    if (token) fetchInterviews();
  }, [token]);

  const STATUS_STYLES = {
    scheduled: { bg: 'bg-surface-3/50 border-surface-3 text-text-secondary', label: 'Scheduled' },
    in_progress: { bg: 'bg-brand-cyan/15 border-brand-cyan/30 text-brand-cyan', label: 'In Progress' },
    completed: { bg: 'bg-status-success/15 border-status-success/30 text-status-success', label: 'Completed' },
    cancelled: { bg: 'bg-surface-3/50 border-surface-3 text-text-muted', label: 'Cancelled' },
    aborted: { bg: 'bg-status-danger/15 border-status-danger/30 text-status-danger', label: 'Aborted' },
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-bold font-display text-text-primary tracking-tight flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-brand-cyan" />
          <span>Interview Sessions</span>
        </h2>
        <p className="text-xs text-text-secondary mt-1">
          Manage and review AI-powered candidate screening interviews.
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20 text-text-muted">
          <Loader2 className="w-5 h-5 animate-spin mr-2" />
          <span className="text-sm">Loading interviews...</span>
        </div>
      ) : interviews.length === 0 ? (
        <div className="p-12 rounded-2xl bg-surface-1 border border-surface-2 text-center">
          <div className="w-14 h-14 rounded-2xl bg-brand-cyan/10 border border-brand-cyan/20 flex items-center justify-center mx-auto mb-4">
            <MessageSquare className="w-7 h-7 text-brand-cyan" />
          </div>
          <h3 className="text-sm font-semibold text-text-primary">No Interviews Yet</h3>
          <p className="text-xs text-text-secondary mt-1 max-w-md mx-auto">
            Prepare an interview from a job's candidate detail view. The AI will generate a 5-category question roadmap targeting identified skill gaps.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {interviews.map((iv) => {
            const statusInfo = STATUS_STYLES[iv.status] || STATUS_STYLES.scheduled;
            return (
              <div
                key={iv.id}
                onClick={() => onSelectInterview(iv.id)}
                className="p-4 rounded-xl bg-surface-1 border border-surface-2 hover:border-brand-cyan/30 hover:shadow-lg hover:shadow-brand-cyan/5 transition cursor-pointer group"
              >
                <div className="flex items-center justify-between mb-3">
                  <span className={`text-[10px] font-mono px-2.5 py-0.5 rounded-full border ${statusInfo.bg}`}>
                    {statusInfo.label}
                  </span>
                  <div className="flex items-center gap-1.5">
                    {iv.tamper_flag && (
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-status-danger/15 border border-status-danger/30 text-status-danger flex items-center gap-0.5">
                        <ShieldAlert className="w-2.5 h-2.5" />
                        TAMPER
                      </span>
                    )}
                    {iv.has_evaluation && (
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-status-success/15 border border-status-success/30 text-status-success flex items-center gap-0.5">
                        <CheckCircle2 className="w-2.5 h-2.5" />
                        Evaluated
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 mb-2">
                  <Users className="w-3.5 h-3.5 text-brand-indigo shrink-0" />
                  <span className="text-xs font-semibold text-text-primary truncate">
                    {iv.candidate_name || 'Unknown Candidate'}
                  </span>
                </div>

                <div className="flex items-center gap-2 mb-3">
                  <Briefcase className="w-3.5 h-3.5 text-text-muted shrink-0" />
                  <span className="text-[10px] text-text-secondary truncate">
                    {iv.job_title || 'Unknown Position'}
                  </span>
                </div>

                <div className="flex items-center justify-between text-[10px] text-text-muted pt-2 border-t border-surface-2/60">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {iv.current_question_index}/{iv.total_questions} questions
                  </span>
                  <span>{new Date(iv.created_at).toLocaleDateString()}</span>
                  {iv.status === 'in_progress' || iv.status === 'scheduled' ? (
                    <Play className="w-3.5 h-3.5 text-brand-cyan opacity-0 group-hover:opacity-100 transition" />
                  ) : (
                    <Eye className="w-3.5 h-3.5 text-text-muted opacity-0 group-hover:opacity-100 transition" />
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
