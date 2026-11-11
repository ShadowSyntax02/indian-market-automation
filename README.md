# Indian Market Daily Report — GitHub + cron-job.org + Slack

Run a daily Indian market report with **no always-on server**. GitHub stores the Python code and executes it through Actions; cron-job.org triggers that workflow by HTTP POST.

```
cron-job.org (17:30 IST, Mon–Fri)
        |
        | POST GitHub workflow_dispatch API
        v
GitHub Actions (Python 3.12)
        |
        | Yahoo Finance chart API (unofficial)
        v
Nifty 50, Bank Nifty, BSE Sensex, USD/INR
        |
        v
Slack Incoming Webhook
```

## 1 — Upload to GitHub

Create a **private** GitHub repository named `indian-market-cron-pipeline` and upload this directory, preserving `.github/workflows/daily-market.yml`. You can also run:

```bash
git init
git add .
git commit -m "Add daily Indian market report pipeline"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/indian-market-cron-pipeline.git
git push -u origin main
```

## 2 — Slack secret

1. Create a Slack app with **Incoming Webhooks** enabled: https://api.slack.com/apps
2. Create a webhook for your chosen channel.
3. GitHub repo → Settings → Secrets and variables → Actions → New repository secret.
4. Name: `SLACK_WEBHOOK_URL`; value: your full Slack webhook URL.

Keep webhook URL confidential. Never commit it to Git.

## 3 — Test manually

GitHub repo → Actions → **Daily Indian Market Report** → Run workflow → choose `main`.
Watch logs and confirm Slack receives a message. Market data may be delayed, stale on exchange holidays, or blocked by unofficial-provider rate limiting.

## 4 — Create the cron at https://cron-job.org/

Create a cronjob with:

| Setting | Value |
| --- | --- |
| Title | Indian Market Daily Close |
| URL | `https://api.github.com/repos/YOUR_USERNAME/indian-market-cron-pipeline/actions/workflows/daily-market.yml/dispatches` |
| HTTP Method | POST |
| Request body | `{"ref":"main"}` |
| Content-Type | `application/json` |
| Accept | `application/vnd.github+json` |
| Authorization | `Bearer YOUR_FINE_GRAINED_GITHUB_TOKEN` |
| Timezone | `Asia/Kolkata` |
| Run time | 17:30 |
| Days | Monday–Friday |

To create the GitHub token: GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate. **Restrict to this one repository**, choose repository permission **Actions: Read and write** (the `workflow_dispatch` endpoint requires Actions write), and set an expiry. Put the token only in cron-job.org's secret header configuration; never commit it to the repository. Be aware that cron-job.org holds this GitHub token. Rotate it if exposed.

Expect HTTP **204 No Content** from GitHub when the trigger is accepted. This does **not** mean the workflow succeeded: check the GitHub Actions job and Slack message. cron-job.org has a 30-second HTTP response timeout, but GitHub only accepts the dispatch request and performs the work asynchronously.

### Optional API creation instead of dashboard

The cron-job.org API supports creating jobs via `PUT https://api.cron-job.org/jobs`, with its own cron-job.org API key. Manual dashboard setup is simplest and safer at first.

## 5 — Troubleshooting

- **401/403 on cron-job.org:** GitHub token expired, insufficient `Actions: write` permission, or wrong repository access.
- **404 on cron-job.org:** wrong repo path, workflow filename, default branch, or token has no access.
- **204 but no Slack message:** check Actions logs; GitHub workflow executes separately.
- **Market-data 429 / blocked:** unofficial Yahoo chart endpoint may rate limit. Replace it with a licensed/reliable data provider for production.
- **No report on a holiday:** latest prior close is shown and marked stale if the Indian market's latest data date precedes the current IST date. Scheduled job still runs on weekday holidays.
- **No USD rate:** the `INR=X` Yahoo ticker is used; inspect provider data for availability and quote convention.

## Run locally (dry run)

```bash
python3 -m unittest discover -s tests -v
DRY_RUN=1 python3 market_report.py
```

## Data caveat

The project uses Yahoo Finance's **unofficial** chart API and can fail or deliver delayed data. This is a personal experimental reporting pipeline, not a guaranteed live/official market-price source. `USD/INR` is a market quote rather than an RBI reference rate. Do not use these values for trading execution.
