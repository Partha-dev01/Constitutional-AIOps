import { ChatPane } from '../components/chat/ChatPane'

/**
 * The full Chat page. All conversation logic lives in the shared ChatPane (so
 * the Console cockpit can embed the same experience); this page renders its
 * `page` variant — heading, history sidebar and the ?ask / ?conversation
 * hand-off params that the e2e contracts depend on.
 */
export function Chat() {
  return <ChatPane variant="page" />
}
