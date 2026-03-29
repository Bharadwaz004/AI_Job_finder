import React from 'react'

/**
 * Circular score indicator with animated stroke.
 * score: 0-100
 * size: pixel diameter
 */
export default function ScoreRing({ score, size = 56 }) {
  const strokeWidth = 4
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference

  // Color gradient based on score
  let color = '#f43f5e' // red
  if (score >= 70) color = '#10b981' // green
  else if (score >= 45) color = '#f59e0b' // amber

  return (
    <div className="score-ring" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        {/* Background ring */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth={strokeWidth}
        />
        {/* Score arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{
            transition: 'stroke-dashoffset 0.8s ease-out, stroke 0.3s',
          }}
        />
      </svg>
      <span
        className="absolute inset-0 flex items-center justify-center text-xs font-bold font-mono"
        style={{ color }}
      >
        {Math.round(score)}
      </span>
    </div>
  )
}
