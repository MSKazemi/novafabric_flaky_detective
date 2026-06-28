# Deploying the Flaky Detective API

The image is public on Docker Hub: **`kazemi/flaky-detective:latest`** (listens on port **8000**).
Goal: a permanent public HTTPS URL that UiPath's cloud agent can call.

## Option A — Render (recommended, free)
1. https://render.com → sign up / log in.
2. **New +** → **Web Service** → **Existing image**.
3. Image URL: `docker.io/kazemi/flaky-detective:latest`
4. Instance type: **Free**. Region: Frankfurt (EU, closest).
5. **Port: 8000** (Render → Advanced → set if asked; the app listens on 8000).
6. Create → wait for "Live". You get a URL like `https://flaky-detective.onrender.com`.
7. Verify: open `https://<your-url>/health` → `{"status":"ok",...}`.

> ⚠️ Render free services **cold-start** (sleep after ~15 min idle, ~50s wake). Before
> recording the demo or running the UiPath agent, hit `/health` once to wake it.

## Option B — Railway (alternative)
1. https://railway.app → New Project → **Deploy a Docker Image**.
2. Image: `kazemi/flaky-detective:latest`. Set port **8000**. Deploy → copy the public URL.

## After you have the URL
1. Smoke-test it:
   ```bash
   curl https://<your-url>/health
   curl https://<your-url>/analyze -H 'content-type: application/json' \
     -d '{"baseline_capsule":"fixture:baseline","current_capsule":"fixture:flaky"}'   # -> flaky
   ```
2. Give the URL to the UiPath connector step: edit `deploy/openapi-3.0.json` →
   set the `servers[0].url` to `https://<your-url>` (so the connector calls the live API),
   then import it in UiPath Integration Service.

## Image details
- Base: `python:3.12-slim`, ~549 MB
- Installs `flaky-detective` + `novafabric>=0.58` + FastAPI/uvicorn from PyPI
- Run locally: `docker run --rm -p 8000:8000 kazemi/flaky-detective:latest`
