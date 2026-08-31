import { LandingHeader } from '../components/landing/LandingHeader'
import { HeroSection } from '../components/landing/HeroSection'
import { StatsBand } from '../components/landing/StatsBand'
import { FeatureGrid } from '../components/landing/FeatureGrid'
import { ArchitectureBand } from '../components/landing/ArchitectureBand'
import { ProofSection } from '../components/landing/ProofSection'
import { TeamFooter } from '../components/landing/TeamFooter'

/**
 * Public landing page mounted at /welcome, OUTSIDE the sidebar Layout. It makes
 * no network/api/websocket calls — fully static and deterministic — so it loads
 * instantly and renders identically with or without a live backend.
 *
 * The fixed LandingHeader overlays the hero (which carries its own top
 * padding), so no page-level offset is needed. Anchor targets: #features,
 * #architecture, #live, #team.
 */
export function Landing() {
  return (
    <div className="relative min-h-screen overflow-x-hidden font-sans text-foreground">
      {/* Animated colour-field backdrop (fixed, decorative, behind everything). */}
      <div className="aurora" aria-hidden="true" />
      <LandingHeader />
      <HeroSection />
      <StatsBand />
      <FeatureGrid />
      <ArchitectureBand />
      <ProofSection />
      <TeamFooter />
    </div>
  )
}
