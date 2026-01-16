"""
Cleanup old newsletters from reMarkable based on age.
"""
import logging
from typing import List
from .remarkable_client import RemarkableClient
from .document_tracker import DocumentTracker

logger = logging.getLogger(__name__)


class NewsletterCleanup:
    """Handle cleanup of old newsletters."""

    def __init__(self, remarkable_client: RemarkableClient, tracker: DocumentTracker):
        """
        Initialize cleanup handler.

        Args:
            remarkable_client: Authenticated reMarkable client
            tracker: Document tracker instance
        """
        self.remarkable = remarkable_client
        self.tracker = tracker

    def cleanup_old_newsletters(
        self,
        folder_name: str,
        max_age_days: int
    ) -> int:
        """
        Delete newsletters older than max_age_days.

        Args:
            folder_name: Folder containing newsletters
            max_age_days: Maximum age in days before deletion

        Returns:
            Number of documents deleted
        """
        logger.info(f"Starting cleanup: deleting newsletters older than {max_age_days} days")

        # Get old documents from tracker
        old_documents = self.tracker.get_old_documents(max_age_days)

        if not old_documents:
            logger.info("No old documents to clean up")
            return 0

        # Get current documents from reMarkable
        remarkable_docs = self.remarkable.get_documents_in_folder(folder_name)
        remarkable_doc_map = {doc.ID: doc for doc in remarkable_docs}

        deleted_count = 0

        for doc_id, metadata in old_documents.items():
            if doc_id in remarkable_doc_map:
                try:
                    # Delete from reMarkable
                    self.remarkable.delete_document(remarkable_doc_map[doc_id])

                    # Remove from tracker
                    self.tracker.remove_document(doc_id)

                    deleted_count += 1
                    logger.info(
                        f"Deleted: {metadata['title']} "
                        f"(age: {metadata['age_days']} days)"
                    )

                except Exception as e:
                    logger.error(f"Error deleting document {doc_id}: {e}")
            else:
                # Document no longer exists on reMarkable, just remove from tracker
                logger.info(
                    f"Document {metadata['title']} not found on reMarkable, "
                    f"removing from tracker"
                )
                self.tracker.remove_document(doc_id)

        logger.info(f"Cleanup complete: deleted {deleted_count} documents")
        return deleted_count

    def sync_tracker(self, folder_name: str) -> None:
        """
        Sync tracker with current state of reMarkable.

        Args:
            folder_name: Folder to sync
        """
        logger.info("Syncing tracker with reMarkable")

        remarkable_docs = self.remarkable.get_documents_in_folder(folder_name)
        remarkable_doc_ids = [doc.ID for doc in remarkable_docs]

        self.tracker.sync_with_remarkable(remarkable_doc_ids)
        logger.info("Sync complete")
