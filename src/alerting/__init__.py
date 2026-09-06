"""
Constitutional AIOps - remote alerting (Track 1).

Pushes operational notifications to a user-configured chat channel (Telegram or
Matrix) so an operator does not have to be watching the app to hear about an
incident. It is the chat-channel sibling of ``src.notifications.webhook``: both
hang off the single ``notify()`` choke point, both are admin-scoped, both deliver
fire-and-forget on short-lived daemon threads (NO poller / worker, so it never
fights the sleep-when-idle deployment), and both swallow their own errors so a
delivery problem can never break the request that raised the alert.

This package covers the OUTBOUND half only (T1a Telegram + T1b Matrix). Inbound
ChatOps (the always-on relay Lambda) is a separate, later, infra-gated phase.

Secrets (the Telegram bot token, the Matrix access token) are Fernet-encrypted
at rest via ``src.auth.crypto`` and never returned by the API (only a boolean
"is set" flag). Routing ids (chat id, homeserver, room id) stay plaintext.
"""
