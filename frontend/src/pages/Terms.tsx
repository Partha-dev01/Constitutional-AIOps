import { LegalPage, LegalSection } from '../components/LegalPage'

/**
 * Public terms of service for the HOSTED demo. These terms govern use of the
 * demo instance only. The software itself is licensed separately under
 * AGPL-3.0. Plain and honest, matching the demo's non-commercial nature.
 */
export function Terms() {
  return (
    <LegalPage title="Terms of Service" lastUpdated="September 5, 2026">
      <p className="text-sm leading-relaxed text-muted-foreground">
        These terms cover your use of the hosted Constitutional AIOps demo. By creating
        an account or using the demo you agree to them. If you do not agree, please do
        not use the demo.
      </p>

      <LegalSection heading="What the demo is">
        <p>
          The demo is a free showcase of the Constitutional AIOps open-source project,
          provided as-is for evaluation and learning. It is not a production service and
          is not meant to manage real infrastructure or hold real operational data.
        </p>
      </LegalSection>

      <LegalSection heading="Your account">
        <p>
          Keep your login details secure. You are responsible for activity under your
          account. Accounts are for individual evaluation, so please do not share them.
        </p>
      </LegalSection>

      <LegalSection heading="Acceptable use">
        <p>You agree not to:</p>
        <ul className="list-disc space-y-1 pl-5">
          <li>use the demo for anything unlawful;</li>
          <li>attempt to disrupt, overload, probe, or break into the service;</li>
          <li>upload real secrets, credentials, or other people's personal data;</li>
          <li>scrape or automate against the demo beyond normal interactive use.</li>
        </ul>
      </LegalSection>

      <LegalSection heading="Availability">
        <p>
          To keep costs low the demo sleeps when idle and wakes on your first visit, so
          the first load can take a moment. The demo may be unavailable, reset, or
          discontinued at any time without notice.
        </p>
      </LegalSection>

      <LegalSection heading="No warranty">
        <p>
          The demo is provided without warranty of any kind, express or implied. To the
          extent allowed by law, the maintainers are not liable for any loss or damage
          arising from your use of the demo.
        </p>
      </LegalSection>

      <LegalSection heading="The software license">
        <p>
          These terms apply to the hosted demo only. The Constitutional AIOps software
          is licensed under the GNU AGPL-3.0. If you run your own copy, that license,
          not these terms, governs your use of the code.
        </p>
      </LegalSection>

      <LegalSection heading="Suspension">
        <p>
          We may suspend or remove any demo account at any time, in particular to stop
          abuse or to protect the service and other users.
        </p>
      </LegalSection>

      <LegalSection heading="Contact and changes">
        <p>
          Questions go through the project repository on GitHub. We may update these
          terms as the demo changes, and continued use after an update means you accept
          the new version.
        </p>
      </LegalSection>
    </LegalPage>
  )
}

export default Terms
