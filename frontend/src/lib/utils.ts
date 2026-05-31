import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: Date | string): string {
  const d = new Date(date)
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * Strip common inline markdown markers (bold/italic/code/heading/list) from a
 * string for plain-text contexts like sidebar titles, where raw `**` would
 * otherwise leak. Not a full parser — just the markers that show up in
 * model-generated previews.
 */
export function stripMarkdown(text: string): string {
  return text
    .replace(/^\s*#{1,6}\s*/g, '')        // heading markers
    .replace(/^\s*([-*+]|\d+[.)])\s+/g, '') // leading bullet / number
    .replace(/\*\*|__/g, '')               // bold
    .replace(/`+/g, '')                    // inline code
    .replace(/(?<!\*)\*(?!\*)/g, '')       // stray single-* italics
    .replace(/\s+/g, ' ')
    .trim()
}

export function formatRelativeTime(date: Date | string): string {
  const now = new Date()
  const d = new Date(date)
  const diffMs = now.getTime() - d.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  return `${diffDays}d ago`
}
