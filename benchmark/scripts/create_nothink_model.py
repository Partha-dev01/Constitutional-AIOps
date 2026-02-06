#!/usr/bin/env python3
"""
Create a custom qwen3-4b-nothink model on Jarvis Labs Ollama.

This model is identical to qwen3:4b but with thinking mode permanently disabled
by removing the <think> tag from the template. This reduces annotation latency
from ~28s to ~5-8s by eliminating chain-of-thought overhead.

Usage: python benchmark/scripts/create_nothink_model.py
"""

import httpx
import json
import sys
import time

JARVIS_URL = "https://96c3f93672471.notebooks.jarvislabs.net"
MODEL_NAME = "qwen3-4b-nothink"

# The original Qwen3 template ends with:
#   {{- if and (ne .Role "assistant") $last }}<|im_start|>assistant
#   <think>
#   {{ end }}
#
# Our modified template ends with:
#   {{- if and (ne .Role "assistant") $last }}<|im_start|>assistant
#   {{ end }}
#
# Also removed the thinking output section from assistant messages.

NOTHINK_TEMPLATE = """{{- $lastUserIdx := -1 -}}
{{- range $idx, $msg := .Messages -}}
{{- if eq $msg.Role "user" }}{{ $lastUserIdx = $idx }}{{ end -}}
{{- end }}
{{- if or .System .Tools }}<|im_start|>system
{{ if .System }}{{ .System }}

{{ end }}
{{- if .Tools }}# Tools

You may call one or more functions to assist with the user query.

You are provided with function signatures within <tools></tools> XML tags:
<tools>
{{- range .Tools }}
{"type": "function", "function": {{ .Function }}}
{{- end }}
</tools>

For each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:
<tool_call>
{"name": <function-name>, "arguments": <args-json-object>}
</tool_call>
{{- end -}}
<|im_end|>
{{ end }}
{{- range $i, $_ := .Messages }}
{{- $last := eq (len (slice $.Messages $i)) 1 -}}
{{- if eq .Role "user" }}<|im_start|>user
{{ .Content }}<|im_end|>
{{ else if eq .Role "assistant" }}<|im_start|>assistant
{{ if .Content }}{{ .Content }}{{ end }}
{{- if .ToolCalls }}
{{- range .ToolCalls }}
<tool_call>
{"name": "{{ .Function.Name }}", "arguments": {{ .Function.Arguments }}}
</tool_call>
{{- end }}
{{- end }}{{ if not $last }}<|im_end|>
{{ end }}
{{- else if eq .Role "tool" }}<|im_start|>user
<tool_response>
{{ .Content }}
</tool_response><|im_end|>
{{ end }}
{{- if and (ne .Role "assistant") $last }}<|im_start|>assistant
{{ end }}
{{- end }}"""


def main():
    print("=" * 60)
    print(f"Creating custom model: {MODEL_NAME}")
    print(f"Jarvis Labs: {JARVIS_URL}")
    print("=" * 60)

    # Step 0: Delete existing model if present
    print("\n[0/4] Deleting existing model (if any)...")
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.request(
                "DELETE",
                f"{JARVIS_URL}/api/delete",
                json={"model": MODEL_NAME},
            )
            print(f"  Delete status: {resp.status_code}")
    except Exception:
        pass  # Model might not exist yet

    # Step 1: Try creating with 'from' + separate template field
    print("\n[1/4] Creating model with 'from' + template...")
    start = time.perf_counter()

    try:
        with httpx.Client(timeout=300.0) as client:
            # Try newer API format first
            payload = {
                "model": MODEL_NAME,
                "from": "qwen3:4b",
                "template": NOTHINK_TEMPLATE,
                "parameters": {
                    "num_ctx": 8192,
                    "temperature": 0.6,
                    "top_k": 20,
                    "top_p": 0.95,
                },
            }
            response = client.post(
                f"{JARVIS_URL}/api/create",
                json=payload,
            )
            elapsed = time.perf_counter() - start
            lines = response.text.strip().split("\n")
            for line in lines:
                print(f"  {line}")
            print(f"  Elapsed: {elapsed:.1f}s")

            if response.status_code != 200:
                print(f"\n[WARN] Template field may not be supported, trying modelfile format...")
                # Fallback: use modelfile string format
                modelfile = f'FROM qwen3:4b\nPARAMETER num_ctx 8192\nTEMPLATE """{NOTHINK_TEMPLATE}"""'
                response = client.post(
                    f"{JARVIS_URL}/api/create",
                    json={"name": MODEL_NAME, "modelfile": modelfile},
                )
                lines = response.text.strip().split("\n")
                for line in lines:
                    print(f"  {line}")

    except Exception as e:
        print(f"\n[FAIL] Request failed: {e}")
        return 1

    # Step 2: Verify model exists and template is correct
    print("\n[2/4] Verifying model template...")
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{JARVIS_URL}/api/show",
                json={"model": MODEL_NAME},
            )
            data = response.json()
            template = data.get("template", "")
            has_think = "<think>" in template
            print(f"  Template length: {len(template)} chars")
            print(f"  Has <think> tag: {has_think}")
            print(f"  Last 150 chars: {repr(template[-150:])}")

            if has_think:
                print(f"  [FAIL] Template STILL has <think> - thinking not disabled!")
                return 1
            else:
                print(f"  [PASS] Template does NOT have <think> - thinking disabled!")

    except Exception as e:
        print(f"  [FAIL] Verification failed: {e}")
        return 1

    # Step 3: Verify model shows in list
    print("\n[3/4] Checking model list...")
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{JARVIS_URL}/api/tags")
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            found = MODEL_NAME in model_names or f"{MODEL_NAME}:latest" in model_names
            print(f"  Models: {model_names}")
            print(f"  {MODEL_NAME} found: {found}")
    except Exception as e:
        print(f"  [FAIL] {e}")

    # Step 4: Quick functional test
    print("\n[4/4] Quick test (single completion)...")
    try:
        with httpx.Client(timeout=120.0) as client:
            start = time.perf_counter()
            response = client.post(
                f"{JARVIS_URL}/v1/chat/completions",
                json={
                    "model": MODEL_NAME,
                    "messages": [
                        {"role": "user", "content": 'Say OK in JSON: {"status": "ok"}'}
                    ],
                    "max_tokens": 100,
                    "temperature": 0.0,
                },
            )
            elapsed = (time.perf_counter() - start) * 1000
            data = response.json()
            msg = data["choices"][0]["message"]
            content = msg.get("content", "")
            reasoning = msg.get("reasoning", "")
            usage = data.get("usage", {})

            print(f"  Latency: {elapsed:.0f}ms")
            print(f"  Tokens: prompt={usage.get('prompt_tokens', 0)}, completion={usage.get('completion_tokens', 0)}")
            print(f"  Content ({len(content)} chars): {repr(content[:300])}")
            print(f"  Reasoning ({len(reasoning)} chars): {repr(reasoning[:300])}")

            if content and not reasoning:
                print(f"\n  [PASS] No-think model works! Direct output, no reasoning overhead.")
                print(f"  Expected latency improvement: ~28s -> {elapsed/1000:.1f}s")
            elif content and reasoning:
                print(f"\n  [WARN] Both fields populated. Thinking may still be partially active.")
            elif not content and reasoning:
                print(f"\n  [FAIL] Content empty, reasoning populated. Thinking NOT disabled.")
            else:
                print(f"\n  [FAIL] Both empty.")

    except Exception as e:
        print(f"  [FAIL] Quick test failed: {e}")
        return 1

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
