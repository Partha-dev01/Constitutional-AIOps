import { LegalPage, LegalSection } from '../components/LegalPage'

/**
 * Public privacy policy for the HOSTED demo. Self-hosted deployments of the
 * open-source project are run by whoever operates them and are not covered
 * here. Intentionally plain and honest: this is a student research demo, not
 * a commercial product.
 */
export function Privacy() {
  return (
    <LegalPage title="Privacy Policy" lastUpdated="September 5, 2026">
      <p className="text-sm leading-relaxed text-muted-foreground">
        This policy explains what the hosted Constitutional AIOps demo collects and
        why. Constitutional AIOps is an open-source project released under the
        AGPL-3.0 license. If you run your own copy of the software, you control your
        own data and this policy does not apply to your deployment.
      </p>

      <LegalSection heading="What we collect">
        <p>
          When you create a demo account we store the username, email address, and a
          hashed password you provide. We never store your password in plain text. Our
          servers also keep standard request logs, such as IP address and timestamps,
          to keep the service secure and to prevent abuse.
        </p>
        <p>
          The demo runs on sample data. Please do not enter real production
          credentials, secrets, or sensitive infrastructure details into it.
        </p>
      </LegalSection>

      <LegalSection heading="How we use it">
        <p>
          Your email is used to verify your account and, if it is ever necessary, to
          contact you about the demo. We do not sell or rent your personal data, we do
          not share it with advertisers, and we do not send marketing email.
        </p>
      </LegalSection>

      <LegalSection heading="Service providers">
        <p>
          The demo is hosted on Amazon Web Services. Account verification email is sent
          through Amazon Simple Email Service. The signup form uses Cloudflare Turnstile
          to tell humans apart from bots. These providers process the minimum data
          needed to perform those functions.
        </p>
      </LegalSection>

      <LegalSection heading="Cookies">
        <p>
          A single session cookie keeps you signed in after login. The demo uses no
          third-party advertising or analytics trackers.
        </p>
      </LegalSection>

      <LegalSection heading="Data retention">
        <p>
          This is a demonstration environment. Demo accounts and any data created in
          them may be reset or removed periodically without notice. Do not rely on the
          demo to store anything you need to keep.
        </p>
      </LegalSection>

      <LegalSection heading="Your choices">
        <p>
          You can ask us to delete your demo account and its associated data. Requests
          go through the project repository on GitHub. Since demo data is transient, the
          simplest path is usually to stop using the account and let the next reset
          clear it.
        </p>
      </LegalSection>

      <LegalSection heading="Changes">
        <p>
          We may update this policy as the demo evolves. When we do, we will change the
          date shown at the top of this page.
        </p>
      </LegalSection>
    </LegalPage>
  )
}

export default Privacy
