import React from 'react'
import { User, Briefcase, GraduationCap, Code, Target, Search } from 'lucide-react'

export default function ProfileCard({ profile, onSearchJobs, showSearchButton }) {
  const p = profile

  return (
    <div className="animate-slide-up">
      {/* Header */}
      <div className="glass-card p-6 sm:p-8 mb-4">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-accent/20 to-accent/5 flex items-center justify-center border border-accent/10">
              <User size={20} className="text-accent-light" />
            </div>
            <div>
              <h3 className="font-display font-semibold text-lg text-white">
                {p.name || 'Your Profile'}
              </h3>
              {p.location && (
                <p className="text-surface-200/50 text-xs mt-0.5">{p.location}</p>
              )}
              {p.years_of_experience > 0 && (
                <p className="text-surface-200/40 text-xs mt-0.5">
                  {p.years_of_experience} years of experience
                </p>
              )}
            </div>
          </div>

          {showSearchButton && (
            <button onClick={onSearchJobs} className="btn-primary shrink-0">
              <Search size={15} />
              Find Matching Jobs
            </button>
          )}
        </div>

        {p.summary && (
          <p className="mt-4 text-surface-200/60 text-sm leading-relaxed border-t border-white/[0.04] pt-4">
            {p.summary}
          </p>
        )}
      </div>

      {/* Skills & Details Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Skills */}
        {p.skills?.length > 0 && (
          <div className="glass-card p-5">
            <div className="flex items-center gap-2 mb-3">
              <Code size={14} className="text-accent-light" />
              <h4 className="text-xs font-semibold uppercase tracking-wider text-surface-200/50">
                Skills ({p.skills.length})
              </h4>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {p.skills.map((s, i) => (
                <span key={i} className="tag text-[11px]">{s}</span>
              ))}
            </div>
          </div>
        )}

        {/* Suggested Roles */}
        {p.suggested_roles?.length > 0 && (
          <div className="glass-card p-5">
            <div className="flex items-center gap-2 mb-3">
              <Target size={14} className="text-mint-light" />
              <h4 className="text-xs font-semibold uppercase tracking-wider text-surface-200/50">
                Suggested Roles
              </h4>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {p.suggested_roles.map((r, i) => (
                <span key={i} className="tag-mint text-[11px]">{r}</span>
              ))}
            </div>
          </div>
        )}

        {/* Experience */}
        {p.experience?.length > 0 && (
          <div className="glass-card p-5">
            <div className="flex items-center gap-2 mb-3">
              <Briefcase size={14} className="text-amber-400" />
              <h4 className="text-xs font-semibold uppercase tracking-wider text-surface-200/50">
                Experience
              </h4>
            </div>
            <div className="space-y-3">
              {p.experience.slice(0, 3).map((exp, i) => (
                <div key={i} className="border-l-2 border-white/[0.06] pl-3">
                  <p className="text-white text-sm font-medium">{exp.title}</p>
                  <p className="text-surface-200/50 text-xs">
                    {exp.company} {exp.duration && `· ${exp.duration}`}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Education */}
        {p.education?.length > 0 && (
          <div className="glass-card p-5">
            <div className="flex items-center gap-2 mb-3">
              <GraduationCap size={14} className="text-sky-400" />
              <h4 className="text-xs font-semibold uppercase tracking-wider text-surface-200/50">
                Education
              </h4>
            </div>
            <div className="space-y-2">
              {p.education.map((edu, i) => (
                <div key={i}>
                  <p className="text-white text-sm font-medium">{edu.degree}</p>
                  <p className="text-surface-200/50 text-xs">
                    {edu.institution} {edu.year && `· ${edu.year}`}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
