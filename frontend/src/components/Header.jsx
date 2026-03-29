import React from 'react'
import { RotateCcw, Sparkles } from 'lucide-react'

export default function Header({ onReset, showReset }) {
  return (
    <header className="border-b border-white/[0.04] backdrop-blur-md sticky top-0 z-50 bg-surface-950/80">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent to-rose-600 flex items-center justify-center">
            <Sparkles size={16} className="text-white" />
          </div>
          <div>
            <h1 className="font-display font-semibold text-base tracking-tight text-white">
              ResumeMatch
            </h1>
            <span className="text-[10px] uppercase tracking-[0.15em] text-accent-light/70 font-medium">
              AI-Powered
            </span>
          </div>
        </div>

        {showReset && (
          <button onClick={onReset} className="btn-ghost text-xs gap-1.5">
            <RotateCcw size={13} />
            Start Over
          </button>
        )}
      </div>
    </header>
  )
}
