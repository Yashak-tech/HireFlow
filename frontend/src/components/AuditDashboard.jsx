import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Search,
  Filter,
  RefreshCw,
  Clock,
  User,
  Database,
  CheckCircle2,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Download,
  Loader2,
  FileCode,
  Tag
} from 'lucide-react';
import { apiUrl } from '../api';

const ACTION_COLORS = {
  job_created: 'bg-brand-cyan/15 text-brand-cyan border-brand-cyan/30',
  job_updated: 'bg-brand-cyan/10 text-brand-cyan border-brand-cyan/20',
  candidate_created: 'bg-brand-indigo/15 text-brand-indigo border-brand-indigo/30',
  candidate_updated: 'bg-brand-indigo/10 text-brand-indigo border-brand-indigo/20',
  resume_parsed: 'bg-brand-blue/15 text-brand-blue border-brand-blue/30',
  match_analysis_completed: 'bg-brand-purple/15 text-brand-purple border-brand-purple/30',
  interview_prepared: 'bg-brand-yellow/15 text-status-warning border-brand-yellow/30',
  interview_turn_processed: 'bg-surface-3 text-text-secondary border-surface-3',
  interview_finalized: 'bg-status-success/15 text-status-success border-status-success/30',
  evaluation_generated: 'bg-brand-cyan/20 text-brand-cyan border-brand-cyan/40',
  recruiter_decision: 'bg-status-success/20 text-status-success border-status-success/40',
  tamper_flag_raised: 'bg-status-danger/20 text-status-danger border-status-danger/40 animate-pulse',
};

const ACTION_LABELS = {
  job_created: 'Job Created',
  job_updated: 'Job Updated',
  candidate_created: 'Candidate Created',
  candidate_updated: 'Candidate Updated',
  resume_parsed: 'Resume Parsed',
  match_analysis_completed: 'Match Analysis',
  interview_prepared: 'Interview Prepared',
  interview_turn_processed: 'Interview Turn',
  interview_finalized: 'Interview Finalized',
  evaluation_generated: 'Evaluation Generated',
  recruiter_decision: 'Human Decision Gate',
  tamper_flag_raised: 'Tamper Flag Alert',
};

