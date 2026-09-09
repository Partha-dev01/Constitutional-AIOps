---
title: Chat and Assistant
outline: deep
---

# Chat and Assistant

The Chat page is where you ask questions about your system in plain language. The
same conversation experience is embedded in the [Console](/features/console)
cockpit, so what you learn here applies there too.

![The assistant](/screenshots/chat.png)

## What you see

- **The conversation pane** in the center, where you type a question and read the
  reply.
- **A history sidebar** listing prior conversations so you can pick one back up.
- **Suggested prompts** to get started when you are not sure what to ask.

## How to use it

1. **Ask a question** about your infrastructure, an incident, or a metric. Natural
   language is fine.
2. **Read the reply.** The assistant answers from your system's real context, not
   from generic knowledge alone.
3. **Follow up.** The conversation keeps context, so you can drill in without
   restating everything.
4. **Reopen a past thread** from the history sidebar to continue where you left
   off.

## The constitutional gate is in the loop

Chat is not a bare model wrapper. When a conversation leads toward an action, the
same constitutional validator that governs the rest of the app applies. A
high-confidence, low-risk action can be audited and proceed. An uncertain one
waits for human approval. A low-confidence one only raises an alert. See
[Constitutional Safety](/guide/safety) for how the twelve principles and the
authorization matrix decide.

## Deep links

Chat accepts hand-off parameters so other pages can send you here with context
already loaded. A `?ask=` parameter pre-fills a question, and a `?conversation=`
parameter opens a specific thread. This is how a selection in the Console or a
widget can continue as a conversation.

## Options when you have no server endpoint

If you have not configured an OpenAI-compatible endpoint, you can still try the
assistant with the in-browser local model. It runs entirely on your device via
WebGPU and sends nothing to our servers. See
[Generative UI](/features/generative-ui#in-browser-local-chat-webllm) for how the
local option works and its trade-offs.

::: tip Set an endpoint for full answers
Server-side chat needs a configured endpoint. If a regular tenant lands here
without one, the app routes them to setup first so a request cannot fail with a
400. Configure yours in [Bring Your Own Endpoint](/guide/bring-your-own-endpoint).
:::
