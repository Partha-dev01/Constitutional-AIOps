/**
 * Minimal end-to-end example for the Constitutional AIOps TypeScript client.
 * Run against an instance you can reach (Node 18+, global fetch).
 *
 *   AIOPS_URL=https://your-instance.example.com AIOPS_TOKEN=... npx tsx examples/quickstart.ts
 */

import { AIOpsClient, ConstitutionalRefusal } from '../src/index'

async function main(): Promise<void> {
  const client = new AIOpsClient({
    baseUrl: process.env.AIOPS_URL ?? 'http://localhost:8000',
    token: process.env.AIOPS_TOKEN,
  })

  console.log('Recent incidents:')
  for await (const incident of client.paginate('/incidents/', {}, 25)) {
    const inc = incident as { id?: string; severity?: string; title?: string }
    console.log(`  ${inc.id ?? '?'}  ${inc.severity ?? '?'}  ${inc.title ?? ''}`)
  }

  const pending = (await client.pendingActions()) as { count?: number }
  console.log(`\nPending actions: ${pending.count ?? 0}`)

  // A few of the 0.2.0 read helpers.
  console.log('Action stats:', await client.actionStats())
  console.log('Episodic graph:', await client.graphStats())
  const unread = (await client.unreadCount()) as { count?: number }
  console.log(`Unread notifications: ${unread.count ?? 0}`)

  // Generative UI (0.3.0): opt-in, cost-fenced explanations of computed data.
  await client.setInsightPreferences({ enabled: true })
  const explained = (await client.explain('anomaly', { count: 1, top: [{ series: 'cpu', z: 3.9 }] })) as {
    available?: boolean
    explanation?: string
    reason?: string
  }
  console.log('Explain (anomaly):', explained.available ? explained.explanation : explained.reason)

  // The MCP tool registry (0.3.0) — the same tools the copilots use.
  const toolList = (await client.tools()) as { total?: number }
  console.log(`Tools available: ${toolList.total ?? 0}`)

  console.log('\nChat:')
  try {
    const result = await client.streamChat('Summarize the current state of the system.', {
      onDelta: (token) => process.stdout.write(token),
    })
    const message = result.message as { content?: string } | undefined
    console.log('\n---\n' + (message?.content ?? ''))
  } catch (error) {
    if (error instanceof ConstitutionalRefusal) console.log('gate refusal:', error.errorCode)
    else throw error
  }
}

void main()