export default function AuditDashboard({ token }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [actionFilter, setActionFilter] = useState('all');
  const [entityFilter, setEntityFilter] = useState('all');
  const [expandedLogId, setExpandedLogId] = useState(null);

  const fetchLogs = async (isRefresh = false) => {
    if (!token) return;
    if (isRefresh) setRefreshing(true);
    else setLoading(true);

    try {
      let url = apiUrl('/api/audit?limit=200');
      if (actionFilter !== 'all') url += `&action=${encodeURIComponent(actionFilter)}`;
      if (entityFilter !== 'all') url += `&entity_type=${encodeURIComponent(entityFilter)}`;

      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.ok) {
        const data = await res.json();
        setLogs(data);
      }
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [token, actionFilter, entityFilter]);

  const filteredLogs = logs.filter((log) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    const actionMatch = log.action?.toLowerCase().includes(term);
    const entityMatch = log.entity_type?.toLowerCase().includes(term) || log.entity_id?.toLowerCase().includes(term);
    const userMatch = log.user_id?.toLowerCase().includes(term);
    const detailsMatch = JSON.stringify(log.details || {}).toLowerCase().includes(term);
    return actionMatch || entityMatch || userMatch || detailsMatch;
  });

  const toggleExpand = (id) => {
    setExpandedLogId(expandedLogId === id ? null : id);
  };

  const handleExportJSON = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(filteredLogs, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `hireflow_audit_trail_${new Date().toISOString().slice(0, 10)}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const tamperLogsCount = logs.filter((l) => l.action === 'tamper_flag_raised').length;
  const humanDecisionsCount = logs.filter((l) => l.action === 'recruiter_decision').length;

  return (
    <div className="flex flex-col gap-6 w-full">
      {/* Header & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold font-display text-text-primary tracking-tight flex items-center gap-2.5">
            <ShieldCheck className="w-5 h-5 text-brand-cyan" />
            <span>Audit & Compliance Governance Log</span>
            <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-surface-2 text-text-muted border border-surface-3">
              {logs.length} Total Events
            </span>
          </h2>
          <p className="text-xs text-text-secondary mt-1">
            Immutable, cryptographically verifiable event stream tracking all AI actions, resume extractions, and recruiter decisions.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => fetchLogs(true)}
            disabled={refreshing || loading}
            className="px-3 py-1.5 rounded-xl bg-surface-2 hover:bg-surface-3 border border-surface-3 text-xs font-semibold text-text-secondary hover:text-text-primary flex items-center gap-1.5 transition disabled:opacity-50"
            title="Refresh logs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-brand-cyan' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            onClick={handleExportJSON}
            disabled={filteredLogs.length === 0}
            className="px-3 py-1.5 rounded-xl bg-surface-2 hover:bg-surface-3 border border-surface-3 text-xs font-semibold text-text-secondary hover:text-text-primary flex items-center gap-1.5 transition disabled:opacity-50"
            title="Export to JSON"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Logs</span>
          </button>
        </div>
      </div>

      {/* KPI Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-surface-1 border border-surface-2 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-cyan/10 border border-brand-cyan/20 flex items-center justify-center text-brand-cyan">
            <Database className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-mono text-text-muted uppercase block">Logged Events</span>
            <span className="text-lg font-bold font-display text-text-primary">{logs.length}</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-surface-1 border border-surface-2 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-status-success/10 border border-status-success/20 flex items-center justify-center text-status-success">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-mono text-text-muted uppercase block">Human Gate Decisions</span>
            <span className="text-lg font-bold font-display text-text-primary">{humanDecisionsCount}</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-surface-1 border border-surface-2 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-indigo/10 border border-brand-indigo/20 flex items-center justify-center text-brand-indigo">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-mono text-text-muted uppercase block">RBAC Multi-Tenant Guard</span>
            <span className="text-xs font-bold text-text-primary">Enforced (Org Scoped)</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-surface-1 border border-surface-2 flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
            tamperLogsCount > 0 
              ? 'bg-status-danger/15 text-status-danger border border-status-danger/30' 
              : 'bg-surface-2 text-text-muted'
          }`}>
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-mono text-text-muted uppercase block">Integrity Alerts</span>
            <span className="text-lg font-bold font-display text-text-primary">
              {tamperLogsCount === 0 ? '0 Anomaly' : `${tamperLogsCount} Detected`}
            </span>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-surface-1 border border-surface-2">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by action, entity ID, user ID, or payload content..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 rounded-lg bg-surface-2 border border-surface-3 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-cyan transition"
          />
        </div>

        <div className="flex items-center gap-3">
          {/* Entity Type Filter */}
          <div className="flex items-center gap-1.5">
            <Tag className="w-3.5 h-3.5 text-text-muted" />
            <select
              value={entityFilter}
              onChange={(e) => setEntityFilter(e.target.value)}
              className="px-2.5 py-1 rounded-lg bg-surface-2 border border-surface-3 text-xs text-text-secondary focus:outline-none focus:border-brand-cyan"
            >
              <option value="all">All Entities</option>
              <option value="job">Jobs</option>
              <option value="candidate">Candidates</option>
              <option value="match">Matches</option>
              <option value="interview">Interviews</option>
              <option value="evaluation">Evaluations</option>
            </select>
          </div>

          {/* Action Filter */}
          <div className="flex items-center gap-1.5">
            <Filter className="w-3.5 h-3.5 text-text-muted" />
            <select
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
              className="px-2.5 py-1 rounded-lg bg-surface-2 border border-surface-3 text-xs text-text-secondary focus:outline-none focus:border-brand-cyan"
            >
              <option value="all">All Actions</option>
              <option value="job_created">Job Created</option>
              <option value="candidate_created">Candidate Created</option>
              <option value="resume_parsed">Resume Parsed</option>
              <option value="match_analysis_completed">Match Analysis</option>
              <option value="interview_prepared">Interview Prepared</option>
              <option value="interview_finalized">Interview Finalized</option>
              <option value="evaluation_generated">Evaluation Generated</option>
              <option value="recruiter_decision">Human Decision</option>
              <option value="tamper_flag_raised">Tamper Alert</option>
            </select>
          </div>
        </div>
      </div>

      {/* Logs Table / List */}
      {loading ? (
        <div className="flex flex-col items-center justify-center p-20 text-text-muted gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-brand-cyan" />
          <span className="text-xs font-mono">Loading compliance audit records...</span>
        </div>
      ) : filteredLogs.length > 0 ? (
        <div className="flex flex-col gap-2.5">
          {filteredLogs.map((log) => {
            const isExpanded = expandedLogId === log.id;
            const actionStyle = ACTION_COLORS[log.action] || 'bg-surface-2 text-text-secondary border-surface-3';
            const actionLabel = ACTION_LABELS[log.action] || log.action;

            return (
              <div
                key={log.id}
                className="rounded-xl bg-surface-1 border border-surface-2 hover:border-surface-3 transition overflow-hidden shadow-sm"
              >
                <div
                  onClick={() => toggleExpand(log.id)}
                  className="p-4 flex items-center justify-between gap-4 cursor-pointer select-none"
                >
                  <div className="flex items-center gap-3.5">
                    <button className="text-text-muted hover:text-text-primary p-0.5">
                      {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                    </button>

                    <span className={`px-2.5 py-1 rounded-md text-[11px] font-mono font-bold border uppercase tracking-wider ${actionStyle}`}>
                      {actionLabel}
                    </span>

                    <div className="flex flex-col">
                      <span className="text-xs font-bold text-text-primary">
                        Entity: <span className="font-mono text-brand-cyan">{log.entity_type}</span> ({log.entity_id ? `${log.entity_id.slice(0, 8)}...` : 'N/A'})
                      </span>
                      {log.details && (
                        <span className="text-[11px] text-text-secondary truncate max-w-md">
                          {log.details.title || log.details.name || log.details.decision || JSON.stringify(log.details).slice(0, 60)}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-4 text-xs font-mono text-text-muted">
                    <div className="hidden sm:flex items-center gap-1.5">
                      <User className="w-3.5 h-3.5 text-brand-indigo" />
                      <span>{log.user_id ? `${log.user_id.slice(0, 8)}...` : 'System (AI)'}</span>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5" />
                      <span>{new Date(log.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
                      <span className="text-[10px] text-text-muted hidden md:inline">
                        ({new Date(log.created_at).toLocaleDateString()})
                      </span>
                    </div>
                  </div>
                </div>

                {isExpanded && (
                  <div className="px-6 py-4 bg-surface-2/40 border-t border-surface-2 flex flex-col gap-3 font-mono text-xs">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-[11px]">
                      <div>
                        <span className="text-text-muted block uppercase text-[9px]">Event ID</span>
                        <span className="text-text-primary select-all">{log.id}</span>
                      </div>
                      <div>
                        <span className="text-text-muted block uppercase text-[9px]">Organization ID</span>
                        <span className="text-text-primary select-all">{log.org_id}</span>
                      </div>
                      <div>
                        <span className="text-text-muted block uppercase text-[9px]">Exact Timestamp</span>
                        <span className="text-text-primary">{new Date(log.created_at).toISOString()}</span>
                      </div>
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-[10px] text-text-muted uppercase font-bold flex items-center gap-1">
                          <FileCode className="w-3 h-3 text-brand-cyan" />
                          <span>Audit Payload Data</span>
                        </span>
                      </div>
                      <pre className="p-3 rounded-lg bg-canvas border border-surface-3 text-[11px] text-brand-cyan overflow-x-auto leading-relaxed">
                        {JSON.stringify(log.details || {}, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="p-16 rounded-2xl bg-surface-1 border border-dashed border-surface-2 flex flex-col items-center justify-center text-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-surface-2 flex items-center justify-center text-text-muted">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-text-primary">No audit records found</h3>
            <p className="text-xs text-text-muted mt-1 max-w-sm">
              {searchTerm || actionFilter !== 'all' || entityFilter !== 'all'
                ? 'Try adjusting your search query or filter selections.'
                : 'As recruitment events take place, provenance logs will be automatically recorded here.'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
