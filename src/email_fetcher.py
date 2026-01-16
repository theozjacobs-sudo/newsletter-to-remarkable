"""
Fetch newsletters from email accounts (Gmail, iCloud) via IMAP.
"""
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class Newsletter:
    """Represents a newsletter email."""

    def __init__(self, subject: str, sender: str, date: datetime, html_body: str, text_body: str):
        self.subject = subject
        self.sender = sender
        self.date = date
        self.html_body = html_body
        self.text_body = text_body
        self.message_id = None

    def __repr__(self):
        return f"Newsletter(subject='{self.subject}', sender='{self.sender}', date={self.date})"


class EmailFetcher:
    """Fetch newsletters from email accounts via IMAP."""

    def __init__(self, email_address: str, password: str, imap_server: str, imap_port: int = 993):
        self.email_address = email_address
        self.password = password
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.connection: Optional[imaplib.IMAP4_SSL] = None

    def connect(self) -> None:
        """Connect to the IMAP server."""
        logger.info(f"Connecting to {self.imap_server}:{self.imap_port}")
        self.connection = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
        self.connection.login(self.email_address, self.password)
        logger.info(f"Successfully logged in as {self.email_address}")

    def disconnect(self) -> None:
        """Disconnect from the IMAP server."""
        if self.connection:
            self.connection.logout()
            logger.info("Disconnected from IMAP server")

    def fetch_newsletters(
        self,
        folder: str = "INBOX",
        lookback_days: int = 7,
        allowed_senders: Optional[List[str]] = None,
        mark_as_read: bool = False
    ) -> List[Newsletter]:
        """
        Fetch newsletters from the specified folder.

        Args:
            folder: IMAP folder to search (e.g., "INBOX", "newsletters")
            lookback_days: How many days back to search for emails
            allowed_senders: List of email addresses to filter by (None = all senders)
            mark_as_read: Whether to mark emails as read after fetching

        Returns:
            List of Newsletter objects
        """
        if not self.connection:
            raise RuntimeError("Not connected to IMAP server. Call connect() first.")

        newsletters = []

        # Select the mailbox
        logger.info(f"Selecting folder: {folder}")
        status, messages = self.connection.select(folder)
        if status != "OK":
            logger.error(f"Failed to select folder {folder}")
            return newsletters

        # Calculate date threshold
        date_threshold = datetime.now() - timedelta(days=lookback_days)
        date_str = date_threshold.strftime("%d-%b-%Y")

        # Search for emails since the date threshold
        search_criteria = f'SINCE {date_str}'
        logger.info(f"Searching for emails with criteria: {search_criteria}")

        status, email_ids = self.connection.search(None, search_criteria)
        if status != "OK":
            logger.error("Failed to search emails")
            return newsletters

        email_id_list = email_ids[0].split()
        logger.info(f"Found {len(email_id_list)} emails")

        for email_id in email_id_list:
            try:
                newsletter = self._fetch_email(email_id, allowed_senders)
                if newsletter:
                    newsletters.append(newsletter)

                    if mark_as_read:
                        self.connection.store(email_id, '+FLAGS', '\\Seen')

            except Exception as e:
                logger.error(f"Error fetching email {email_id}: {e}")
                continue

        logger.info(f"Successfully fetched {len(newsletters)} newsletters")
        return newsletters

    def _fetch_email(self, email_id: bytes, allowed_senders: Optional[List[str]]) -> Optional[Newsletter]:
        """Fetch and parse a single email."""
        status, msg_data = self.connection.fetch(email_id, "(RFC822)")

        if status != "OK":
            return None

        # Parse the email
        email_body = msg_data[0][1]
        msg = email.message_from_bytes(email_body)

        # Extract sender
        sender = msg.get("From", "")
        # Filter by allowed senders if specified
        if allowed_senders:
            sender_email = email.utils.parseaddr(sender)[1]
            if not any(allowed in sender_email for allowed in allowed_senders):
                logger.debug(f"Skipping email from {sender_email} (not in allowed senders)")
                return None

        # Extract subject
        subject_header = msg.get("Subject", "")
        subject = self._decode_header(subject_header)

        # Extract date
        date_str = msg.get("Date", "")
        date = email.utils.parsedate_to_datetime(date_str) if date_str else datetime.now()

        # Extract message ID
        message_id = msg.get("Message-ID", "")

        # Extract body
        html_body = ""
        text_body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/html":
                    html_body = part.get_payload(decode=True).decode(errors='ignore')
                elif content_type == "text/plain":
                    text_body = part.get_payload(decode=True).decode(errors='ignore')
        else:
            content_type = msg.get_content_type()
            body = msg.get_payload(decode=True).decode(errors='ignore')
            if content_type == "text/html":
                html_body = body
            else:
                text_body = body

        newsletter = Newsletter(subject, sender, date, html_body, text_body)
        newsletter.message_id = message_id

        logger.debug(f"Fetched: {newsletter}")
        return newsletter

    @staticmethod
    def _decode_header(header: str) -> str:
        """Decode email header."""
        decoded_parts = decode_header(header)
        decoded_str = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_str += part.decode(encoding or 'utf-8', errors='ignore')
            else:
                decoded_str += part
        return decoded_str

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
