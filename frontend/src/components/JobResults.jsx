import React, { useState } from 'react'
import { ExternalLink, ChevronDown, ChevronUp, MapPin, Building2, Clock, Banknote } from 'lucide-react'
import ScoreRing from './ScoreRing'

const METHOD_LABELS = {
  rule_based: 'Rule-Based',
  llm_based: 'AI Deep Score',
  hybrid: 'Hybrid',
}

export default function JobResults({ jobs, method, onRerank, totalFound }) {
  return (
    <div className="mt-8 animate-slide-up">
      {/* Controls bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h3 className="font-display font-semibold text-lg text-white">
            Matched Jobs
          </h3>
          <p className="text-surface-200/40 text-xs mt-0.5">
            {jobs.length} jobs ranked by relevance
            {totalFound > jobs.length && ` (of ${totalFound} found)`}
          </p>
        </div>

        {/* Ranking method toggle */}
        <div className="flex items-center gap-1 bg-white/[0.03] rounded-xl p-1 border border-white/[0.06]">
          {Object.entries(METHOD_LABELS).map(([key, label]) => (
            <button
              key={key}
              onClick={() => onRerank(key)}
              className={`
                px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all duration-200
                ${method === key
                  ? 'bg-accent text-white shadow-sm'
                  : 'text-surface-200/50 hover:text-surface-200/80 hover:bg-white/[0.03]'
                }
              `}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Job Cards */}
      <div className="space-y-3">
        {jobs.map((item, i) => (
          <JobCard key={item.job.id || i} data={item} index={i} />
        ))}
      </div>
    </div>
  )
}


function JobCard({ data, index }) {
  const [expanded, setExpanded] = useState(false)
  const { job, match_score, matched_skills, missing_skills, explanation, improvement_tips } = data

  return (
    <div
      className="glass-card-hover p-5 animate-fade-in"
      style={{ animationDelay: `${index * 60}ms` }}
    >
      {/* Top row */}
      <div className="flex items-start gap-4">
        <ScoreRing score={match_score} />

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h4 className="font-display font-semibold text-white text-sm truncate">
                {job.title}
              </h4>
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1">
                {job.company && (
                  <span className="inline-flex items-center gap-1 text-xs text-surface-200/60">
                    <Building2 size={11} />
                    {job.company}
                  </span>
                )}
                {job.location && (
                  <span className="inline-flex items-center gap-1 text-xs text-surface-200/40">
                    <MapPin size={11} />
                    {job.location}
                  </span>
                )}
                {job.posted_date && (
                  <span className="inline-flex items-center gap-1 text-xs text-surface-200/30">
                    <Clock size={11} />
                    {job.posted_date}
                  </span>
                )}
                {job.salary && (
                  <span className="inline-flex items-center gap-1 text-xs text-mint-light/70">
                    <Banknote size={11} />
                    {job.salary}
                  </span>
                )}
              </div>
            </div>

            {/* Apply link */}
            {job.link && (
              <a
                href={job.link}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-ghost text-[11px] px-3 py-1.5 shrink-0"
              >
                Apply <ExternalLink size={11} />
              </a>
            )}
          </div>

          {/* Skills tags row */}
          <div className="flex flex-wrap gap-1 mt-3">
            {matched_skills.slice(0, 6).map((s, i) => (
              <span key={i} className="tag-mint text-[10px] py-0.5 px-2">{s}</span>
            ))}
            {missing_skills.slice(0, 4).map((s, i) => (
              <span key={i} className="tag-missing text-[10px] py-0.5 px-2">{s}</span>
            ))}
          </div>
        </div>
      </div>

      {/* Expand toggle */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="mt-3 w-full flex items-center justify-center gap-1 text-[11px] text-surface-200/30 hover:text-surface-200/60 transition-colors py-1"
      >
        {expanded ? (
          <>Less <ChevronUp size={12} /></>
        ) : (
          <>Details <ChevronDown size={12} /></>
        )}
      </button>

      {/* Expanded details */}
      {expanded && (
        <div className="mt-3 pt-3 border-t border-white/[0.04] space-y-3 animate-fade-in">
          {/* Explanation */}
          {explanation && (
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-surface-200/40 mb-1">
                Match Analysis
              </p>
              <p className="text-sm text-surface-200/70 leading-relaxed">{explanation}</p>
            </div>
          )}

          {/* Job description */}
          {job.description && (
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-surface-200/40 mb-1">
                Description
              </p>
              <p className="text-xs text-surface-200/50 leading-relaxed line-clamp-4">
                {job.description}
              </p>
            </div>
          )}

          {/* Improvement tips */}
          {improvement_tips?.length > 0 && (
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-surface-200/40 mb-1.5">
                Tips to Improve Match
              </p>
              <ul className="space-y-1">
                {improvement_tips.map((tip, i) => (
                  <li key={i} className="text-xs text-surface-200/60 flex items-start gap-2">
                    <span className="text-accent-light mt-0.5">→</span>
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
