import React, { useState, useEffect } from 'react';
import { 
  X, 
  User, 
  Mail, 
  Phone, 
  MapPin, 
  Briefcase, 
  FileText, 
  Calendar, 
  Edit3, 
  Check, 
  AlertCircle,
  Loader2,
  Sparkles,
  ShieldCheck,
  Quote,
  Eye,
  EyeOff,
  GraduationCap,
  Award,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Send,
  MessageSquare,
  ArrowRight,
  Lock
} from 'lucide-react';

export default function CandidateDetailModal({ isOpen, onClose, candidate, onCandidateUpdated, token }) {
  const [activeTab, setActiveTab] = useState('profile'); // 'profile' | 'evaluation'
  const [isEditing, setIsEditing] = useState(false);
  const [fullName, setFullName] = useState(candidate?.full_name || '');
  const [email, setEmail] = useState(candidate?.email || '');
  const [phone, setPhone] = useState(candidate?.phone || '');
  const [location, setLocation] = useState(candidate?.location || '');
  const [currentTitle, setCurrentTitle] = useState(candidate?.current_title || '');
  const [currentCompany, setCurrentCompany] = useState(candidate?.current_company || '');
  const [yearsOfExperience, setYearsOfExperience] = useState(candidate?.years_of_experience || '');
  const [linkedinUrl, setLinkedinUrl] = useState(candidate?.linkedin_url || '');
  const [githubUrl, setGithubUrl] = useState(candidate?.github_url || '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  // Phase 3 Intelligence states
  const [isParsing, setIsParsing] = useState(false);
  const [parseError, setParseError] = useState(null);
  const [evidenceList, setEvidenceList] = useState([]);
  const [loadingEvidence, setLoadingEvidence] = useState(false);
  const [showMaskedProfile, setShowMaskedProfile] = useState(false);
  const [maskedProfile, setMaskedProfile] = useState(null);

  // Phase 5 & 7 Evaluation & Decision states
  const [evaluation, setEvaluation] = useState(null);
  const [interviewId, setInterviewId] = useState(null);
  const [loadingEvaluation, setLoadingEvaluation] = useState(false);
  const [decisionAction, setDecisionAction] = useState('advance');
  const [decisionNotes, setDecisionNotes] = useState('');
  const [submittingDecision, setSubmittingDecision] = useState(false);
  const [decisionSuccess, setDecisionSuccess] = useState(null);

  useEffect(() => {
    if (candidate) {
      setFullName(candidate.full_name || '');
      setEmail(candidate.email || '');
      setPhone(candidate.phone || '');
      setLocation(candidate.location || '');
      setCurrentTitle(candidate.current_title || '');
      setCurrentCompany(candidate.current_company || '');
      setYearsOfExperience(candidate.years_of_experience || '');
      setLinkedinUrl(candidate.linkedin_url || '');
      setGithubUrl(candidate.github_url || '');
      setError(null);
      setParseError(null);
      setDecisionSuccess(null);
      fetchEvidence();
      fetchCandidateEvaluation();
    }
  }, [candidate]);

  const fetchEvidence = async () => {
    if (!candidate?.id || !token) return;
    setLoadingEvidence(true);
    try {
      const res = await fetch(`/api/candidates/${candidate.id}/evidence`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setEvidenceList(data);
      }
    } catch (e) {
      // Non-blocking
    } finally {
      setLoadingEvidence(false);
    }
  };

  const fetchCandidateEvaluation = async () => {
    if (!candidate?.id || !token) return;
    setLoadingEvaluation(true);
    setEvaluation(null);
    setInterviewId(null);

    try {
      // Fetch interviews to find one for this candidate
      const res = await fetch('/api/interviews', {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.ok) {
        const interviews = await res.json();
        const candInterview = interviews.find((intv) => intv.candidate_id === candidate.id);
        if (candInterview) {
          setInterviewId(candInterview.id);
          // Fetch evaluation for this interview
          const evalRes = await fetch(`/api/interviews/${candInterview.id}/evaluation`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          if (evalRes.ok) {
            const evalData = await evalRes.json();
            setEvaluation(evalData);
            if (evalData.human_decision) {
              setDecisionAction(evalData.human_decision);
              setDecisionNotes(evalData.human_decision_notes || '');
            }
          }
        }
      }
    } catch (err) {
      console.error('Error fetching evaluation:', err);
    } finally {
      setLoadingEvaluation(false);
    }
  };

  const handleFetchMaskedProfile = async () => {
    if (maskedProfile) {
      setShowMaskedProfile(!showMaskedProfile);
      return;
    }
    try {
      const res = await fetch(`/api/candidates/${candidate.id}/masked-profile`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setMaskedProfile(data.anonymized_profile);
        setShowMaskedProfile(true);
      }
    } catch (e) {
      // Non-blocking
    }
  };

  const handleParseResume = async (resumeId = null) => {
    setParseError(null);
    setIsParsing(true);
    try {
      const url = resumeId 
        ? `/api/candidates/${candidate.id}/parse-resume?resume_id=${resumeId}`
        : `/api/candidates/${candidate.id}/parse-resume`;
      
      const res = await fetch(url, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Resume parsing failed.');
      }

      // Re-fetch updated candidate details
      const candRes = await fetch(`/api/candidates/${candidate.id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (candRes.ok) {
        const updated = await candRes.json();
        onCandidateUpdated(updated);
      }
      await fetchEvidence();
    } catch (err) {
      setParseError(err.message);
    } finally {
      setIsParsing(false);
    }
  };

  const handleSave = async () => {
    setError(null);
    setSaving(true);
    try {
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
      };

      const res = await fetch(`/api/candidates/${candidate.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to update candidate.');
      }

      const updated = await res.json();
      onCandidateUpdated(updated);
      setIsEditing(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleSubmitHumanDecision = async () => {
    if (!interviewId) return;
    setSubmittingDecision(true);
    setDecisionSuccess(null);
    setError(null);

    try {
      const res = await fetch(`/api/interviews/${interviewId}/evaluation/decision`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          decision: decisionAction,
          notes: decisionNotes.trim() || 'Recruiter verified and signed off.',
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to submit decision.');
      }

      const updatedEval = await res.json();
      setEvaluation(updatedEval);
      setDecisionSuccess(`Human decision recorded: ${decisionAction.toUpperCase()}`);

      // Re-fetch candidate to reflect updated pipeline stage
      const candRes = await fetch(`/api/candidates/${candidate.id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (candRes.ok) {
        const updatedCand = await candRes.json();
        onCandidateUpdated(updatedCand);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmittingDecision(false);
    }
  };

  if (!isOpen || !candidate) return null;

  const parsedProfile = candidate.parsed_profile || {};
  const activeResume = candidate.resumes && candidate.resumes.length > 0 ? candidate.resumes[0] : null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-surface-1 border border-surface-2 rounded-2xl w-full max-w-3xl overflow-hidden shadow-2xl my-8 flex flex-col max-h-[85vh]">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-surface-2 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-brand-indigo/10 border border-brand-indigo/20 text-brand-indigo flex items-center justify-center font-bold font-display">
              {candidate.full_name?.charAt(0) || 'C'}
            </div>
            <div>
              <h3 className="text-sm font-bold text-text-primary font-display">{candidate.full_name}</h3>
              <p className="text-[11px] text-text-secondary">
                {candidate.current_title ? `${candidate.current_title} at ${candidate.current_company || 'Independent'}` : 'Candidate Profile'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {activeTab === 'profile' && (
              !isEditing ? (
                <button
                  onClick={() => setIsEditing(true)}
                  className="px-3 py-1.5 rounded-lg bg-surface-2 hover:bg-surface-3 text-text-secondary hover:text-text-primary text-xs font-medium flex items-center gap-1.5 transition"
                >
                  <Edit3 className="w-3.5 h-3.5" />
                  <span>Edit Profile</span>
                </button>
              ) : (
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="px-3 py-1.5 rounded-lg bg-brand-cyan text-canvas text-xs font-bold flex items-center gap-1.5 transition disabled:opacity-50 shadow-md shadow-brand-cyan/20"
                >
                  {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                  <span>Save</span>
                </button>
              )
            )}
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-2 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Tab Switcher */}
        <div className="px-6 border-b border-surface-2 bg-surface-1 flex gap-4 shrink-0">
          <button
            onClick={() => setActiveTab('profile')}
            className={`py-3 text-xs font-semibold border-b-2 flex items-center gap-2 transition ${
              activeTab === 'profile'
                ? 'border-brand-cyan text-brand-cyan'
                : 'border-transparent text-text-muted hover:text-text-secondary'
            }`}
          >
            <User className="w-3.5 h-3.5" />
            <span>Profile & Resumes</span>
          </button>

          <button
            onClick={() => setActiveTab('evaluation')}
            className={`py-3 text-xs font-semibold border-b-2 flex items-center gap-2 transition ${
              activeTab === 'evaluation'
                ? 'border-status-success text-status-success'
                : 'border-transparent text-text-muted hover:text-text-secondary'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Evaluation & Decision Gate</span>
            {evaluation && (
              <span className="w-2 h-2 rounded-full bg-status-success animate-pulse" />
            )}
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 flex flex-col gap-6 overflow-y-auto flex-1">
          {error && (
            <div className="p-3 rounded-lg bg-status-danger/10 border border-status-danger/20 text-status-danger text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {decisionSuccess && (
            <div className="p-3 rounded-lg bg-status-success/10 border border-status-success/20 text-status-success text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{decisionSuccess}</span>
            </div>
          )}

          {/* TAB 1: PROFILE & RESUMES */}
          {activeTab === 'profile' && (
            <>
              {parseError && (
                <div className="p-4 rounded-xl bg-status-danger/10 border border-status-danger/30 text-status-danger text-xs flex flex-col gap-2">
                  <div className="flex items-center gap-2 font-bold">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    <span>Parsing Failure</span>
                  </div>
                  <p className="text-text-secondary leading-relaxed">{parseError}</p>
                  <button
                    onClick={() => handleParseResume()}
                    className="self-start mt-1 px-3 py-1 rounded-lg bg-status-danger/20 hover:bg-status-danger/30 text-status-danger font-semibold text-[11px] transition flex items-center gap-1.5"
                  >
                    <Sparkles className="w-3 h-3" /> Retry Parsing
                  </button>
                </div>
              )}

              {/* Basic Profile Details */}
              {isEditing ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 p-4 rounded-xl bg-surface-2/40 border border-surface-2">
                  <div>
                    <label className="text-[11px] font-mono text-text-muted mb-1 block">Full Name *</label>
                    <input
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      className="w-full px-3 py-1.5 rounded-lg bg-surface-1 border border-surface-3 text-xs text-text-primary focus:outline-none focus:border-brand-cyan"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] font-mono text-text-muted mb-1 block">Email Address *</label>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full px-3 py-1.5 rounded-lg bg-surface-1 border border-surface-3 text-xs text-text-primary focus:outline-none focus:border-brand-cyan"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] font-mono text-text-muted mb-1 block">Phone</label>
                    <input
                      type="text"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      className="w-full px-3 py-1.5 rounded-lg bg-surface-1 border border-surface-3 text-xs text-text-primary focus:outline-none focus:border-brand-cyan"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] font-mono text-text-muted mb-1 block">Location</label>
                    <input
                      type="text"
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                      className="w-full px-3 py-1.5 rounded-lg bg-surface-1 border border-surface-3 text-xs text-text-primary focus:outline-none focus:border-brand-cyan"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] font-mono text-text-muted mb-1 block">Current Title</label>
                    <input
                      type="text"
                      value={currentTitle}
                      onChange={(e) => setCurrentTitle(e.target.value)}
                      className="w-full px-3 py-1.5 rounded-lg bg-surface-1 border border-surface-3 text-xs text-text-primary focus:outline-none focus:border-brand-cyan"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] font-mono text-text-muted mb-1 block">Current Company</label>
                    <input
                      type="text"
                      value={currentCompany}
                      onChange={(e) => setCurrentCompany(e.target.value)}
                      className="w-full px-3 py-1.5 rounded-lg bg-surface-1 border border-surface-3 text-xs text-text-primary focus:outline-none focus:border-brand-cyan"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] font-mono text-text-muted mb-1 block">Years of Experience</label>
                    <input
                      type="number"
                      step="0.5"
                      value={yearsOfExperience}
                      onChange={(e) => setYearsOfExperience(e.target.value)}
                      className="w-full px-3 py-1.5 rounded-lg bg-surface-1 border border-surface-3 text-xs text-text-primary focus:outline-none focus:border-brand-cyan"
                    />
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-xl bg-surface-2/20 border border-surface-2">
                  <div className="flex items-center gap-2.5">
                    <Mail className="w-4 h-4 text-text-muted shrink-0" />
                    <div className="truncate">
                      <span className="text-[10px] text-text-muted block">Email</span>
                      <span className="text-xs font-mono text-text-primary truncate">{candidate.email}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <Phone className="w-4 h-4 text-text-muted shrink-0" />
                    <div>
                      <span className="text-[10px] text-text-muted block">Phone</span>
                      <span className="text-xs font-mono text-text-primary">{candidate.phone || 'N/A'}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <MapPin className="w-4 h-4 text-text-muted shrink-0" />
                    <div>
                      <span className="text-[10px] text-text-muted block">Location</span>
                      <span className="text-xs text-text-primary">{candidate.location || 'Remote / Unset'}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <Briefcase className="w-4 h-4 text-brand-cyan shrink-0" />
                    <div>
                      <span className="text-[10px] text-text-muted block">Experience</span>
                      <span className="text-xs font-bold text-text-primary">{candidate.years_of_experience || 0} Years</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Uploaded Documents & Parsing CTA */}
              <div className="flex flex-col gap-2.5">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-semibold text-text-primary flex items-center gap-2">
                    <FileText className="w-4 h-4 text-brand-cyan" />
                    <span>Uploaded Resume & Documents</span>
                  </h4>
                  {activeResume && (
                    <button
                      onClick={() => handleParseResume(activeResume.id)}
                      disabled={isParsing}
                      className="px-3 py-1 rounded-lg bg-brand-cyan/15 hover:bg-brand-cyan/25 text-brand-cyan border border-brand-cyan/30 text-xs font-medium flex items-center gap-1.5 transition disabled:opacity-50"
                    >
                      {isParsing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                      <span>
                        {activeResume.parsing_status === 'completed' 
                          ? 'Re-extract Intelligence' 
                          : 'Parse with AI'}
                      </span>
                    </button>
                  )}
                </div>

                {candidate.resumes && candidate.resumes.length > 0 ? (
                  <div className="flex flex-col gap-2">
                    {candidate.resumes.map((r) => (
                      <div
                        key={r.id}
                        className="p-3.5 rounded-xl bg-surface-2/50 border border-surface-2 flex items-center justify-between text-xs font-mono"
                      >
                        <div className="flex items-center gap-3">
                          <FileText className="w-5 h-5 text-brand-cyan shrink-0" />
                          <div>
                            <span className="text-text-primary font-medium block truncate max-w-[280px]">{r.file_name}</span>
                            <span className="text-[10px] text-text-muted">
                              {(r.file_size_bytes / 1024).toFixed(1)} KB • {r.file_type}
                            </span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span
                            className={`px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                              r.parsing_status === 'completed'
                                ? 'bg-status-success/15 border border-status-success/30 text-status-success'
                                : r.parsing_status === 'failed'
                                ? 'bg-status-danger/15 border border-status-danger/30 text-status-danger'
                                : 'bg-surface-3 text-text-muted border border-surface-3'
                            }`}
                          >
                            {r.parsing_status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-text-muted italic bg-surface-2/20 p-3 rounded-lg border border-dashed border-surface-3">
                    No resume document uploaded yet.
                  </p>
                )}
              </div>

              {/* Extracted Intelligence */}
              {parsedProfile && (parsedProfile.candidate_summary || parsedProfile.work_experience?.length > 0 || parsedProfile.skills?.length > 0) && (
                <div className="flex flex-col gap-4 p-4 rounded-xl bg-surface-2/30 border border-surface-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-brand-cyan" />
                      <h4 className="text-xs font-bold uppercase tracking-wider text-text-primary font-display">
                        Extracted Document Intelligence
                      </h4>
                    </div>
                    <button
                      onClick={handleFetchMaskedProfile}
                      className="px-2.5 py-1 rounded bg-surface-2 hover:bg-surface-3 border border-surface-3 text-[11px] font-mono text-text-secondary flex items-center gap-1.5 transition"
                    >
                      {showMaskedProfile ? <EyeOff className="w-3 h-3 text-status-warning" /> : <Eye className="w-3 h-3 text-brand-cyan" />}
                      <span>{showMaskedProfile ? 'Show Original' : 'Preview Bias-Masked'}</span>
                    </button>
                  </div>

                  {parsedProfile.candidate_summary && (
                    <div className="p-3 rounded-lg bg-surface-1 border border-surface-2 text-xs">
                      <span className="text-[10px] font-bold text-text-muted uppercase block mb-1">Professional Summary</span>
                      <p className="text-text-secondary leading-relaxed">
                        {showMaskedProfile && maskedProfile?.candidate_summary
                          ? maskedProfile.candidate_summary
                          : parsedProfile.candidate_summary}
                      </p>
                    </div>
                  )}

                  {parsedProfile.work_experience && parsedProfile.work_experience.length > 0 && (
                    <div className="flex flex-col gap-2">
                      <span className="text-[10px] font-bold text-text-muted uppercase">Career Highlights</span>
                      <div className="flex flex-col gap-2">
                        {parsedProfile.work_experience.map((exp, idx) => (
                          <div key={idx} className="p-3 rounded-lg bg-surface-1 border border-surface-2 text-xs flex flex-col gap-1">
                            <div className="flex items-center justify-between">
                              <span className="font-bold text-text-primary">{exp.title}</span>
                              <span className="text-[10px] font-mono text-text-muted">{exp.company}</span>
                            </div>
                            {exp.highlights && exp.highlights.length > 0 && (
                              <ul className="list-disc list-inside text-text-secondary text-[11px] space-y-0.5 mt-1">
                                {exp.highlights.slice(0, 3).map((h, hIdx) => (
                                  <li key={hIdx}>{h}</li>
                                ))}
                              </ul>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Grounded Evidence */}
              <div className="flex flex-col gap-2.5">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-semibold text-text-primary flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-brand-cyan" />
                    <span>Grounded Evidence & Provenance</span>
                  </h4>
                  <span className="text-[10px] font-mono text-text-muted">
                    {evidenceList.length} verified quotes
                  </span>
                </div>

                {loadingEvidence ? (
                  <div className="p-4 rounded-xl bg-surface-2/20 text-center text-xs text-text-muted font-mono flex items-center justify-center gap-2">
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-brand-cyan" />
                    <span>Retrieving provenance records...</span>
                  </div>
                ) : evidenceList.length > 0 ? (
                  <div className="flex flex-col gap-2 max-h-56 overflow-y-auto pr-1">
                    {evidenceList.map((ev) => (
                      <div
                        key={ev.id}
                        className="p-3 rounded-xl bg-surface-1 border border-surface-2 text-xs flex flex-col gap-1.5"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 rounded bg-brand-cyan/10 border border-brand-cyan/20 text-brand-cyan font-mono text-[10px] font-bold uppercase">
                              {ev.claim_type}: {ev.claim_text}
                            </span>
                            <span className="text-[10px] font-mono text-text-muted">Source: {ev.source_type}</span>
                          </div>
                          <span className="px-1.5 py-0.5 rounded bg-status-success/10 text-status-success font-mono text-[10px] font-bold">
                            {(ev.confidence_score * 100).toFixed(0)}% confidence
                          </span>
                        </div>
                        <div className="p-2 rounded bg-surface-2/50 border border-surface-2 text-[11px] text-text-secondary italic flex items-start gap-1.5">
                          <Quote className="w-3 h-3 text-brand-cyan/60 shrink-0 mt-0.5" />
                          <span>"{ev.verbatim_source_text}"</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-text-muted italic bg-surface-2/20 p-3 rounded-lg border border-dashed border-surface-3">
                    No grounded evidence recorded yet.
                  </p>
                )}
              </div>
            </>
          )}

          {/* TAB 2: EVALUATION & HUMAN DECISION GATE */}
          {activeTab === 'evaluation' && (
            <div className="flex flex-col gap-6">
              {loadingEvaluation ? (
                <div className="p-16 flex flex-col items-center justify-center text-text-muted gap-3">
                  <Loader2 className="w-8 h-8 animate-spin text-status-success" />
                  <span className="text-xs font-mono">Loading evaluation report...</span>
                </div>
              ) : evaluation ? (
                <>
                  {/* Evaluation Score Highlights */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-4 rounded-xl bg-surface-2/50 border border-surface-2 flex flex-col items-center justify-center text-center">
                      <span className="text-[10px] font-mono text-text-muted uppercase">Overall Score</span>
                      <span className="text-2xl font-bold font-display text-brand-cyan">
                        {evaluation.overall_interview_score?.toFixed(1)}%
                      </span>
                    </div>

                    <div className="p-4 rounded-xl bg-surface-2/50 border border-surface-2 flex flex-col items-center justify-center text-center">
                      <span className="text-[10px] font-mono text-text-muted uppercase">Technical Depth</span>
                      <span className="text-2xl font-bold font-display text-brand-indigo">
                        {evaluation.technical_score?.toFixed(1)}%
                      </span>
                    </div>

                    <div className="p-4 rounded-xl bg-surface-2/50 border border-surface-2 flex flex-col items-center justify-center text-center">
                      <span className="text-[10px] font-mono text-text-muted uppercase">Communication</span>
                      <span className="text-2xl font-bold font-display text-status-success">
                        {evaluation.communication_score?.toFixed(1)}%
                      </span>
                    </div>

                    <div className="p-4 rounded-xl bg-surface-2/50 border border-surface-2 flex flex-col items-center justify-center text-center">
                      <span className="text-[10px] font-mono text-text-muted uppercase">AI Recommendation</span>
                      <span className={`text-sm font-bold font-mono uppercase px-2.5 py-1 rounded-full mt-1 ${
                        evaluation.ai_recommendation === 'advance'
                          ? 'bg-status-success/20 text-status-success border border-status-success/40'
                          : evaluation.ai_recommendation === 'hold'
                          ? 'bg-status-warning/20 text-status-warning border border-status-warning/40'
                          : 'bg-status-danger/20 text-status-danger border border-status-danger/40'
                      }`}>
                        {evaluation.ai_recommendation || 'PENDING'}
                      </span>
                    </div>
                  </div>

                  {/* Category Breakdown Bars */}
                  {evaluation.category_scores && Object.keys(evaluation.category_scores).length > 0 && (
                    <div className="p-4 rounded-xl bg-surface-2/30 border border-surface-2 flex flex-col gap-3">
                      <span className="text-xs font-bold text-text-primary uppercase font-mono">
                        Category Competency Breakdown
                      </span>
                      <div className="flex flex-col gap-2.5">
                        {Object.entries(evaluation.category_scores).map(([category, score]) => (
                          <div key={category} className="flex flex-col gap-1">
                            <div className="flex justify-between text-xs font-mono">
                              <span className="text-text-secondary capitalize">{category.replace('_', ' ')}</span>
                              <span className="text-brand-cyan font-bold">{Number(score).toFixed(0)}%</span>
                            </div>
                            <div className="w-full h-1.5 bg-surface-3 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-gradient-to-r from-brand-cyan to-brand-indigo rounded-full"
                                style={{ width: `${Math.min(100, Math.max(0, Number(score)))}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Executive Summary */}
                  {evaluation.executive_summary && (
                    <div className="p-4 rounded-xl bg-surface-2/40 border border-surface-2 text-xs flex flex-col gap-1.5">
                      <span className="text-[10px] font-bold text-text-muted uppercase">AI Executive Summary</span>
                      <p className="text-text-secondary leading-relaxed">{evaluation.executive_summary}</p>
                    </div>
                  )}

                  {/* Strengths & Weaknesses */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl bg-status-success/5 border border-status-success/20 flex flex-col gap-2">
                      <span className="text-xs font-bold text-status-success flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Identified Strengths</span>
                      </span>
                      <ul className="list-disc list-inside text-xs text-text-secondary space-y-1">
                        {evaluation.strengths && evaluation.strengths.length > 0 ? (
                          evaluation.strengths.map((s, idx) => <li key={idx}>{s}</li>)
                        ) : (
                          <li className="italic text-text-muted">No explicit strengths listed.</li>
                        )}
                      </ul>
                    </div>

                    <div className="p-4 rounded-xl bg-status-warning/5 border border-status-warning/20 flex flex-col gap-2">
                      <span className="text-xs font-bold text-status-warning flex items-center gap-1.5">
                        <AlertCircle className="w-4 h-4" />
                        <span>Areas for Growth / Gap Probes</span>
                      </span>
                      <ul className="list-disc list-inside text-xs text-text-secondary space-y-1">
                        {evaluation.weaknesses && evaluation.weaknesses.length > 0 ? (
                          evaluation.weaknesses.map((w, idx) => <li key={idx}>{w}</li>)
                        ) : (
                          <li className="italic text-text-muted">No major weaknesses identified.</li>
                        )}
                      </ul>
                    </div>
                  </div>

                  {/* HUMAN DECISION GATE */}
                  <div className="p-5 rounded-2xl bg-gradient-to-br from-surface-1 to-surface-2/70 border border-brand-cyan/30 flex flex-col gap-4 shadow-xl">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <Lock className="w-4 h-4 text-brand-cyan" />
                        <h4 className="text-sm font-bold text-text-primary font-display">
                          Recruiter Human Decision Gate
                        </h4>
                      </div>
                      <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-brand-cyan/15 text-brand-cyan border border-brand-cyan/30 font-bold uppercase">
                        Human-in-the-Loop Required
                      </span>
                    </div>

                    <p className="text-xs text-text-muted leading-relaxed">
                      AI evaluation is strictly decision support. Recruiter sign-off is mandatory before any pipeline progression.
                    </p>

                    {/* Decision Selection */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                      {[
                        { id: 'advance', label: 'Advance', color: 'border-status-success text-status-success bg-status-success/10' },
                        { id: 'hold', label: 'Hold', color: 'border-status-warning text-status-warning bg-status-warning/10' },
                        { id: 'offer', label: 'Extend Offer', color: 'border-brand-cyan text-brand-cyan bg-brand-cyan/10' },
                        { id: 'reject', label: 'Reject', color: 'border-status-danger text-status-danger bg-status-danger/10' },
                      ].map((action) => (
                        <button
                          key={action.id}
                          type="button"
                          onClick={() => setDecisionAction(action.id)}
                          className={`p-2.5 rounded-xl border text-xs font-bold transition flex items-center justify-center gap-1.5 ${
                            decisionAction === action.id
                              ? `${action.color} ring-2 ring-brand-cyan/30 shadow-md`
                              : 'bg-surface-2/60 border-surface-3 text-text-secondary hover:text-text-primary'
                          }`}
                        >
                          <Check className={`w-3.5 h-3.5 ${decisionAction === action.id ? 'opacity-100' : 'opacity-0'}`} />
                          <span>{action.label}</span>
                        </button>
                      ))}
                    </div>

                    {/* Recruiter Notes */}
                    <div>
                      <label className="text-[11px] font-mono text-text-muted block mb-1">
                        Recruiter Rationale & Governance Notes:
                      </label>
                      <textarea
                        rows={2}
                        value={decisionNotes}
                        onChange={(e) => setDecisionNotes(e.target.value)}
                        placeholder="State reason for hiring decision, interview performance commentary, or follow-up requirements..."
                        className="w-full p-2.5 rounded-xl bg-surface-1 border border-surface-3 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-cyan transition"
                      />
                    </div>

                    <div className="flex items-center justify-between pt-1">
                      {evaluation.human_decision ? (
                        <span className="text-[11px] font-mono text-text-muted">
                          Last decision: <span className="font-bold uppercase text-brand-cyan">{evaluation.human_decision}</span>
                          {evaluation.human_decision_at && ` at ${new Date(evaluation.human_decision_at).toLocaleTimeString()}`}
                        </span>
                      ) : (
                        <span className="text-[11px] font-mono text-text-muted italic">
                          Awaiting recruiter authorization.
                        </span>
                      )}

                      <button
                        onClick={handleSubmitHumanDecision}
                        disabled={submittingDecision}
                        className="px-4 py-2 rounded-xl bg-status-success hover:bg-status-success/90 text-canvas text-xs font-bold flex items-center gap-2 transition disabled:opacity-50 shadow-lg shadow-status-success/20 cursor-pointer"
                      >
                        {submittingDecision ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                        <span>Submit Human Decision</span>
                      </button>
                    </div>
                  </div>
                </>
              ) : (
                <div className="p-12 rounded-2xl bg-surface-2/20 border border-dashed border-surface-2 flex flex-col items-center justify-center text-center gap-3">
                  <div className="w-12 h-12 rounded-2xl bg-surface-2 flex items-center justify-center text-text-muted">
                    <MessageSquare className="w-6 h-6" />
                  </div>
                  <h4 className="text-sm font-bold text-text-primary">No Completed Interview Found</h4>
                  <p className="text-xs text-text-muted max-w-sm">
                    Conduct an AI-assisted screening interview for this candidate from the Job Requisition dashboard to generate competency rubrics and evaluation summaries.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
