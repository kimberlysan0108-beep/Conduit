# Conduit — full source repository

**Risk-aware customer resolution, with deterministic control over business actions.**

A runnable research prototype based on Kimberly Sánchez's Conduit internship brief. Python / FastAPI, SQLAlchemy / PostgreSQL, Redis worker, React / TypeScript console, Stripe **test-only** adapter, optional LLM planner and reviewer, policy retrieval, 500-case benchmark, tests and CI.


## Start here: this is the full source package

This repository includes the Python backend, backend-connected React operator console,
database models and migration, simulator, policy and authorization engines, provider
adapters, benchmark fixtures/runners, automated tests, CI, Docker, and documentation.
It also includes the corrected standalone browser demo from the conversation.

### Choose what you want to run

| Entry point | What it runs | How |
|---|---|---|
| Root `index.html` | The latest interactive browser demo, including navigation and investigation fixes | Open it or publish the root on GitHub Pages |
| `frontend/demo/preview-source.html` | Editable source fragment for that browser demo | Source reference; the root index is the standalone export |
| `frontend/operator-console/` + `backend/` | The React console connected to the actual FastAPI/SQL application | Follow the Docker instructions below |

The two frontends are different implementations: the root demo is a browser simulation;
the React console uses backend APIs. The recent visual refinements and demo controls are
in the standalone demo; they have not been ported into the backend-connected React UI.
All source for both is included. The backend-connected application runs with simulator
payments and a deterministic planner by default, without Stripe or paid AI credentials.

GitHub Pages can publish root `index.html`, but cannot execute Python or PostgreSQL.
Uploading this repository to GitHub stores the full source; run Docker locally or use
backend-capable hosting to run the full application. No public backend deployment or
live-provider credentials are included.

Unzip this package and add the entire extracted folder through GitHub Desktop. Publish
all the source together; do not upload only `index.html` if you want the full repository.
The archive excludes installed dependencies, environment secrets and local databases.
`npm ci` and `pip install` recreate the dependencies when you run the project.

## Start the entire local demo

Install Docker Desktop, open a terminal **inside this folder**, then:

```bash
cp .env.example .env
docker compose up --build
```

Open **http://localhost:3000**. API documentation: **http://localhost:8000/docs**.

1. Choose **Customer**, enter `local-customer-change-me`, and connect.
2. Submit the prefilled refund request for `pay_demo`.
3. Inspect the proposed $89 refund, then click **Confirm**.
4. The case becomes `RESPOND` only after verification. Open **Trajectory**.
5. Reload the page and connect as **Operator** using `local-operator-change-me` to inspect all cases. These role selections change the UI only; the backend derives actual permissions from the token.

The seeded subscription is `sub_demo`; the order is `ord_demo`; the customer is `cus_demo`. The order has an authoritative verified-missing flag. After a refund succeeds, new refund cases cannot spend its balance again. To reset **only this demo's data**, run `docker compose down -v` and start again. That command deletes the demo database volume.

These default tokens are for a loopback-only demo. Do not publicly expose this configuration.

## Without Docker

Python 3.11+ and Node 22+:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
python -m alembic upgrade head
python -m backend.seed
python -m uvicorn backend.main:app --reload
```

In a second terminal:

```bash
cd frontend/operator-console
npm ci
npm run dev -- --host 127.0.0.1
```

Open the local URL printed by Vite. Without `.env`, the backend defaults to SQLite and simulator payments. If you copied the Docker `.env`, change `DATABASE_URL=sqlite:///./conduit.db` and clear `REDIS_URL` for this route. On Windows, activate with `.venv\Scripts\activate` instead of `source`.

## Run validation and reproduce experiments

```bash
python -m pytest -q
python -m benchmark.generators.generate --count 500
python -m benchmark.evaluators.run --variant all
python -m benchmark.evaluators.retrieval
python scripts/check_benchmark.py
cd frontend/operator-console && npm run build
```

Measured results and limitations are in **EVALUATION.md**. Raw results and per-case trajectories are in `docs/experiments/*.json`. A/B ablations exist only in the offline evaluator; no API or environment switch disables policy enforcement.

## Optional LLM and reviewer

Set `PLANNER=llm`, `LLM_API_KEY`, `LLM_MODEL` and a compatible `LLM_BASE_URL`. The model produces a validated intent and confidence, never an authorization or arbitrary tool call. To compare 2–4 models:

```bash
python -m benchmark.evaluators.run --variant C --models MODEL_1 MODEL_2
python -m benchmark.evaluators.run --variant C --models MODEL_1 --reviewer REVIEWER_MODEL
```

Use your provider's actual model IDs. No model API was called for the supplied measurements. Model failures escalate. A reviewer may veto or escalate high-risk proposals; it cannot relax policy or authority. Token use is recorded; API cost remains `null` until you apply your provider's actual prices. `EMBEDDING_MODEL` enables API embedding retrieval; offline mode explicitly uses BM25 + TF-IDF cosine, not semantic embeddings.

## Stripe test mode

Set a `sk_test_…` key, run `python scripts/stripe_fixture.py` against fresh seed data, then set `PAYMENT_PROVIDER=stripe`. Set `STRIPE_WEBHOOK_SECRET` to your test endpoint's signing secret. Route Stripe **test** events to `/webhooks/stripe` with Stripe's development tooling. Supported events: payment-intent succeeded/failed; refund created/updated/failed; subscription deleted.

The refund adapter, signature validation, event replay and local ledger are implemented. Provider behavior is covered by mock and signed-fixture tests, **not a live Stripe sandbox run**. Subscription, order and credit mutations remain local simulation even in Stripe payment mode. Do not interpret them as Stripe subscription updates. Only an explicitly imported test subscription using its exact Stripe ID receives deletion events.

## Repository map

- `backend/agent/`: explicit workflow, constrained planners and reviewer.
- `backend/policies/`, `risk/`: deterministic eligibility, graduated authority and retrieval.
- `backend/payments/`, `webhooks/`: test adapter, durable events and replay.
- `frontend/operator-console/`: responsive customer/operator console.
- `benchmark/`: 500 fixtures, generation and independent business-state evaluator.
- `tests/`: unit, property, integration, E2E and fault tests.
- `docs/designs/`: required design documents.
- `docs/experiments/`: measured ablations and retrieval results.
- `ARCHITECTURE.md`, `EVALUATION.md`, `docs/TECHNICAL-REPORT.md`.
- `docs/presentation.html`: keyboard-navigable final presentation.

## What is and is not complete

The local prototype, console, benchmark, tests, migrations and CI configuration are included. It supports billing refunds/approved credits, subscription cancellation, and order status/replacement/address correction. Unsupported requests ask for clarification; upgrade/downgrade and failed-payment recovery are intentionally outside the implemented subset.

There is **no publicly deployed service**, real-organization shadow study, live LLM/reviewer comparison, or live Stripe test run in this delivery. Those need deployment infrastructure, credentials and/or operator data. Docker deployment configuration and experiment commands are provided; these prerequisites are not fabricated as completed work. This is a production-*style* prototype, not a production-certified payments system.

## Put it on GitHub

Upload the extracted **contents of this folder** using GitHub Desktop: **File → Add Local Repository → Create a Repository → Publish repository**. Do not add `node_modules`, `.venv`, `.env`, or a local database. They are excluded by `.gitignore` and are not in the delivery ZIP. The dependency installers recreate them.
