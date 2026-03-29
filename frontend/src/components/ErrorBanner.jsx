import React from 'react'
import { AlertTriangle, X } from 'lucide-react'

export default function ErrorBanner({ message, onDismiss }) {
  return (
    <div className="mb-6 flex items-center gap-3 bg-rose-500/[0.08] border border-rose-500/20 rounded-xl px-4 py-3 animate-fade-in">
      <AlertTriangle size={16} className="text-rose-400 shrink-0" />
      <p className="text-rose-300 text-sm flex-1">{message}</p>
      <button
        onClick={onDismiss}
        className="text-rose-400/60 hover:text-rose-300 transition-colors p-1"
      >
        <X size={14} />
      </button>
    </div>
  )
}
