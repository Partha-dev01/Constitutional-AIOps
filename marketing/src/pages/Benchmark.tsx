import { BarChart3 } from 'lucide-react'
import { PageShell, Pill, H2, P, Stat, CTARow } from '../components/prose'

/**
 * Standalone "Benchmark" page (/benchmark.html, a Vite entry). Reports only the
 * canonical, paper-final figures and is honest about what they mean. Fully
 * static and public-safe, no network calls.
 */

const BASELINES: { model: string; rca: string; delta: string }[] = [
  { model: 'Constitutional AIOps', rca: '82.0%', delta: 'reference' },
  { model: 'Llama-3.3-70B', rca: '71.2%', delta: '+10.8pp' },
  { model: 'DeepSeek-V3.2', rca: '66.9%', delta: '+15.1pp' },
]

export function Benchmark() {
  return (
    <PageShell
      maxWidth="4xl"
      pill={<Pill icon={<BarChart3 className="h-3.5 w-3.5" aria-hidden="true" />}>Benchmark</Pill>}
      title="Measured, not asserted"
      lead="The numbers below come from the project's evaluation corpus and are reported exactly as they appear in the paper. You can re-run the same harness against any endpoint you point the app at."
    >
      <section>
        <div className="grid gap-4 sm:grid-cols-3">
          <Stat value="82.4%" label="Overall accuracy on the labelled corpus" />
          <Stat value="+10.8pp" label={<>Root-cause accuracy over Llama-3.3-70B</>} />
          <Stat value="~1.5x" label="Faster with AWQ quantization" />
        </div>
      </section>

      <H2 id="rca">Root-cause analysis</H2>
      <P>
        Root-cause analysis is where the approach pulls ahead. On the same cases, it scores meaningfully
        higher than two strong open baselines run under identical conditions.
      </P>
      <div className="mb-6 overflow-x-auto rounded-xl border border-border">
        <table className="w-full text-left text-sm">
          <thead className="bg-card/70 text-muted-foreground">
            <tr>
              <th className="px-4 py-3 font-semibold">Model</th>
              <th className="px-4 py-3 font-semibold">RCA accuracy</th>
              <th className="px-4 py-3 font-semibold">Difference</th>
            </tr>
          </thead>
          <tbody>
            {BASELINES.map((row) => (
              <tr key={row.model} className="border-t border-border">
                <td className="px-4 py-3 font-medium text-foreground">{row.model}</td>
                <td className="px-4 py-3 text-muted-foreground">{row.rca}</td>
                <td className="px-4 py-3 text-muted-foreground">{row.delta}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <H2 id="method">How it was measured</H2>
      <P>
        The corpus holds 431 cases drawn from real incident data, of which 357 were scored under the
        reported protocol. An ablated configuration reaches 84.0% overall. These are single-run figures on
        a fixed set, so treat them as a grounded reference rather than a leaderboard claim. The point of
        shipping the harness in the app is that you do not have to take the number on faith: swap in your
        own model and score it against the same cases.
      </P>

      <figure className="m-0">
        <div className="shot-frame">
          <img
            src="/screenshots/benchmark.png"
            alt="The in-app benchmark view scoring a model against the evaluation corpus"
            loading="lazy"
            className="block w-full"
          />
        </div>
        <figcaption className="mt-2 text-center text-xs text-muted-foreground">
          The benchmark harness, running inside the app
        </figcaption>
      </figure>

      <CTARow />
    </PageShell>
  )
}
