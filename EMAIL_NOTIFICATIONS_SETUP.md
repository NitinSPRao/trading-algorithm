# Email Notifications Setup

Get daily trading reports sent to your email automatically.

## What You'll Receive

Every trading day at 9:30 AM ET, you and your partner will receive an email with:

### 📊 Daily Report Contents

```
============================================================
📊 DAILY TRADING REPORT - 2025-12-15 09:30 AM ET
============================================================

🔄 TODAY'S ACTIVITY:
   Entered Position Today: ✅ YES / ❌ NO
   Exited Position Today:  ✅ YES / ❌ NO

📍 CURRENT POSITION:
   Status: 🟢 IN POSITION / ⚪ NO POSITION

   If IN POSITION:
   - Purchase Price: $120.50
   - Position Size: 85 shares
   - Exit Price Needed: $127.49
   - Current Profit: +2.3%

   If NO POSITION:
   - Days Since Last Trade: 3

📈 CURRENT MARKET DATA:
   TECL Price: $123.45
   VIX: 15.67
   TECL 30-day SMA: $125.30
   VIX 30-day WMA: 16.89

🎯 ENTRY PRICE TARGETS:
   Immediate Buy if TECL < $93.98 (0.75 × SMA)
   VIX Buy Threshold: TECL < $156.63 (1.25 × SMA)
   VIX Condition (VIX > $17.57): ❌ NOT MET
   Distance to Immediate Buy: $29.47 (23.9%)
============================================================
```

**Attachments:**
- `daily_report.json` - Machine-readable data
- `daily_trading.log` - Full execution log

## Setup Steps

### 1. Get Gmail App Password

For security, use a Gmail App Password (not your regular password):

1. Go to your Google Account: https://myaccount.google.com/
2. **Security** → **2-Step Verification** (enable if not already)
3. **Security** → **App passwords**
4. Select app: **Mail**
5. Select device: **Other (Custom name)**
6. Enter: "Trading Algorithm"
7. Click **Generate**
8. **Copy the 16-character password** (you'll only see it once!)

### 2. Add Email Secrets to GitHub

Go to your repository → **Settings** → **Secrets and variables** → **Actions**

Add these **3 new secrets**:

| Secret Name | Value | Example |
|-------------|-------|---------|
| `EMAIL_USERNAME` | Your Gmail address | `youremail@gmail.com` |
| `EMAIL_PASSWORD` | App password from step 1 | `abcd efgh ijkl mnop` |
| `EMAIL_TO` | Recipient email(s) | `you@gmail.com,partner@gmail.com` |

**For multiple recipients:**
- Separate with commas: `email1@gmail.com,email2@gmail.com`
- Both you and your partner will receive reports

### 3. Done!

That's it! The next workflow run will send emails automatically.

## Testing Email Notifications

1. Go to **Actions** tab
2. Click your workflow
3. **Run workflow** → **Run workflow**
4. Wait for completion
5. Check your email inbox!

## Email Settings

The workflow is configured to use:
- **Server:** Gmail SMTP (smtp.gmail.com)
- **Port:** 465 (SSL)
- **Security:** Secure connection
- **Priority:** Normal

### Using Different Email Provider

If you're not using Gmail, update these in the workflow file (`.github/workflows/daily-trading-dst.yml`):

**Outlook/Hotmail:**
```yaml
server_address: smtp-mail.outlook.com
server_port: 587
```

**Yahoo Mail:**
```yaml
server_address: smtp.mail.yahoo.com
server_port: 465
```

**Custom SMTP:**
```yaml
server_address: your-smtp-server.com
server_port: 587  # or 465
```

## Troubleshooting

### Not Receiving Emails?

1. **Check spam folder** - First email might go to spam
2. **Verify secrets** - Ensure all 3 email secrets are set correctly
3. **Check app password** - Make sure you used app password, not regular password
4. **Review workflow logs** - Look for email sending step errors

### Email Sending Failed?

Common issues:
- **2-Step Verification not enabled** - Required for app passwords
- **Wrong app password** - Generate a new one
- **Email address typo** - Check `EMAIL_TO` secret
- **Gmail blocking** - Allow less secure apps if needed

### Want to Stop Emails?

Option 1: **Remove email step from workflow**
- Edit `.github/workflows/daily-trading-dst.yml`
- Delete or comment out the "Send email report" step

Option 2: **Set EMAIL_TO to empty**
- Update `EMAIL_TO` secret to blank

## Email Frequency

Emails are sent:
- ✅ **Every trading day** (Monday-Friday)
- ✅ **At 9:30 AM ET** (after market open)
- ✅ **After successful run** (whether trades occur or not)
- ✅ **On failures** (so you know if something breaks)

## Privacy & Security

✅ **Secrets are encrypted** - GitHub encrypts all secrets
✅ **Not in logs** - Secrets don't appear in workflow logs
✅ **SSL/TLS used** - Email sent over secure connection
✅ **App password** - Not your main Gmail password

## Customizing the Report

Want to modify what's in the email? Edit `trading_algorithm/daily_trader.py`:

**Key function:** `format_report_text(report)`

Add/remove sections as needed. The report includes all the data you requested:
- ✅ Entered position today
- ✅ Exited position today
- ✅ Currently in open position
- ✅ Exit price needed (if in position)
- ✅ Days since last trade (if not in position)
- ✅ Entry price targets at current VIX levels

## Example Workflow

```
9:30 AM ET → GitHub Actions runs
            ↓
         Checks signals
            ↓
         Executes any trades
            ↓
         Generates report
            ↓
         Sends email to you & partner
            ↓
         You check email over coffee ☕
```

No need to manually check - the report comes to you!

## Questions?

- Check the [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md) for general workflow setup
- Review workflow logs in **Actions** tab for errors
- Test with a manual run first before relying on scheduled runs

Your comprehensive daily trading reports are ready! 📧✅
