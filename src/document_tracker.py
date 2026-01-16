"""
Track uploaded documents and their upload dates for cleanup purposes.
"""
import json
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DocumentTracker:
    """Track uploaded documents and their metadata."""

    def __init__(self, tracker_file: str = "tracker.json"):
        """
        Initialize document tracker.

        Args:
            tracker_file: Path to the JSON file storing document metadata
        """
        self.tracker_file = Path(tracker_file)
        self.documents: Dict[str, Dict] = {}
        self._load()

    def _load(self) -> None:
        """Load tracker data from file."""
        if self.tracker_file.exists():
            try:
                with open(self.tracker_file, 'r') as f:
                    self.documents = json.load(f)
                logger.info(f"Loaded {len(self.documents)} tracked documents")
            except Exception as e:
                logger.error(f"Error loading tracker file: {e}")
                self.documents = {}
        else:
            logger.info("No existing tracker file found, starting fresh")
            self.documents = {}

    def _save(self) -> None:
        """Save tracker data to file."""
        try:
            with open(self.tracker_file, 'w') as f:
                json.dump(self.documents, f, indent=2)
            logger.debug(f"Saved {len(self.documents)} tracked documents")
        except Exception as e:
            logger.error(f"Error saving tracker file: {e}")

    def add_document(
        self,
        document_id: str,
        title: str,
        upload_date: Optional[datetime] = None,
        message_id: Optional[str] = None
    ) -> None:
        """
        Add or update a document in the tracker.

        Args:
            document_id: Unique document ID from reMarkable
            title: Document title
            upload_date: Upload timestamp (defaults to now)
            message_id: Original email message ID
        """
        if upload_date is None:
            upload_date = datetime.now()

        self.documents[document_id] = {
            'title': title,
            'upload_date': upload_date.isoformat(),
            'message_id': message_id
        }

        self._save()
        logger.info(f"Tracked document: {title} (ID: {document_id})")

    def get_document(self, document_id: str) -> Optional[Dict]:
        """
        Get document metadata.

        Args:
            document_id: Document ID

        Returns:
            Document metadata dict or None
        """
        return self.documents.get(document_id)

    def remove_document(self, document_id: str) -> None:
        """
        Remove a document from the tracker.

        Args:
            document_id: Document ID to remove
        """
        if document_id in self.documents:
            title = self.documents[document_id]['title']
            del self.documents[document_id]
            self._save()
            logger.info(f"Removed from tracker: {title} (ID: {document_id})")

    def get_old_documents(self, max_age_days: int) -> Dict[str, Dict]:
        """
        Get documents older than the specified age.

        Args:
            max_age_days: Maximum age in days

        Returns:
            Dict of document_id -> metadata for old documents
        """
        now = datetime.now()
        old_documents = {}

        for doc_id, metadata in self.documents.items():
            upload_date = datetime.fromisoformat(metadata['upload_date'])
            age_days = (now - upload_date).days

            if age_days >= max_age_days:
                old_documents[doc_id] = {
                    **metadata,
                    'age_days': age_days
                }

        logger.info(f"Found {len(old_documents)} documents older than {max_age_days} days")
        return old_documents

    def is_already_uploaded(self, message_id: str) -> bool:
        """
        Check if an email has already been uploaded.

        Args:
            message_id: Email message ID

        Returns:
            True if already uploaded
        """
        for metadata in self.documents.values():
            if metadata.get('message_id') == message_id:
                return True
        return False

    def get_all_documents(self) -> Dict[str, Dict]:
        """
        Get all tracked documents.

        Returns:
            Dict of document_id -> metadata
        """
        return self.documents.copy()

    def sync_with_remarkable(self, remarkable_document_ids: list) -> None:
        """
        Remove tracked documents that no longer exist on reMarkable.

        Args:
            remarkable_document_ids: List of current document IDs from reMarkable
        """
        removed_count = 0
        for doc_id in list(self.documents.keys()):
            if doc_id not in remarkable_document_ids:
                logger.info(f"Document {doc_id} no longer on reMarkable, removing from tracker")
                del self.documents[doc_id]
                removed_count += 1

        if removed_count > 0:
            self._save()
            logger.info(f"Synced tracker, removed {removed_count} documents")
