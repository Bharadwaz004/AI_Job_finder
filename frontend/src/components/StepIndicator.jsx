import React from 'react'
import { Check } from 'lucide-react'

export default function StepIndicator({ steps, current }) {
  return (
    <div className="flex items-center justify-center gap-1 py-8">
      {steps.map((s, i) => {
        const done = i < current
        const active = i === current
        return (
          <React.Fragment key={s.key}>
            <div className="flex items-center gap-2">
              <div
                className={`
                  w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold
                  transition-all duration-300
                  ${done ? 'bg-mint text-surface-950' : ''}
                  ${active ? 'bg-accent text-white ring-2 ring-accent/30 ring-offset-2 ring-offset-surface-950' : ''}
                  ${!done && !active ? 'bg-white/[0.06] text-surface-200/40' : ''}
                `}
              >
                {done ? <Check size={14} strokeWidth={3} /> : i + 1}
              </div>
              <span
                className={`text-xs font-medium hidden sm:block transition-colors duration-300
                  ${active ? 'text-white' : done ? 'text-mint-light/70' : 'text-surface-200/30'}
                `}
              >
                {s.label}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div
                className={`w-8 sm:w-12 h-px mx-1 transition-colors duration-300
                  ${done ? 'bg-mint/40' : 'bg-white/[0.06]'}
                `}
              />
            )}
          </React.Fragment>
        )
      })}
    </div>
  )
}
