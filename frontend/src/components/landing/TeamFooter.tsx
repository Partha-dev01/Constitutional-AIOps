import { Link } from 'react-router-dom'
import { Shield, GraduationCap, ArrowRight } from 'lucide-react'

const TEAM = [
  '[redacted]',
  '[redacted]',
  '[redacted]',
  '[redacted]',
]

export function TeamFooter() {
  return (
    <footer className="py-20 sm:py-28">
      <div className="mx-auto max-w-4xl px-6 text-center">
        <div className="mb-6 flex items-center justify-center gap-2">
          <Shield className="h-7 w-7 text-primary" />
          <span className="text-lg font-bold">Constitutional AIOps</span>
        </div>

        <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-1.5 text-xs font-medium text-muted-foreground">
          <GraduationCap className="h-3.5 w-3.5 text-primary" />
          B.Tech Final Year Project
        </div>

        <div className="mx-auto mb-10 grid max-w-2xl gap-2">
          <div className="flex flex-wrap items-center justify-center gap-x-3 gap-y-1 text-sm text-foreground">
            {TEAM.map((member) => (
              <span key={member}>{member}</span>
            ))}
          </div>
          <p className="text-sm text-muted-foreground">
            [redacted]
          </p>
          <p className="text-sm text-muted-foreground">
            Advisor: [redacted]
          </p>
        </div>

        <Link
          to="/"
          className="group inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground transition-transform hover:-translate-y-0.5"
        >
          Open the Dashboard
          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
        </Link>

        <p className="mt-10 text-xs text-muted-foreground">
          Constitutional AIOps · v0.7.0
        </p>
      </div>
    </footer>
  )
}
