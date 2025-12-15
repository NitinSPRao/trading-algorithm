# GitHub Actions Trading Setup Guide

This guide shows you how to run your trading algorithm automatically using GitHub Actions at market open (9:30 AM ET) every weekday.

## Why GitHub Actions?

✅ **Free** - GitHub provides free compute for public repos (2,000 minutes/month private repos)
✅ **Reliable** - Runs in the cloud, no need for your computer to be on
✅ **Automated** - Set it and forget it
✅ **Logs** - Automatic logging and artifact storage
✅ **Monitoring** - Email notifications on success/failure

## Prerequisites

1. GitHub account (free)
2. Your trading algorithm repository on GitHub
3. Alpaca API credentials (paper or live trading)

## Setup Steps

### 1. Push Your Code to GitHub

If you haven't already:

```bash
cd /Users/nitinrao/Downloads/trading-algorithm

# Initialize git (if not already done)
git init
git add .
git commit -m "Add trading algorithm with GitHub Actions"

# Add remote and push
git remote add origin https://github.com/NitinSPRao/trading-algorithm.git
git push -u origin main
```

### 2. Add API Keys as GitHub Secrets

**This is critical for security!** Never commit API keys to your repository.

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

Add these secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `ALPACA_API_KEY` | Your Alpaca API key | From Alpaca dashboard |
| `ALPACA_SECRET_KEY` | Your Alpaca secret key | From Alpaca dashboard |
| `ALPACA_BASE_URL` | `https://paper-api.alpaca.markets` | For paper trading |
| `POSITION_SIZE_LIMIT` | `0.95` | Use 95% of buying power |

**For live trading**, change `ALPACA_BASE_URL` to `https://api.alpaca.markets`

### 3. Choose Your Workflow

You have two workflow options:

#### Option A: Simple Workflow (Recommended)
- File: `.github/workflows/daily-trading.yml`
- Single cron schedule
- Manual DST adjustment needed twice a year

#### Option B: DST-Aware Workflow
- File: `.github/workflows/daily-trading-dst.yml`
- Automatically handles Daylight Saving Time
- Two cron schedules (switches automatically)

**Recommended:** Use Option B (DST-Aware) for fully automated operation.

### 4. Enable GitHub Actions

1. Go to your repository on GitHub
2. Click the **Actions** tab
3. You should see your workflow(s)
4. GitHub Actions should be enabled by default

### 5. Test the Workflow Manually

Before waiting for the scheduled run:

1. Go to **Actions** tab
2. Click on your workflow name (e.g., "Daily Trading Algorithm (DST-Aware)")
3. Click **Run workflow** dropdown
4. Click **Run workflow** button
5. Watch it execute in real-time!

## How It Works

### Schedule Times

The workflow runs at **9:30 AM Eastern Time** every weekday (Monday-Friday).

**DST-Aware Schedule:**
- **Standard Time** (Nov-Mar): `30 14 * * 1-5` (2:30 PM UTC = 9:30 AM ET)
- **Daylight Saving** (Mar-Nov): `30 13 * * 1-5` (1:30 PM UTC = 9:30 AM EDT)

### What Happens Each Run

1. ✅ **Checkout code** - Gets latest version from your repo
2. ✅ **Set up Python** - Installs Python 3.11
3. ✅ **Install dependencies** - Installs required packages
4. ✅ **Check time** - Verifies it's a trading day
5. ✅ **Run trading algorithm** - Executes your strategy
6. ✅ **Upload logs** - Saves logs as artifacts (90 days)
7. ✅ **Create summary** - Shows results in Actions UI

### Execution Flow

```
9:30 AM ET ──> GitHub Actions Triggered
                      │
                      ├─> Fetch latest code
                      ├─> Install Python & dependencies
                      ├─> Check if market is open
                      ├─> Run trading algorithm
                      │   ├─> Get TECL & VIX prices
                      │   ├─> Calculate indicators
                      │   ├─> Check buy/sell signals
                      │   └─> Execute trades (if any)
                      ├─> Upload logs
                      └─> Send notification
```

## Monitoring

### View Logs

1. Go to **Actions** tab
2. Click on a workflow run
3. Click on the job name (e.g., "trade")
4. Expand steps to see logs
5. Download artifacts for full logs

### Download Historical Logs

1. Go to completed workflow run
2. Scroll to bottom "Artifacts" section
3. Download `trading-logs-XXX.zip`
4. Extract and review `daily_trading.log`

### Check Last Execution

```bash
# View recent runs from command line (requires GitHub CLI)
gh run list --workflow=daily-trading-dst.yml --limit 10
```

