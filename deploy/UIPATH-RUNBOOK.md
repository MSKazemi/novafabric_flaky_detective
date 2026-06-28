# UiPath build runbook — connector + agent

Do these in UiPath Automation Cloud (org `novafabricagenthack`) after the API is deployed and you
have its public URL `https://<API>`. Prereqs: `deploy/openapi-3.0.json` (set its `servers[0].url`
to `https://<API>` first).

## Part 1 — Integration Service custom connector
1. App launcher (⠿) → **Integration Service**.
2. **Connectors** → **Build a connector** → **Start from an API definition / Import OpenAPI**.
3. Upload **`deploy/openapi-3.0.json`**. Name it **NovaFabric Flaky Detective**.
4. Base URL: `https://<API>`. Auth: **No auth** (the demo API is open).
5. Confirm the **POST /analyze** operation imported (request: `baseline_capsule`,
   `current_capsule`; response: `verdict`, `confidence`, `differing_step`, `remediation`, `signal`).
6. **Save / Publish** the connector. Create a **Connection** to it (no credentials needed).
7. Test the connection: run `/analyze` with `fixture:baseline` + `fixture:flaky` → expect `flaky`.

## Part 2 — Agent Builder agent
1. App launcher (⠿) → **Agents** (Agent Builder) → **New agent** → name **Flaky Detective**.
2. **Instructions / System prompt:** paste from `deploy/agent-system-prompt.md`.
3. **Model:** pick the available default (e.g. gpt-4o / the cloud's default LLM).
4. **Tools → Add tool →** select the **NovaFabric Flaky Detective** connector's **analyzeRuns
   (POST /analyze)** operation. Map inputs: `baseline_capsule`, `current_capsule`.
5. **Test panel** — try these three prompts; the agent should call the tool and report:
   - "Compare fixture:baseline against fixture:flaky." → **flaky**
   - "Compare fixture:baseline against fixture:regression." → **regression**
   - "Compare fixture:baseline against fixture:baseline." → **pass**
6. **Publish** the agent so it has a stable run surface (for the demo + the "UiPath Labs link"
   field on Devpost).

## Part 3 — (optional, strengthens the testing story) Test Manager
- App launcher → **Test Manager** → create a project "Flaky Detective" → add 3 test cases
  (flaky / regression / pass) → attach the agent verdict as the test result. Time-box this; it's
  a bonus for the "agentic testing" narrative, not required for a working submission.

## What to capture for Devpost / demo
- The **agent run URL** (Automation Cloud) → goes in Devpost "UiPath Labs link" field.
- Screenshots: connector operation, agent test panel showing a `flaky` and a `regression` verdict.
- These feed the demo video (`docs/DEMO-SCRIPT.md`) and the Devpost gallery.
