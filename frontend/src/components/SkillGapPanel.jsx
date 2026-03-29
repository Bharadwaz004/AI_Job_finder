import React from 'react'
import { TrendingUp, Check, X, Lightbulb } from 'lucide-react'

export default function SkillGapPanel({ data }) {
  if (!data || !data.most_demanded_skills?.length) return null

  return (
    <div className="mt-6 glass-card p-6 animate-slide-up">
      <div className="flex items-center gap-2 mb-5">
        <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center border border-amber-500/20">
          <TrendingUp size={16} className="text-amber-400" />
        </div>
        <div>
          <h3 className="font-display font-semibold text-sm text-white">Skill Gap Analysis</h3>
          <p className="text-[11px] text-surface-200/40">Based on all matched jobs</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Most Demanded */}
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wider text-surface-200/40 mb-2">
            Most Demanded
          </p>
          <div className="space-y-1.5">
            {data.most_demanded_skills.slice(0, 8).map((s, i) => {
              const hasIt = data.user_has?.some(
                (us) => us.toLowerCase() === s.toLowerCase()
              )
              return (
                <div key={i} className="flex items-center gap-2 text-xs">
                  {hasIt ? (
                    <Check size={12} className="text-mint shrink-0" />
                  ) : (
                    <X size={12} className="text-rose-400 shrink-0" />
                  )}
                  <span className={hasIt ? 'text-surface-200/70' : 'text-surface-200/50'}>
                    {s}
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        {/* Your Skills */}
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wider text-surface-200/40 mb-2">
            You Have
          </p>
          <div className="flex flex-wrap gap-1">
            {(data.user_has || []).slice(0, 12).map((s, i) => (
              <span key={i} className="tag-mint text-[10px] py-0.5 px-2">{s}</span>
            ))}
          </div>
        </div>

        {/* Recommendations */}
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wider text-surface-200/40 mb-2 flex items-center gap-1">
            <Lightbulb size={11} className="text-amber-400" />
            Recommendations
          </p>
          <ul className="space-y-2">
            {(data.recommendations || []).slice(0, 5).map((r, i) => (
              <li key={i} className="text-xs text-surface-200/60 leading-relaxed flex items-start gap-2">
                <span className="text-amber-400 mt-0.5 shrink-0">•</span>
                {r}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
