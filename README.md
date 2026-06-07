# Inbox Operator

**AI email triage & draft automation in n8n — AI proposes, human approves, send, log.**

An n8n workflow that ingests incoming email, uses an LLM to classify intent and draft a reply, routes the draft into a human-approval queue, sends only after approval, and logs every action. The point is the guardrail pattern: **AI proposes → human approves → send → log** — nothing auto-sends.

## Architecture

_(diagram coming in a later phase)_

## Tech Stack
- **n8n** (self-hosted via Docker) — workflow orchestration
- **Gmail API** (OAuth2) — email source + draft/send
- **Groq** (Llama 3.x, OpenAI-compatible API) — classification + drafting
- Docker / docker-compose

## Setup
1. Install Docker Desktop.
2. Clone this repo, then `docker compose up -d`.
3. Open http://localhost:5678 and create a local owner account.
4. Configure Gmail OAuth2 and Groq credentials inside n8n (see `.env.example`).
5. Import the workflow from `workflows/`.

## Live Demo
_(walkthrough recording + screenshots coming once built)_

## Technical Decisions
- **Self-hosted n8n over Cloud:** owned artifact, committable compose file, no trial expiry.
- **Groq over OpenAI:** free tier, fast, OpenAI-compatible.
- **Drafts not auto-send:** core guardrail — human stays in the loop.

## What Didn'\''t Work / Lessons
_(filled in as we go)_
