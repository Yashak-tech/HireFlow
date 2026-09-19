import React, { useState, useEffect, useRef } from 'react';
import {
  ArrowLeft,
  MessageSquare,
  Send,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  Clock,
  ChevronRight,
  Brain,
  Target,
  Users,
  Heart,
  Compass,
  SkipForward,
  AlertCircle,
  Play
} from 'lucide-react';

const CATEGORY_META = {
  technical_depth: { label: 'Technical Depth', icon: Brain, color: 'brand-cyan' },
  gap_probe: { label: 'Gap Probe', icon: Target, color: 'brand-blue' },
  behavioral: { label: 'Behavioral', icon: Users, color: 'brand-indigo' },
  culture_fit: { label: 'Culture Fit', icon: Heart, color: 'status-success' },
  situational: { label: 'Situational', icon: Compass, color: 'status-warning' },
};

export default function InterviewWorkspace({ interviewId, onBack, token }) {
  const [interview, setInterview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [candidateInput, setCandidateInput] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [turnHistory, setTurnHistory] = useState([]);
  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [turnHistory]);

  const fetchInterview = async () => {
    try {
      setLoading(true);
      const res = await fetch(`/api/interviews/${interviewId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Failed to load interview');
      const data = await res.json();
      setInterview(data);

      // Build turn history from existing answers
      const history = [];
      const sortedQuestions = [...(data.questions || [])].sort((a, b) => a.order_index - b.order_index);
      for (const q of sortedQuestions) {
        const qAnswers = (data.answers || [])
          .filter(a => a.question_id === q.id)
          .sort((a, b) => new Date(a.created_at) - new Date(b.created_at));

        if (qAnswers.length > 0) {
          history.push({ type: 'question', data: q });
          for (const ans of qAnswers) {
            history.push({ type: 'answer', data: ans });
            if (ans.follow_up_prompt) {
              history.push({ type: 'follow_up', text: ans.follow_up_prompt });
            }
          }
        }
      }

      // If interview is in progress and current question hasn't been answered, show it
      if (data.status === 'in_progress' || data.status === 'scheduled') {
        const currentIdx = data.current_question_index;
        const currentQ = sortedQuestions[currentIdx];
        const hasAnswers = currentQ && (data.answers || []).some(a => a.question_id === currentQ.id);
        if (currentQ && !hasAnswers) {
          history.push({ type: 'question', data: currentQ });
        }
      }

      setTurnHistory(history);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (interviewId && token) {
      fetchInterview();
    }
  }, [interviewId, token]);

  const handleSubmitTurn = async () => {
    if (!candidateInput.trim() || submitting) return;

    const inputText = candidateInput.trim();
    setCandidateInput('');
    setSubmitting(true);

    // Optimistically add answer to history
    setTurnHistory(prev => [...prev, { type: 'answer', data: { transcript_text: inputText, attempt_number: 1 } }]);

    try {
      const res = await fetch(`/api/interviews/${interviewId}/turn`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ candidate_input: inputText }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to process turn');
      }

      const turnData = await res.json();

      // Update interview state
      setInterview(prev => ({
        ...prev,
        status: turnData.status,
        current_question_index: turnData.current_question_index,
        tamper_flag: turnData.tamper_flag,
        tamper_details: turnData.tamper_details,
      }));

      // Add AI response to history
      if (turnData.follow_up_prompt) {
        setTurnHistory(prev => [...prev, { type: 'follow_up', text: turnData.follow_up_prompt }]);
      } else if (turnData.ai_message) {
        if (turnData.next_question) {
          setTurnHistory(prev => [...prev, { type: 'question', data: turnData.next_question }]);
        } else if (turnData.status === 'completed') {
          setTurnHistory(prev => [...prev, { type: 'system', text: turnData.ai_message }]);
        } else if (turnData.status === 'aborted') {
          setTurnHistory(prev => [...prev, { type: 'tamper', text: turnData.ai_message, details: turnData.tamper_details }]);
        }
      }
    } catch (err) {
      setTurnHistory(prev => [...prev, { type: 'error', text: err.message }]);
    } finally {
      setSubmitting(false);
    }
  };

  const handleStartInterview = async () => {
    if (!interview) return;

    // If scheduled, submitting the first turn will start it
    const sortedQuestions = [...(interview.questions || [])].sort((a, b) => a.order_index - b.order_index);
    if (sortedQuestions.length > 0 && interview.status === 'scheduled') {
      setInterview(prev => ({ ...prev, status: 'in_progress' }));
      const firstQ = sortedQuestions[0];
      setTurnHistory([{ type: 'question', data: firstQ }]);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmitTurn();
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 text-text-muted">
        <Loader2 className="w-6 h-6 animate-spin mr-2" />
        <span className="text-sm">Loading interview session...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="p-6 rounded-xl bg-status-danger/10 border border-status-danger/20 text-status-danger text-sm">
          <AlertCircle className="w-5 h-5 mb-2" />
          {error}
        </div>
      </div>
    );
  }

  if (!interview) return null;

  const sortedQuestions = [...(interview.questions || [])].sort((a, b) => a.order_index - b.order_index);
  const isActive = interview.status === 'in_progress' || interview.status === 'scheduled';
  const isCompleted = interview.status === 'completed';
  const isAborted = interview.status === 'aborted';

  return (
    <div className="flex flex-col gap-4 h-full">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={onBack}
          className="p-2 rounded-lg hover:bg-surface-2 text-text-muted hover:text-text-primary transition"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div className="flex-1">
          <h2 className="text-lg font-bold font-display text-text-primary flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-brand-cyan" />
            Interview Session
          </h2>
          <div className="flex items-center gap-3 text-xs text-text-secondary mt-0.5">
            <span>{interview.candidate_name || 'Candidate'}</span>
            <span className="text-text-muted">•</span>
            <span>{interview.job_title || 'Position'}</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Status badge */}
          <span className={`text-[10px] font-mono px-2.5 py-1 rounded-full border ${
            isCompleted ? 'bg-status-success/15 border-status-success/30 text-status-success' :
            isAborted ? 'bg-status-danger/15 border-status-danger/30 text-status-danger' :
            isActive ? 'bg-brand-cyan/15 border-brand-cyan/30 text-brand-cyan' :
            'bg-surface-3/50 border-surface-3 text-text-secondary'
          }`}>
            {interview.status?.toUpperCase()}
          </span>

          {/* Tamper indicator */}
          {interview.tamper_flag && (
            <span className="text-[10px] font-mono px-2.5 py-1 rounded-full bg-status-danger/15 border border-status-danger/30 text-status-danger flex items-center gap-1">
              <ShieldAlert className="w-3 h-3" />
              TAMPER
            </span>
          )}

          {/* Progress */}
          <span className="text-[10px] font-mono px-2.5 py-1 rounded-full bg-surface-2 border border-surface-3 text-text-muted">
            {Math.min(interview.current_question_index, sortedQuestions.length)}/{sortedQuestions.length} Q
          </span>
        </div>
      </div>

      {/* Main Content: Split view */}
      <div className="flex gap-4 flex-1 min-h-0" style={{ height: 'calc(100vh - 260px)' }}>
        {/* Left: Question Roadmap Sidebar */}
        <div className="w-64 shrink-0 p-4 rounded-xl bg-surface-1 border border-surface-2 overflow-y-auto">
          <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">
            Question Roadmap
          </h3>
          <div className="flex flex-col gap-2">
            {sortedQuestions.map((q, idx) => {
              const meta = CATEGORY_META[q.category] || CATEGORY_META.technical_depth;
              const Icon = meta.icon;
              const isAnswered = idx < interview.current_question_index;
              const isCurrent = idx === interview.current_question_index && isActive;

              return (
                <div
                  key={q.id}
                  className={`p-2.5 rounded-lg border text-xs transition ${
                    isCurrent
                      ? `bg-${meta.color}/10 border-${meta.color}/30 text-text-primary ring-1 ring-${meta.color}/20`
                      : isAnswered
                      ? 'bg-surface-2/40 border-surface-3/60 text-text-muted'
                      : 'bg-surface-2/20 border-surface-2 text-text-muted'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    {isAnswered ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-status-success shrink-0" />
                    ) : (
                      <Icon className={`w-3.5 h-3.5 shrink-0 ${isCurrent ? `text-${meta.color}` : 'text-text-muted'}`} />
                    )}
                    <span className={`font-semibold ${isCurrent ? `text-${meta.color}` : ''}`}>
                      {meta.label}
                    </span>
                  </div>
                  <p className="text-[10px] text-text-muted line-clamp-2 pl-5.5">
                    {q.question_text.substring(0, 80)}...
                  </p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Chat Area */}
        <div className="flex-1 flex flex-col rounded-xl bg-surface-1 border border-surface-2 overflow-hidden">
          {/* Chat messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {/* Interview not started yet */}
            {interview.status === 'scheduled' && turnHistory.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full gap-4 text-text-muted">
                <div className="w-16 h-16 rounded-2xl bg-brand-cyan/10 border border-brand-cyan/20 flex items-center justify-center">
                  <Play className="w-8 h-8 text-brand-cyan" />
                </div>
                <div className="text-center">
                  <p className="text-sm font-semibold text-text-primary">Ready to begin interview</p>
                  <p className="text-xs text-text-secondary mt-1">
                    {sortedQuestions.length} questions prepared across {new Set(sortedQuestions.map(q => q.category)).size} categories
                  </p>
                </div>
                <button
                  onClick={handleStartInterview}
                  className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-brand-cyan to-brand-blue text-canvas text-xs font-bold hover:shadow-lg hover:shadow-brand-cyan/20 transition"
                >
                  Start Interview
                </button>
              </div>
            )}

            {/* Turn history */}
            {turnHistory.map((turn, idx) => {
              if (turn.type === 'question') {
                const meta = CATEGORY_META[turn.data.category] || CATEGORY_META.technical_depth;
                const Icon = meta.icon;
                return (
                  <div key={idx} className="flex gap-3">
                    <div className={`w-8 h-8 rounded-xl bg-${meta.color}/15 border border-${meta.color}/25 flex items-center justify-center shrink-0 mt-0.5`}>
                      <Icon className={`w-4 h-4 text-${meta.color}`} />
                    </div>
                    <div className="flex-1 p-3 rounded-xl bg-surface-2/60 border border-surface-3 max-w-[85%]">
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full bg-${meta.color}/10 text-${meta.color}`}>
                          {meta.label}
                        </span>
                        <span className="text-[10px] text-text-muted">Q{turn.data.order_index + 1}</span>
                      </div>
                      <p className="text-xs text-text-primary leading-relaxed whitespace-pre-wrap">
                        {turn.data.question_text}
                      </p>
                      {turn.data.targeted_gap && (
                        <p className="text-[10px] text-text-muted mt-2 flex items-center gap-1">
                          <Target className="w-3 h-3" />
                          Probing: {turn.data.targeted_gap}
                        </p>
                      )}
                    </div>
                  </div>
                );
              }

              if (turn.type === 'answer') {
                return (
                  <div key={idx} className="flex gap-3 justify-end">
                    <div className="p-3 rounded-xl bg-brand-cyan/10 border border-brand-cyan/20 max-w-[85%]">
                      <p className="text-xs text-text-primary leading-relaxed whitespace-pre-wrap">
                        {turn.data.transcript_text}
                      </p>
                      {turn.data.attempt_number > 1 && (
                        <p className="text-[10px] text-text-muted mt-1">Follow-up response (attempt {turn.data.attempt_number})</p>
                      )}
                    </div>
                    <div className="w-8 h-8 rounded-xl bg-brand-indigo/15 border border-brand-indigo/25 flex items-center justify-center shrink-0 mt-0.5">
                      <Users className="w-4 h-4 text-brand-indigo" />
                    </div>
                  </div>
                );
              }

              if (turn.type === 'follow_up') {
                return (
                  <div key={idx} className="flex gap-3">
                    <div className="w-8 h-8 rounded-xl bg-status-warning/15 border border-status-warning/25 flex items-center justify-center shrink-0 mt-0.5">
                      <AlertTriangle className="w-4 h-4 text-status-warning" />
                    </div>
                    <div className="p-3 rounded-xl bg-status-warning/5 border border-status-warning/20 max-w-[85%]">
                      <p className="text-[10px] font-semibold text-status-warning mb-1">Follow-up Needed</p>
                      <p className="text-xs text-text-primary leading-relaxed">{turn.text}</p>
                    </div>
                  </div>
                );
              }

              if (turn.type === 'system') {
                return (
                  <div key={idx} className="flex gap-3">
                    <div className="w-8 h-8 rounded-xl bg-status-success/15 border border-status-success/25 flex items-center justify-center shrink-0 mt-0.5">
                      <CheckCircle2 className="w-4 h-4 text-status-success" />
                    </div>
                    <div className="p-3 rounded-xl bg-status-success/5 border border-status-success/20 max-w-[85%]">
                      <p className="text-xs text-text-primary leading-relaxed">{turn.text}</p>
                    </div>
                  </div>
                );
              }

              if (turn.type === 'tamper') {
                return (
                  <div key={idx} className="flex gap-3">
                    <div className="w-8 h-8 rounded-xl bg-status-danger/15 border border-status-danger/25 flex items-center justify-center shrink-0 mt-0.5">
                      <ShieldAlert className="w-4 h-4 text-status-danger" />
                    </div>
                    <div className="p-3 rounded-xl bg-status-danger/5 border border-status-danger/20 max-w-[85%]">
                      <p className="text-[10px] font-bold text-status-danger mb-1">⚠ Security Violation Detected</p>
                      <p className="text-xs text-text-primary leading-relaxed">{turn.text}</p>
                      {turn.details && (
                        <p className="text-[10px] text-text-muted mt-1">
                          Category: {turn.details.category} — {turn.details.reason}
                        </p>
                      )}
                    </div>
                  </div>
                );
              }

              if (turn.type === 'error') {
                return (
                  <div key={idx} className="p-3 rounded-xl bg-status-danger/10 border border-status-danger/20 text-xs text-status-danger">
                    Error: {turn.text}
                  </div>
                );
              }

              return null;
            })}

            <div ref={chatEndRef} />
          </div>

          {/* Input area */}
          {isActive && (
            <div className="border-t border-surface-2 p-3 bg-surface-1">
              <div className="flex gap-2 items-end">
                <textarea
                  value={candidateInput}
                  onChange={(e) => setCandidateInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Type your answer here... (Enter to send, Shift+Enter for new line)"
                  rows={2}
                  className="flex-1 px-3 py-2.5 rounded-xl bg-surface-2 border border-surface-3 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-cyan/40 focus:ring-1 focus:ring-brand-cyan/20 resize-none"
                  disabled={submitting}
                />
                <button
                  onClick={handleSubmitTurn}
                  disabled={submitting || !candidateInput.trim()}
                  className="p-2.5 rounded-xl bg-gradient-to-r from-brand-cyan to-brand-blue text-canvas hover:shadow-lg hover:shadow-brand-cyan/20 transition disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
                >
                  {submitting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                </button>
              </div>
              <div className="flex items-center gap-3 mt-2 text-[10px] text-text-muted">
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  Question {Math.min(interview.current_question_index + 1, sortedQuestions.length)} of {sortedQuestions.length}
                </span>
                {interview.tamper_flag && (
                  <span className="flex items-center gap-1 text-status-danger">
                    <ShieldAlert className="w-3 h-3" />
                    Tamper detected
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Completed state */}
          {isCompleted && (
            <div className="border-t border-surface-2 p-4 bg-status-success/5 text-center">
              <div className="flex items-center justify-center gap-2 text-sm text-status-success font-semibold">
                <CheckCircle2 className="w-4 h-4" />
                Interview Complete
              </div>
              <p className="text-[10px] text-text-muted mt-1">
                All {sortedQuestions.length} questions answered. Evaluation pending.
              </p>
            </div>
          )}

          {/* Aborted state */}
          {isAborted && (
            <div className="border-t border-surface-2 p-4 bg-status-danger/5 text-center">
              <div className="flex items-center justify-center gap-2 text-sm text-status-danger font-semibold">
                <ShieldAlert className="w-4 h-4" />
                Interview Terminated
              </div>
              <p className="text-[10px] text-text-muted mt-1">
                Session aborted due to security violation.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
