import { cn } from '../../lib/utils'

interface ShotFrameProps {
  /** Root-absolute image source, e.g. /screenshots/dashboard.png */
  src: string
  alt: string
  /** Hero shot loads eagerly; everything else lazy-loads. */
  eager?: boolean
  className?: string
}

/**
 * Glass "browser" frame shared by the hero showcase and the proof rows:
 * rounded glass panel, 3-dot window chrome, top sheen, drop glow (all in
 * .shot-frame / .shot-sheen, see styles/landing.css).
 *
 * Screenshots may not exist in every deployment; each <img> hides itself on
 * error so a missing PNG degrades to an empty chrome bar with no broken icon.
 */
export function ShotFrame({ src, alt, eager = false, className }: ShotFrameProps) {
  return (
    <figure className={cn('shot-frame', className)}>
      {/* Window chrome */}
      <div
        className="flex items-center gap-1.5 border-b border-border/60 bg-card/80 px-4 py-2.5"
        aria-hidden="true"
      >
        <span className="h-2.5 w-2.5 rounded-full bg-[hsl(0_70%_55%/0.8)]" />
        <span className="h-2.5 w-2.5 rounded-full bg-[hsl(45_90%_55%/0.8)]" />
        <span className="h-2.5 w-2.5 rounded-full bg-[hsl(140_60%_45%/0.8)]" />
      </div>
      <img
        src={src}
        alt={alt}
        loading={eager ? 'eager' : 'lazy'}
        className="block w-full"
        onError={(e) => {
          (e.currentTarget as HTMLImageElement).style.display = 'none'
        }}
      />
      {/* Animated glossy sweep (killed under reduced motion). */}
      <div className="shot-sheen" aria-hidden="true" />
    </figure>
  )
}
