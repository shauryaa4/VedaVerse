import type { Confidence, AnswerConfidence } from '../types'

interface BadgeProps {
  level: Confidence | AnswerConfidence
  label?: string
}

export function Badge({ level, label }: BadgeProps) {
  const cls = `badge badge-${level}`
  const text = label ?? level.toUpperCase()
  return <span className={cls}>{text}</span>
}

export function VerifiedBadge() {
  return <span className="badge badge-verified">Verified ✓</span>
}