## Cost Considerations

### GitHub Actions Minutes

**Free tier limits:**
- Public repositories: **Unlimited** ✅
- Private repositories: **2,000 minutes/month** (plenty for daily trading)

**Your usage:**
- Each run: ~2-3 minutes
- Daily runs: ~60-75 minutes/month
- Well within free tier! ✅

### Making It More Efficient

The workflow already includes:
- ✅ Dependency caching (faster installs)
- ✅ 15-minute timeout (prevents stuck jobs)
- ✅ Conditional execution (skips weekends)

## Advanced Features

### Adding Notifications

Add to the workflow to get notified of trades:

#### Slack Notification

Add this step after trading:

```yaml
- name: Notify Slack
  if: always()
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {
        "text": "Trading algorithm completed: ${{ job.status }}"
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

#### Email Notification

GitHub automatically sends email on workflow failure. To enable:
1. Go to **Settings** → **Notifications**
2. Enable "Actions" notifications

#### Discord Notification

```yaml
- name: Discord Notification
  if: always()
  uses: sarisia/actions-status-discord@v1
  with:
    webhook: ${{ secrets.DISCORD_WEBHOOK }}
    title: "Trading Algorithm"
    description: "Status: ${{ job.status }}"
```

### Running Multiple Strategies

You can run different strategies by creating multiple workflow files:

```
.github/workflows/
├── tecl-strategy.yml       # Your TECL strategy
├── spy-strategy.yml        # Different stock
└── crypto-strategy.yml     # Cryptocurrency
```

### Dry Run Mode

The DST-Aware workflow supports manual dry runs:

1. Go to **Actions** → workflow
2. Click **Run workflow**
3. Set `dry_run` to `true`
4. See what the algorithm would do without actual trades

## Troubleshooting

### Workflow Not Running?

1. **Check Actions are enabled:**
   - Settings → Actions → Allow actions

2. **Verify cron syntax:**
   - Use [crontab.guru](https://crontab.guru) to verify

3. **Check GitHub Actions status:**
   - Visit [githubstatus.com](https://www.githubstatus.com)

### Trades Not Executing?

1. **Check if market is open:**
   - Look at workflow logs for "Market is closed" message

2. **Verify API credentials:**
   - Check Secrets are set correctly
   - Test credentials locally

3. **Review trading logic:**
   - Check if buy/sell conditions are met
   - Review `daily_trading.log` in artifacts

### Workflow Failing?

1. **Check Python dependencies:**
   - Verify all packages install correctly
   - Look for import errors in logs

2. **API rate limits:**
   - Alpaca has rate limits
   - Add delays if hitting limits

3. **Timeout issues:**
   - Increase `timeout-minutes` if needed
   - Default is 15 minutes

## Security Best Practices

### ✅ Do's

- ✅ Use repository secrets for API keys
- ✅ Start with paper trading
- ✅ Review logs regularly
- ✅ Test manually before automation
- ✅ Keep repository private if using live trading

### ❌ Don'ts

- ❌ Never commit `.env` file with real keys
- ❌ Don't put API keys in workflow file
- ❌ Don't ignore failed workflow notifications
- ❌ Don't skip testing with paper trading first

## Switching from Paper to Live Trading

When you're ready to use real money:

1. **Verify strategy performance:**
   - Run paper trading for at least 2 weeks
   - Review all trades carefully
   - Confirm logic matches backtesting

2. **Update secrets:**
   - Change `ALPACA_BASE_URL` to `https://api.alpaca.markets`
   - Update API keys to live trading keys

3. **Start small:**
   - Set `POSITION_SIZE_LIMIT=0.10` (10% of buying power)
   - Gradually increase as you gain confidence

4. **Monitor closely:**
   - Check logs daily for first week
   - Set up notifications
   - Review monthly performance

## Summary

✅ **Automated** - Runs at 9:30 AM ET Monday-Friday
✅ **Reliable** - Cloud-based, no local computer needed
✅ **Free** - GitHub Actions free tier is generous
✅ **Safe** - Starts with paper trading
✅ **Logged** - Full execution history preserved
✅ **Monitored** - Email notifications on issues

Your backtested 24,012% return strategy is now running automatically in the cloud! 🚀

## Next Steps

1. ✅ Push code to GitHub
2. ✅ Add API secrets
3. ✅ Test manual run
4. ✅ Monitor first few automatic runs
5. ✅ Review weekly performance
6. 🎯 Consider switching to live trading after validation

**Questions?** Check the workflow logs or review the trading algorithm documentation.
