import { HeroSection } from '../components/landing/HeroSection'
import { FeatureGrid } from '../components/landing/FeatureGrid'
import { ArchitectureBand } from '../components/landing/ArchitectureBand'
import { ProofSection } from '../components/landing/ProofSection'
import { TeamFooter } from '../components/landing/TeamFooter'

/**
 * Public landing page mounted at /welcome, OUTSIDE the sidebar Layout. It makes
 * no network/api/websocket calls — fully static and deterministic — so it loads
 * instantly and renders identically with or without a live backend.
 */
export function Landing() {
  return (
    <div className="min-h-screen overflow-x-hidden bg-background font-sans text-foreground">
      <HeroSection />
      <FeatureGrid />
      <ArchitectureBand />
      <ProofSection />
      <TeamFooter />
    </div>
  )
}
