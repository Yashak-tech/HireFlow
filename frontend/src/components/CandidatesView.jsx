import React, { useState } from 'react';
import { 
  Users, 
  UserPlus, 
  UploadCloud, 
  Search, 
  MapPin, 
  Briefcase, 
  FileText, 
  Calendar,
  ChevronRight,
  ExternalLink,
  Loader2
} from 'lucide-react';

export default function CandidatesView({ 
  candidates, 
  loading, 
  onSelectCandidate, 
  onOpenCreateCandidate, 
  onOpenUpload 
}) {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredCandidates = candidates.filter((c) => {
    const term = searchTerm.toLowerCase();
    return (
      c.full_name.toLowerCase().includes(term) ||
      c.email.toLowerCase().includes(term) ||
      (c.current_title && c.current_title.toLowerCase().includes(term)) ||
      (c.current_company && c.current_company.toLowerCase().includes(term)) ||
      (c.location && c.location.toLowerCase().includes(term))
    );
  });

  return (
    <div className="flex flex-col gap-6 w-full">
      {/* Header & Actions */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold font-display text-text-primary tracking-tight flex items-center gap-2.5">
            <Users className="w-5 h-5 text-brand-indigo" />
            <span>Candidate Talent Pool</span>
            <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-surface-2 text-text-muted border border-surface-3">
              {candidates.length}
            </span>
          </h2>
          <p className="text-xs text-text-secondary mt-1">
            Organization-wide candidate profiles, skills inventories, and uploaded resume documents.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onOpenCreateCandidate}
            className="px-3.5 py-2 rounded-xl bg-surface-2 hover:bg-surface-3 border border-surface-3 text-text-primary text-xs font-semibold flex items-center gap-2 transition"
          >
            <UserPlus className="w-4 h-4 text-brand-indigo" />
            <span>Add Candidate</span>
          </button>

          <button
            onClick={() => onOpenUpload(null)}
            className="px-4 py-2 rounded-xl bg-brand-cyan hover:bg-brand-cyan/90 text-canvas text-xs font-bold flex items-center gap-2 shadow-lg shadow-brand-cyan/20 transition cursor-pointer"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Upload Resume</span>
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="p-4 rounded-xl bg-surface-1 border border-surface-2">
        <div className="relative w-full">
          <Search className="w-4 h-4 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search candidates by name, email, job title, company, or location..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 rounded-lg bg-surface-2 border border-surface-3 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-indigo transition"
          />
        </div>
      </div>

      {/* Candidates List / Grid */}
      {loading ? (
        <div className="flex flex-col items-center justify-center p-20 text-text-muted gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-brand-indigo" />
          <span className="text-xs font-mono">Loading candidates...</span>
        </div>
      ) : filteredCandidates.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredCandidates.map((cand) => (
            <div
              key={cand.id}
              onClick={() => onSelectCandidate(cand)}
              className="p-5 rounded-2xl bg-surface-1 border border-surface-2 hover:border-brand-indigo/40 cursor-pointer transition flex flex-col justify-between gap-4 group shadow-xl hover:shadow-2xl hover:shadow-brand-indigo/5"
            >
              <div className="flex flex-col gap-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-surface-2 to-surface-3 text-brand-indigo font-display font-bold flex items-center justify-center text-sm border border-surface-3 group-hover:border-brand-indigo/40 transition">
                      {cand.full_name?.charAt(0) || 'C'}
                    </div>
                    <div>
                      <h3 className="text-sm font-bold font-display text-text-primary group-hover:text-brand-indigo transition">
                        {cand.full_name}
                      </h3>
                      <p className="text-[11px] text-text-secondary truncate max-w-[180px]">
                        {cand.current_title || 'Software Engineer'}
                        {cand.current_company ? ` at ${cand.current_company}` : ''}
                      </p>
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-text-muted group-hover:text-brand-indigo transition" />
                </div>

                <div className="flex flex-wrap items-center gap-2 text-[11px] text-text-muted font-mono">
                  {cand.location && (
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3 text-text-muted" />
                      {cand.location}
                    </span>
                  )}
                  {cand.years_of_experience && (
                    <span className="flex items-center gap-1">
                      <Briefcase className="w-3 h-3 text-brand-indigo" />
                      {cand.years_of_experience}y exp
                    </span>
                  )}
                </div>

                {/* Skills Preview */}
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
                        +{cand.skills.length - 4}
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Bottom Card Footer */}
              <div className="pt-3 border-t border-surface-2 flex items-center justify-between text-[11px] font-mono text-text-muted">
                <span className="flex items-center gap-1 text-brand-cyan">
                  <FileText className="w-3.5 h-3.5" />
                  {cand.resumes?.length || 0} resume doc{cand.resumes?.length === 1 ? '' : 's'}
                </span>
                <span className="text-text-muted">
                  {cand.associated_jobs?.length || 0} role{cand.associated_jobs?.length === 1 ? '' : 's'}
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-16 rounded-2xl bg-surface-1 border border-dashed border-surface-2 flex flex-col items-center justify-center text-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-surface-2 flex items-center justify-center text-text-muted">
            <Users className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-text-primary">No candidates found</h3>
            <p className="text-xs text-text-muted mt-1 max-w-sm">
              {searchTerm
                ? 'Try adjusting your search query.'
                : 'Upload resumes or add candidate profiles to begin candidate screening.'}
            </p>
          </div>
          {!searchTerm && (
            <div className="flex items-center gap-3 mt-2">
              <button
                onClick={onOpenCreateCandidate}
                className="px-4 py-2 rounded-xl bg-surface-2 hover:bg-surface-3 text-text-primary text-xs font-semibold transition"
              >
                Add Profile Manually
              </button>
              <button
                onClick={() => onOpenUpload(null)}
                className="px-4 py-2 rounded-xl bg-brand-cyan hover:bg-brand-cyan/90 text-canvas text-xs font-bold shadow-lg shadow-brand-cyan/20 transition"
              >
                Upload Resume
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
