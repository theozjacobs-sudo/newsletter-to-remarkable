#!/usr/bin/env python3
"""
Main script to sync newsletters from email to reMarkable tablet.
"""
import os
import sys
import yaml
import logging
from pathlib import Path
from dotenv import load_dotenv
from src.email_fetcher import EmailFetcher
from src.pdf_converter import PDFConverter
from src.remarkable_client import RemarkableClient
from src.document_tracker import DocumentTracker
from src.cleanup import NewsletterCleanup

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('newsletter-sync.log')
    ]
)
logger = logging.getLogger(__name__)


def load_config(config_path: str = 'config.yaml') -> dict:
    """Load configuration from YAML file."""
    if not Path(config_path).exists():
        logger.error(f"Configuration file not found: {config_path}")
        logger.error("Please copy config.yaml.example to config.yaml and fill in your settings")
        sys.exit(1)

    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def get_env_variable(var_name: str) -> str:
    """Get environment variable with error handling."""
    value = os.getenv(var_name)
    if not value:
        logger.error(f"Environment variable {var_name} not set")
        logger.error("Please check your .env file")
        sys.exit(1)
    return value


def fetch_newsletters(config: dict) -> list:
    """Fetch newsletters from all configured email accounts."""
    all_newsletters = []

    for account in config['email_accounts']:
        logger.info(f"Fetching newsletters from {account['email']}")

        try:
            # Get password from environment
            password = get_env_variable(account['password_env'])

            # Create fetcher and connect
            fetcher = EmailFetcher(
                email_address=account['email'],
                password=password,
                imap_server=account['imap_server'],
                imap_port=account.get('imap_port', 993)
            )

            with fetcher:
                newsletters = fetcher.fetch_newsletters(
                    folder=account.get('folder', 'INBOX'),
                    lookback_days=config['sync'].get('lookback_days', 7),
                    allowed_senders=account.get('allowed_senders'),
                    mark_as_read=config['sync'].get('mark_as_read', False)
                )

                all_newsletters.extend(newsletters)
                logger.info(f"Fetched {len(newsletters)} newsletters from {account['email']}")

        except Exception as e:
            logger.error(f"Error fetching from {account['email']}: {e}")
            continue

    return all_newsletters


def upload_newsletters(newsletters: list, config: dict, remarkable: RemarkableClient, tracker: DocumentTracker) -> int:
    """Convert newsletters to PDF and upload to reMarkable."""
    if not newsletters:
        logger.info("No newsletters to upload")
        return 0

    # Get or create folder
    folder_name = config['remarkable']['folder_name']
    folder = remarkable.get_or_create_folder(folder_name)

    # Initialize PDF converter
    pdf_converter = PDFConverter()

    uploaded_count = 0

    for newsletter in newsletters:
        try:
            # Skip if already uploaded
            if newsletter.message_id and tracker.is_already_uploaded(newsletter.message_id):
                logger.info(f"Skipping already uploaded: {newsletter.subject}")
                continue

            # Convert to PDF
            pdf_bytes = pdf_converter.convert_newsletter_to_pdf(
                subject=newsletter.subject,
                sender=newsletter.sender,
                date=newsletter.date,
                html_body=newsletter.html_body,
                text_body=newsletter.text_body
            )

            # Generate filename
            safe_subject = "".join(
                c if c.isalnum() or c in (' ', '-', '_') else '_'
                for c in newsletter.subject
            )
            filename = f"{safe_subject[:50]}"

            # Upload to reMarkable
            doc = remarkable.upload_pdf(pdf_bytes, filename, folder)

            # Track the upload
            tracker.add_document(
                document_id=doc.ID,
                title=filename,
                message_id=newsletter.message_id
            )

            uploaded_count += 1
            logger.info(f"Uploaded: {filename}")

        except Exception as e:
            logger.error(f"Error uploading newsletter '{newsletter.subject}': {e}")
            continue

    return uploaded_count


def main():
    """Main execution function."""
    logger.info("=== Newsletter to reMarkable Sync Started ===")

    # Load environment variables
    load_dotenv()

    # Load configuration
    config = load_config()

    # Initialize document tracker
    tracker = DocumentTracker()

    # Initialize reMarkable client
    remarkable_token = get_env_variable(config['remarkable']['one_time_code_env'])
    remarkable = RemarkableClient(remarkable_token)

    try:
        # Authenticate with reMarkable
        remarkable.authenticate()

        # Fetch newsletters from email
        newsletters = fetch_newsletters(config)
        logger.info(f"Total newsletters fetched: {len(newsletters)}")

        # Upload newsletters to reMarkable
        uploaded_count = upload_newsletters(newsletters, config, remarkable, tracker)
        logger.info(f"Successfully uploaded {uploaded_count} newsletters")

        # Cleanup old newsletters
        cleanup = NewsletterCleanup(remarkable, tracker)
        deleted_count = cleanup.cleanup_old_newsletters(
            folder_name=config['remarkable']['folder_name'],
            max_age_days=config['cleanup']['max_age_days']
        )
        logger.info(f"Cleaned up {deleted_count} old newsletters")

        # Sync tracker with reMarkable
        cleanup.sync_tracker(config['remarkable']['folder_name'])

        logger.info("=== Newsletter to reMarkable Sync Completed Successfully ===")

    except Exception as e:
        logger.error(f"Fatal error during sync: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
