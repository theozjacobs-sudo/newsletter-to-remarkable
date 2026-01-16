# Newsletter to reMarkable

Automatically sync newsletters from your Gmail and iCloud accounts to your reMarkable tablet, with automatic cleanup after 30 days.

## Features

- **Automatic Newsletter Fetching**: Connects to Gmail and iCloud via IMAP to fetch newsletters
- **PDF Conversion**: Converts newsletter HTML/text content to beautifully formatted PDFs optimized for reMarkable's e-ink display
- **Organized Storage**: Creates a dedicated "Newsletters" folder on your reMarkable
- **Automatic Cleanup**: Deletes newsletters older than 30 days automatically
- **Duplicate Prevention**: Tracks uploaded newsletters to avoid duplicates
- **GitHub Actions Automation**: Runs daily via GitHub Actions (no server required!)

## How It Works

1. **Daily Schedule**: GitHub Actions runs the sync script every day at 8 AM UTC
2. **Fetch Newsletters**: Retrieves new newsletters from your configured email accounts
3. **Convert to PDF**: Transforms email content into reader-friendly PDFs
4. **Upload to reMarkable**: Sends PDFs to your reMarkable tablet via the cloud API
5. **Track & Cleanup**: Tracks upload dates and deletes newsletters older than 30 days

## Setup Instructions

### 1. Fork This Repository

Click the "Fork" button at the top of this repository to create your own copy.

### 2. Get Email App Passwords

#### Gmail
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Factor Authentication if not already enabled
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Generate a new app password for "Mail"
5. Save this password (you'll add it to GitHub Secrets)

#### iCloud
1. Go to [Apple ID Account](https://appleid.apple.com/)
2. Sign in and go to "Security" section
3. Under "App-Specific Passwords", click "Generate Password"
4. Name it "reMarkable Sync" and generate
5. Save this password (you'll add it to GitHub Secrets)

### 3. Get reMarkable API Token

1. Go to [https://my.remarkable.com/connect/desktop](https://my.remarkable.com/connect/desktop)
2. Click "Connect" to generate a one-time code
3. Copy this code **immediately** (you'll add it to GitHub Secrets)

**Important**:
- This one-time code is **only used for the first sync**. After that, a persistent device token is cached automatically.
- The code itself expires if not used within a short time, so add it to GitHub Secrets quickly.
- If you need to re-authenticate later, clear the cache in GitHub Actions and generate a new code.

### 4. Configure GitHub Secrets

In your forked repository:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** and add the following:

| Secret Name | Value |
|-------------|-------|
| `GMAIL_EMAIL` | Your Gmail address (e.g., `you@gmail.com`) |
| `GMAIL_PASSWORD` | Gmail App Password from step 2 |
| `ICLOUD_EMAIL` | Your iCloud email address (e.g., `you@icloud.com`) |
| `ICLOUD_PASSWORD` | iCloud App-Specific Password from step 2 |
| `REMARKABLE_TOKEN` | One-time code from step 3 |

**Optional secrets** (if you want to specify specific folders):
- `GMAIL_FOLDER` - Gmail folder/label to fetch from (default: `INBOX`)
- `ICLOUD_FOLDER` - iCloud folder to fetch from (default: `INBOX`)

### 5. Enable GitHub Actions

1. Go to the **Actions** tab in your repository
2. Click "I understand my workflows, go ahead and enable them"
3. The workflow will now run daily at 8 AM UTC

### 6. Test the Sync

To test immediately without waiting for the daily schedule:

1. Go to **Actions** tab
2. Click on "Sync Newsletters to reMarkable" workflow
3. Click "Run workflow" → "Run workflow"
4. Wait for it to complete and check the logs

## Configuration

### How Newsletter Filtering Works

**Important**: By default, the system fetches **ALL emails** from your inbox from the last 7 days. To avoid syncing personal emails, you have two options:

#### Option A: Use a Dedicated Folder (Recommended)

1. In Gmail: Create a label called "Newsletters"
2. Set up filters to automatically label newsletters (Gmail → Settings → Filters)
3. In the workflow file, change `folder: 'INBOX'` to `folder: 'Newsletters'`

For iCloud, create a mailbox and set up rules to move newsletters there.

#### Option B: Filter by Sender

Add specific newsletter sender addresses to `allowed_senders`:

```yaml
email_accounts:
  - provider: gmail
    email: ${{ secrets.GMAIL_EMAIL }}
    folder: INBOX
    allowed_senders:
      - newsletter@substack.com
      - hello@example.com
      - updates@another.com
```

Only emails from these addresses will be synced.

### Customizing Settings

Edit `.github/workflows/sync-newsletters.yml` to modify:

```yaml
cleanup:
  max_age_days: 30  # Change to your preferred age

sync:
  lookback_days: 7  # How many days back to check for emails
  mark_as_read: true  # Mark emails as read after processing
```

## Local Development

To run this locally:

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy configuration files:
   ```bash
   cp config.yaml.example config.yaml
   cp .env.example .env
   ```

4. Edit `config.yaml` and `.env` with your credentials

5. Run the sync:
   ```bash
   python main.py
   ```

## Troubleshooting

### Sync Not Working

1. **Check GitHub Actions logs**: Go to Actions tab and view the latest run
2. **Verify secrets**: Make sure all GitHub Secrets are set correctly
3. **reMarkable token expired**: Generate a new token and update `REMARKABLE_TOKEN` secret
4. **Email connection issues**: Verify your app passwords are correct

### No Newsletters Appearing

1. Check that newsletters are in the correct folder (INBOX or specified folder)
2. Verify `lookback_days` is sufficient (default is 7 days)
3. Check if `allowed_senders` filter is too restrictive
4. Look at the sync logs in GitHub Actions

### Newsletters Not Deleting

1. Verify that `tracker.json` is being cached properly in GitHub Actions
2. Check that newsletters are actually older than `max_age_days` (default 30 days)

## Project Structure

```
newsletter-to-remarkable/
├── src/
│   ├── email_fetcher.py      # IMAP email fetching
│   ├── pdf_converter.py      # HTML to PDF conversion
│   ├── remarkable_client.py  # reMarkable Cloud API client
│   ├── document_tracker.py   # Track uploaded documents
│   └── cleanup.py            # Cleanup old documents
├── main.py                   # Main orchestration script
├── requirements.txt          # Python dependencies
├── config.yaml.example       # Configuration template
├── .env.example             # Environment variables template
└── .github/
    └── workflows/
        └── sync-newsletters.yml  # GitHub Actions workflow

```

## Privacy & Security

- All credentials are stored as encrypted GitHub Secrets
- The sync runs in a private GitHub Actions environment
- No data is stored or transmitted to third parties (only GitHub ↔ Email ↔ reMarkable)
- Email passwords use app-specific passwords, not your main account password

## License

MIT License - feel free to use and modify as needed!

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Acknowledgments

- Built with [rmapy](https://github.com/subutux/rmapy) for reMarkable API access
- Uses [WeasyPrint](https://weasyprint.org/) for PDF generation
