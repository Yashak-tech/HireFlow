import React, { useEffect, useState } from 'react';
import { 
  Sparkles, 
  Briefcase, 
  Users, 
  ShieldCheck, 
  UserCheck, 
  Building2, 
  LogOut, 
  AlertCircle,
  CheckCircle2,
  Plus,
  UploadCloud,
  MessageSquare,
  Database,
  Loader2,
  Layers
} from 'lucide-react';

import JobsView from './components/JobsView';
import JobDetailView from './components/JobDetailView';
import CandidatesView from './components/CandidatesView';
import CreateJobModal from './components/CreateJobModal';
import CreateCandidateModal from './components/CreateCandidateModal';
import UploadResumeModal from './components/UploadResumeModal';
import CandidateDetailModal from './components/CandidateDetailModal';
import InterviewWorkspace from './components/InterviewWorkspace';
import InterviewListView from './components/InterviewListView';
import AuditDashboard from './components/AuditDashboard';
import { apiUrl } from './api';

export default function App() {
  const [health, setHealth] = useState(null);
  const [loadingHealth, setLoadingHealth] = useState(true);

  // Auth state
  const [authData, setAuthData] = useState(null);
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState(null);

  // Navigation state: 'jobs' | 'candidates' | 'interviews' | 'audit'
  const [currentTab, setCurrentTab] = useState('jobs');
  const [selectedJobId, setSelectedJobId] = useState(null);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [activeInterviewId, setActiveInterviewId] = useState(null);

  // Modals state
  const [isCreateJobOpen, setIsCreateJobOpen] = useState(false);
  const [isCreateCandidateOpen, setIsCreateCandidateOpen] = useState(false);
  const [isUploadResumeOpen, setIsUploadResumeOpen] = useState(false);
  const [uploadTargetJobId, setUploadTargetJobId] = useState(null);

  // Data state
  const [jobs, setJobs] = useState([]);
  const [loadingJobs, setLoadingJobs] = useState(false);
  const [candidates, setCandidates] = useState([]);
  const [loadingCandidates, setLoadingCandidates] = useState(false);

  // Demo seed state
  const [seedingDemo, setSeedingDemo] = useState(false);

  // Toast feedback
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  useEffect(() => {
    // Health probe
    fetch(apiUrl('/api/health'))
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        setHealth(data);
        setLoadingHealth(false);
      })
      .catch(() => setLoadingHealth(false));

    // Restore saved token
    const savedToken = localStorage.getItem('hireflow_token');
    if (savedToken) {
      fetch(apiUrl('/api/auth/me'), {
        headers: { Authorization: `Bearer ${savedToken}` },
      })
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (data) {
            setAuthData({
              access_token: savedToken,
              user: data.user,
              organization: data.organization,
            });
          } else {
            localStorage.removeItem('hireflow_token');
          }
        })
        .catch(() => localStorage.removeItem('hireflow_token'));
    }
  }, []);

  // Fetch jobs & candidates when authenticated
  const fetchJobs = async () => {
    if (!authData?.access_token) return;
    setLoadingJobs(true);
    try {
      const res = await fetch(apiUrl('/api/jobs'), {
        headers: { Authorization: `Bearer ${authData.access_token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setJobs(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingJobs(false);
    }
  };

  const fetchCandidates = async () => {
    if (!authData?.access_token) return;
    setLoadingCandidates(true);
    try {
      const res = await fetch(apiUrl('/api/candidates'), {
        headers: { Authorization: `Bearer ${authData.access_token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setCandidates(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingCandidates(false);
    }
  };

  useEffect(() => {
    if (authData?.access_token) {
      fetchJobs();
      fetchCandidates();
    }
  }, [authData]);

  const handleDemoLogin = async (persona) => {
    setAuthLoading(true);
    setAuthError(null);

    try {
      const res = await fetch(apiUrl('/api/auth/demo-login'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ persona }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Login failed');
      }

      const data = await res.json();
      setAuthData(data);
      localStorage.setItem('hireflow_token', data.access_token);
      showToast(`Signed in as ${data.user.full_name} (${data.user.role})`);
    } catch (err) {
      setAuthError(err.message);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    setAuthData(null);
    setJobs([]);
    setCandidates([]);
    setSelectedJobId(null);
    setSelectedCandidate(null);
    setActiveInterviewId(null);
    localStorage.removeItem('hireflow_token');
    showToast('Logged out successfully', 'info');
  };

  const handleSeedDemoData = async () => {
    if (!authData?.access_token) return;
    setSeedingDemo(true);
    try {
      const res = await fetch(apiUrl('/api/demo/seed'), {
        method: 'POST',
        headers: { Authorization: `Bearer ${authData.access_token}` },
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to seed demo data.');
      }

      const data = await res.json();
      showToast('Demo data seeded! 1 Role, 3 Candidates, Interview & Evaluation loaded.');
      await fetchJobs();
      await fetchCandidates();
    } catch (err) {
      showToast(err.message, 'danger');
    } finally {
      setSeedingDemo(false);
    }
  };

  const handleStartInterview = (interviewId) => {
    setActiveInterviewId(interviewId);
    setCurrentTab('interviews');
  };

  const handleJobCreated = (newJob) => {
    setJobs([newJob, ...jobs]);
    showToast(`Job requisition '${newJob.title}' created!`);
  };

  const handleCandidateCreated = (newCandidate) => {
    setCandidates([newCandidate, ...candidates]);
    showToast(`Candidate profile '${newCandidate.full_name}' added!`);
  };

  const handleResumeUploaded = (updatedCandidate) => {
    setCandidates((prev) => {
      const exists = prev.some((c) => c.id === updatedCandidate.id);
      if (exists) {
        return prev.map((c) => (c.id === updatedCandidate.id ? updatedCandidate : c));
      }
      return [updatedCandidate, ...prev];
    });
    fetchJobs();
    showToast(`Resume uploaded for ${updatedCandidate.full_name}!`);
  };

  const handleCandidateUpdated = (updatedCandidate) => {
    setSelectedCandidate(updatedCandidate);
    setCandidates((prev) =>
      prev.map((c) => (c.id === updatedCandidate.id ? updatedCandidate : c))
    );
    showToast(`Candidate '${updatedCandidate.full_name}' updated!`);
  };

  const openUploadModal = (jobId = null) => {
    setUploadTargetJobId(jobId);
    setIsUploadResumeOpen(true);
  };

  return (
    <div className="min-h-screen bg-canvas text-text-primary flex flex-col font-sans selection:bg-brand-cyan/20 selection:text-brand-cyan">
      {/* Toast Notification */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 animate-bounce">
          <div className={`px-4 py-2.5 rounded-xl border text-xs font-semibold shadow-2xl flex items-center gap-2 ${
            toast.type === 'danger'
              ? 'bg-status-danger/20 border-status-danger/40 text-status-danger backdrop-blur-md'
              : toast.type === 'info'
              ? 'bg-brand-indigo/20 border-brand-indigo/40 text-brand-indigo backdrop-blur-md'
              : 'bg-status-success/20 border-status-success/40 text-status-success backdrop-blur-md'
          }`}>
            <CheckCircle2 className="w-4 h-4" />
            <span>{toast.message}</span>
          </div>
        </div>
      )}

      {/* Top Navbar */}
      <header className="border-b border-surface-2/80 bg-surface-1/60 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div 
              onClick={() => { setSelectedJobId(null); setCurrentTab('jobs'); }}
              className="flex items-center gap-2.5 cursor-pointer"
            >
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-brand-cyan via-brand-blue to-brand-indigo flex items-center justify-center shadow-lg shadow-brand-cyan/20">
                <Sparkles className="w-4 h-4 text-canvas" />
              </div>
              <span className="font-display font-bold text-lg tracking-tight text-text-primary">
                Hire<span className="text-brand-cyan">Flow</span>
              </span>
            </div>

            <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-surface-2 text-brand-cyan border border-brand-cyan/20 font-bold uppercase tracking-wider">
              Phase 7 Ready
            </span>

            {/* Navigation Tabs (when logged in) */}
            {authData && (
              <nav className="hidden md:flex items-center gap-1 ml-4 pl-4 border-l border-surface-2 text-xs">
                <button
                  onClick={() => { setSelectedJobId(null); setCurrentTab('jobs'); }}
                  className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition ${
                    currentTab === 'jobs'
                      ? 'bg-surface-2 text-brand-cyan font-bold border border-surface-3'
                      : 'text-text-muted hover:text-text-primary hover:bg-surface-2/50'
                  }`}
                >
                  <Briefcase className="w-3.5 h-3.5" />
                  <span>Job Requisitions</span>
                </button>

                <button
                  onClick={() => { setSelectedJobId(null); setCurrentTab('candidates'); }}
                  className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition ${
                    currentTab === 'candidates'
                      ? 'bg-surface-2 text-brand-indigo font-bold border border-surface-3'
                      : 'text-text-muted hover:text-text-primary hover:bg-surface-2/50'
                  }`}
                >
                  <Users className="w-3.5 h-3.5" />
                  <span>Candidates</span>
                </button>

                <button
                  onClick={() => { setSelectedJobId(null); setActiveInterviewId(null); setCurrentTab('interviews'); }}
                  className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition ${
                    currentTab === 'interviews'
                      ? 'bg-surface-2 text-status-success font-bold border border-surface-3'
                      : 'text-text-muted hover:text-text-primary hover:bg-surface-2/50'
                  }`}
                >
                  <MessageSquare className="w-3.5 h-3.5" />
                  <span>Interviews</span>
                </button>

                <button
                  onClick={() => { setSelectedJobId(null); setActiveInterviewId(null); setCurrentTab('audit'); }}
                  className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition ${
                    currentTab === 'audit'
                      ? 'bg-surface-2 text-brand-cyan font-bold border border-surface-3'
                      : 'text-text-muted hover:text-text-primary hover:bg-surface-2/50'
                  }`}
                >
                  <ShieldCheck className="w-3.5 h-3.5" />
                  <span>Audit Trail</span>
                </button>
              </nav>
            )}
          </div>

          {/* Right Header: Seed Data Button + Health + User Profile */}
          <div className="flex items-center gap-3">
            {authData && (
              <button
                onClick={handleSeedDemoData}
                disabled={seedingDemo}
                className="hidden sm:flex px-3 py-1 rounded-lg bg-surface-2 hover:bg-surface-3 border border-brand-cyan/30 text-xs font-mono text-brand-cyan items-center gap-1.5 transition disabled:opacity-50"
                title="Seed realistic demo jobs, candidates, and evaluations"
              >
                {seedingDemo ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Database className="w-3.5 h-3.5" />}
                <span>Seed Demo Data</span>
              </button>
            )}

            <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-lg bg-surface-1 border border-surface-2 text-[11px] font-mono text-text-secondary">
              <div className={`w-2 h-2 rounded-full ${health ? 'bg-status-success animate-pulse' : 'bg-status-warning'}`} />
              API: {loadingHealth ? '...' : health ? 'Ready' : 'Offline'}
            </div>

            {authData ? (
              <div className="flex items-center gap-3 pl-2 border-l border-surface-2">
                <div className="text-right">
                  <div className="text-xs font-semibold text-text-primary">{authData.user.full_name}</div>
                  <div className="text-[10px] font-mono text-brand-cyan capitalize">{authData.user.role}</div>
                </div>
                <button
                  onClick={handleLogout}
                  className="p-1.5 rounded-lg hover:bg-surface-2 text-text-muted hover:text-status-danger transition"
                  title="Log out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <span className="text-xs text-text-muted font-mono">Demo Mode</span>
            )}
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 flex flex-col gap-8">
        {!authData ? (
          /* Sign-in / Persona Switcher View when unauthenticated */
          <div className="max-w-xl mx-auto w-full my-auto flex flex-col gap-6">
            <div className="p-8 rounded-2xl bg-surface-1 border border-surface-2 shadow-2xl flex flex-col gap-6 text-center">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-brand-cyan via-brand-blue to-brand-indigo flex items-center justify-center mx-auto shadow-lg shadow-brand-cyan/20">
                <Sparkles className="w-6 h-6 text-canvas" />
              </div>
              <div>
                <h1 className="text-xl font-bold font-display text-text-primary">Sign In to HireFlow</h1>
                <p className="text-xs text-text-secondary mt-1">
                  Select an authenticated demo persona to experience role-based recruitment workflows.
                </p>
              </div>

              {authError && (
                <div className="p-3 rounded-lg bg-status-danger/10 border border-status-danger/20 text-status-danger text-xs flex items-center gap-2 text-left">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{authError}</span>
                </div>
              )}

              <div className="flex flex-col gap-3">
                <button
                  onClick={() => handleDemoLogin('sarah_jenkins')}
                  disabled={authLoading}
                  className="p-4 rounded-xl border border-surface-3 bg-surface-2/60 hover:border-brand-cyan/60 hover:bg-surface-2 text-left flex items-center justify-between transition group cursor-pointer"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-text-primary group-hover:text-brand-cyan transition">
                        Sarah Jenkins
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-brand-cyan/15 text-brand-cyan">
                        Recruiter
                      </span>
                    </div>
                    <div className="text-[11px] text-text-muted mt-0.5">Senior Technical Recruiter • Acme Technologies</div>
                  </div>
                  <UserCheck className="w-5 h-5 text-text-muted group-hover:text-brand-cyan transition" />
                </button>

                <button
                  onClick={() => handleDemoLogin('marcus_vance')}
                  disabled={authLoading}
                  className="p-4 rounded-xl border border-surface-3 bg-surface-2/60 hover:border-brand-indigo/60 hover:bg-surface-2 text-left flex items-center justify-between transition group cursor-pointer"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-text-primary group-hover:text-brand-indigo transition">
                        Marcus Vance
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-brand-indigo/15 text-brand-indigo">
                        Hiring Manager
                      </span>
                    </div>
                    <div className="text-[11px] text-text-muted mt-0.5">Director of Engineering • Acme Technologies</div>
                  </div>
                  <UserCheck className="w-5 h-5 text-text-muted group-hover:text-brand-indigo transition" />
                </button>
              </div>
            </div>
          </div>
        ) : (
          /* Authenticated Dashboard View */
          <>
            {/* View Switcher based on currentTab & selectedJobId */}
            {currentTab === 'jobs' && (
              selectedJobId ? (
                <JobDetailView
                  jobId={selectedJobId}
                  onBack={() => setSelectedJobId(null)}
                  token={authData.access_token}
                  onOpenUpload={openUploadModal}
                  onSelectCandidate={(cand) => setSelectedCandidate(cand)}
                  onStartInterview={handleStartInterview}
                />
              ) : (
                <JobsView
                  jobs={jobs}
                  loading={loadingJobs}
                  onSelectJob={(id) => setSelectedJobId(id)}
                  onOpenCreateJob={() => setIsCreateJobOpen(true)}
                  token={authData.access_token}
                />
              )
            )}

            {currentTab === 'interviews' && (
              activeInterviewId ? (
                <InterviewWorkspace
                  interviewId={activeInterviewId}
                  onBack={() => setActiveInterviewId(null)}
                  token={authData.access_token}
                />
              ) : (
                <InterviewListView
                  token={authData.access_token}
                  onSelectInterview={(id) => setActiveInterviewId(id)}
                />
              )
            )}

            {currentTab === 'candidates' && (
              <CandidatesView
                candidates={candidates}
                loading={loadingCandidates}
                onSelectCandidate={(cand) => setSelectedCandidate(cand)}
                onOpenCreateCandidate={() => setIsCreateCandidateOpen(true)}
                onOpenUpload={openUploadModal}
              />
            )}

            {currentTab === 'audit' && (
              <AuditDashboard token={authData.access_token} />
            )}
          </>
        )}
      </main>

      {/* Modals */}
      <CreateJobModal
        isOpen={isCreateJobOpen}
        onClose={() => setIsCreateJobOpen(false)}
        onJobCreated={handleJobCreated}
        token={authData?.access_token}
      />

      <CreateCandidateModal
        isOpen={isCreateCandidateOpen}
        onClose={() => setIsCreateCandidateOpen(false)}
        onCandidateCreated={handleCandidateCreated}
        jobs={jobs}
        defaultJobId={selectedJobId}
        token={authData?.access_token}
      />

      <UploadResumeModal
        isOpen={isUploadResumeOpen}
        onClose={() => setIsUploadResumeOpen(false)}
        onUploaded={handleResumeUploaded}
        jobs={jobs}
        defaultJobId={uploadTargetJobId || selectedJobId}
        token={authData?.access_token}
      />

      <CandidateDetailModal
        isOpen={!!selectedCandidate}
        onClose={() => setSelectedCandidate(null)}
        candidate={selectedCandidate}
        onCandidateUpdated={handleCandidateUpdated}
        token={authData?.access_token}
      />

      {/* Footer */}
      <footer className="border-t border-surface-2/80 py-6 text-center text-xs text-text-muted font-mono">
        HireFlow v1.0.0 — Intelligent, Auditable AI Recruitment Copilot — Phase 7 Final Hardened
      </footer>
    </div>
  );
}
