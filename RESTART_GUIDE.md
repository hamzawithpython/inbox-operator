# Inbox Operator — Restart Guide

A checklist for getting the project running again after time away. Work top to bottom.

---

## 0. Prerequisites (should already be installed)

Open **VS Code**, then open the integrated terminal (`` Ctrl+` ``). Verify the tools:

```powershell
docker --version
docker compose version
git --version
gh --version
```

If **Docker Desktop** isn't running, open it from the Start menu and wait until the whale icon is steady ("Engine running"). Nothing below works without it.

---

## 1. Go to the project and pull latest

```powershell
cd C:\Users\Admin\Desktop\portfolio\inbox-operator
git checkout main
git pull origin main
```

Confirm you're in the right place and on a clean branch:

```powershell
pwd          # should end in \inbox-operator
git status   # should say "working tree clean"
git branch   # confirm which branch you're on
```

If starting **new work**, branch off main first:

```powershell
git checkout -b feat/<your-feature-name>
git push -u origin feat/<your-feature-name>
```

---

## 2. Recreate the secret files (NOT in git — you must recreate these)

These are gitignored, so they won't be on a fresh clone. If they're missing, recreate them with your **real** keys.

**Root `.env`** (used by docker-compose to pass the Groq key to the RAG service):

```powershell
"GROQ_API_KEY=gsk_YOUR_REAL_GROQ_KEY" | Out-File -FilePath .env -Encoding ascii
```

**RAG service `.env`** (only needed if running the RAG service outside Docker, e.g. local dev):

```powershell
"GROQ_API_KEY=gsk_YOUR_REAL_GROQ_KEY" | Out-File -FilePath rag-service\.env -Encoding ascii
```

Verify (should show your real key, no placeholder, no weird leading characters):

```powershell
Get-Content .env
```

> Use `-Encoding ascii`, NOT `utf8` — `utf8` adds a BOM that breaks `.env` parsing.

Confirm secrets are NOT tracked:

```powershell
git status   # .env and rag-service/.env must NOT appear
```

---

## 3. Start the containers (n8n + RAG service)

```powershell
docker compose up -d --build
```

The `--build` rebuilds the RAG image (needed if the key/code changed; first build takes a few minutes — it installs torch, downloads the embedding model, and builds the vector store). On later restarts where nothing changed, you can drop `--build`:

```powershell
docker compose up -d
```

Confirm BOTH containers are up:

```powershell
docker compose ps
```

Expected: `inbox-operator-n8n` (Up, port 5678) and `inbox-operator-rag` (Up, port 8000).

---

## 4. Verify the RAG service is healthy

```powershell
curl.exe http://localhost:8000/health
```

Expected: `{"status":"ok","documents":15}`

Quick grounded-reply check (optional):

```powershell
'{"subject":"Password help","body":"I forgot my password, how do I reset it?","from_name":"Alex"}' | Out-File -Encoding ascii test_req.json
curl.exe -X POST http://localhost:8000/support-reply -H "Content-Type: application/json" -d "@test_req.json"
Remove-Item test_req.json
```

Expected: a JSON `draft` describing the password-reset steps, with `sources` listing the reset FAQ.

> If the RAG container keeps restarting: `docker compose logs rag-service`. Most common cause is a missing/placeholder `GROQ_API_KEY` in the root `.env`.

---

## 5. Open n8n and re-check credentials

Open **http://localhost:5678** in Chrome. Log in with your local n8n owner account.

n8n stores credentials in the `n8n_data/` volume (gitignored), so on the SAME machine they persist. If credentials are missing (fresh machine / volume reset), reconnect them under **Credentials**:

| Credential | Type | Notes |
|---|---|---|
| Gmail - test2 | Gmail OAuth2 | account `hamza.asif6182.2@gmail.com`; redirect `http://localhost:5678/rest/oauth2-credential/callback` |
| Groq API | Header Auth | `Authorization` = `Bearer gsk_...` |
| Slack - Inbox Operator | Slack API | bot token `xoxb-...` |
| Google Sheets - test2 | Google Sheets OAuth2 | same OAuth client as Gmail; Sheets API enabled |

If the workflow itself is missing, import it: **Workflows → Import from File →** `workflows/inbox-operator.json`.

---

## 6. Smoke test the full workflow

Send a test email **from** `hamjaa.jee@gmail.com` **to** `hamza.asif6182.2@gmail.com` (test2), then in n8n:

1. Click **Gmail Trigger → Execute step** (confirm it shows your test email).
2. Click **Execute workflow**.
3. For a support/finance/other email: approval email lands in test2 → click **APPROVE** → reply delivered to hamjaa.jee.
4. Check the Google Sheet (`Inbox Operator Log`) for a new audit row.

Test emails by category:

| Subject | Body | Routes to |
|---|---|---|
| `Password help` | I forgot my password, how do I reset it? | Customer Support (RAG) |
| `Invoice #4421` | When is invoice 4421 due? | Finance |
| `50% off sale` | Huge weekend sale, 50% off!!! | Promotion (auto-filed) |
| `URGENT system down` | Production is down, need help now! | High Priority (Slack) |
| `Coffee next week?` | Want to grab coffee next week? | Other |

---

## 7. Stopping work

Stop the containers (keeps data/volumes):

```powershell
docker compose down
```

To also wipe the n8n data volume (DANGER — deletes credentials & local workflow state; only if you want a clean reset):

```powershell
docker compose down -v
```

---

## 8. Commit discipline reminder

- Branch per feature: `feat/<name>`; keep `main` deployable.
- Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`.
- Before committing the workflow, re-export from n8n (⋯ → Download), move into `workflows/inbox-operator.json`, then **scrub for secrets**:

```powershell
Select-String -Path ".\workflows\inbox-operator.json" -Pattern "gsk_","Bearer","clientSecret","refreshToken","accessToken","xoxb"
```

Must return nothing before you `git add` / `commit` / `push`.

---

## Quick reference — known gotchas

- **n8n fields**: Fixed (plain text, no `=`) vs Expression (toggle on, `{{ }}`). JSON-body fields must be in Expression mode, and the live preview should start with `{`, not `={`.
- **Reach the RAG service from n8n** by container name: `http://rag-service:8000` — NOT `localhost` (inside n8n's container, localhost is n8n).
- **Gmail labels** are referenced by internal ID — don't delete/recreate the `Promotions-Auto` label or the node reference breaks.
- **PowerShell `Out-File`**: use `-Encoding ascii` for `.env`/config files (avoids BOM).
- **Outlook/Exchange senders** mask their address behind a privacy relay — replies bounce. Test with normal Gmail senders.
- **Port conflicts**: 5678 (n8n), 8000 (RAG). Stop stray processes or change the host port mapping in `docker-compose.yml`.

---

## Service map

| Service | URL | Container |
|---|---|---|
| n8n editor | http://localhost:5678 | inbox-operator-n8n |
| RAG service | http://localhost:8000 | inbox-operator-rag |
| RAG health | http://localhost:8000/health | — |

Accounts: **test2** `hamza.asif6182.2@gmail.com` (workflow inbox + approvals), **customer** `hamjaa.jee@gmail.com` (send tests from here).
