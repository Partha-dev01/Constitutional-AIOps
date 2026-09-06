import { Workflow } from 'lucide-react'
import { PageShell, Pill, H2, P, Code, Card, CTARow } from '../components/prose'

/**
 * Standalone "How it works" page (/architecture.html, a Vite entry). Walks the
 * telemetry-to-remediation pipeline, the two-agent split, the graph memory and
 * where the models run. Fully static and public-safe, no network calls.
 */

const STAGES: { n: string; title: string; body: string }[] = [
  {
    n: '1',
    title: 'Ingest telemetry',
    body: 'Logs, metrics and traces arrive through an OpenTelemetry collector into an LGTM stack (Loki, Grafana, Tempo, Prometheus). This is the raw signal the system reasons over.',
  },
  {
    n: '2',
    title: 'Annotate, fast',
    body: 'A small fast agent classifies and tags the stream as it lands, turning noisy telemetry into structured, labelled events without waiting on the larger model.',
  },
  {
    n: '3',
    title: 'Correlate against memory',
    body: 'Structured events are matched against a graph of past incidents in Neo4j, so a new problem is read in the light of how similar ones actually resolved.',
  },
  {
    n: '4',
    title: 'Reason and propose',
    body: 'The larger reasoning agent performs root-cause analysis and drafts a remediation. It proposes; it does not execute on its own.',
  },
  {
    n: '5',
    title: 'Pass the gate',
    body: 'Every proposal runs the constitutional gate: twelve principles across three tiers, then a confidence score that routes it to automatic, human approval, or alert only.',
  },
  {
    n: '6',
    title: 'Act, then learn',
    body: 'An approved action runs and the outcome is written back to the graph, so the next incident starts from a slightly better memory. Nothing acts silently.',
  },
]

export function Architecture() {
  return (
    <PageShell
      maxWidth="5xl"
      pill={<Pill icon={<Workflow className="h-3.5 w-3.5" aria-hidden="true" />}>How it works</Pill>}
      title="From telemetry to a safe fix"
      lead="Constitutional AIOps reads your observability data, finds the likely cause, and proposes a fix that has to clear a safety gate before anything runs. Here is the whole path."
    >
      <section>
        <H2 id="pipeline">The pipeline</H2>
        <P>
          Six stages, each doing one job. The split between a fast annotator and a slower reasoner is the
          point: cheap work stays cheap and the expensive model is only spent where judgement is needed.
        </P>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {STAGES.map((s) => (
            <Card key={s.n}>
              <div className="mb-3 flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-background text-sm font-bold text-primary">
                {s.n}
              </div>
              <h3 className="mb-1.5 text-base font-semibold">{s.title}</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">{s.body}</p>
            </Card>
          ))}
        </div>
      </section>

      <H2 id="agents">Two agents, not one</H2>
      <P>
        The system runs two models side by side rather than swapping one in and out. A fast agent
        (Qwen3-4B) annotates telemetry in near real time. A reasoning agent (Qwen3-14B) handles
        root-cause analysis, remediation planning and the chat you talk to. Keeping both loaded means no
        swap latency and a clean division of labour: classification never waits behind analysis.
      </P>

      <H2 id="memory">Graph-episodic memory</H2>
      <P>
        Incidents are not treated as one-off events. Each resolved case becomes a node in a Neo4j graph,
        linked to the entities and services it touched. When a new incident looks like an old one, the
        reasoning agent retrieves that history and the confidence score reflects how a similar fix fared
        before. The graph is pruned and degree-capped so it stays a useful map rather than a hairball.
      </P>

      <H2 id="endpoint">Where the models run</H2>
      <P>
        The app is bring-your-own-endpoint. It talks to any OpenAI-compatible model server over a URL and
        an optional API key, so you can point it at your own hosted models, a local runtime, or a managed
        provider. It does not require the project to run its own GPU. Set the two endpoints with{' '}
        <Code>FAST_AGENT_URL</Code> and <Code>REASONING_AGENT_URL</Code>, or aim both at one model for a
        minimal setup.
      </P>

      <P>
        The safety story behind stage five has its own page:{' '}
        <a href="/safety.html" className="font-medium text-primary hover:underline">the constitutional layer</a>.
      </P>

      <CTARow />
    </PageShell>
  )
}
