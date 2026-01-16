"""
Interface with reMarkable Cloud API to upload and manage documents.
"""
from rmapy.api import Client
from rmapy.folder import Folder
from rmapy.document import Document
from typing import Optional, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class RemarkableClient:
    """Client for interacting with reMarkable Cloud."""

    def __init__(self, one_time_code: Optional[str] = None):
        """
        Initialize reMarkable client.

        Args:
            one_time_code: One-time code from https://my.remarkable.com/device/desktop/connect
        """
        self.client = Client()
        self.one_time_code = one_time_code
        self.is_authenticated = False

    def authenticate(self) -> None:
        """Authenticate with reMarkable Cloud."""
        if not self.one_time_code:
            raise ValueError("One-time code is required for authentication")

        logger.info("Authenticating with reMarkable Cloud")
        self.client.register_device(self.one_time_code)
        self.client.renew_token()
        self.is_authenticated = True
        logger.info("Successfully authenticated with reMarkable Cloud")

    def get_or_create_folder(self, folder_name: str) -> Folder:
        """
        Get existing folder or create a new one.

        Args:
            folder_name: Name of the folder

        Returns:
            Folder object
        """
        if not self.is_authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        logger.info(f"Looking for folder: {folder_name}")

        # Get all items
        items = self.client.get_meta_items()

        # Search for existing folder
        for item in items:
            if isinstance(item, Folder) and item.VissibleName == folder_name:
                logger.info(f"Found existing folder: {folder_name}")
                return item

        # Create new folder
        logger.info(f"Creating new folder: {folder_name}")
        folder = Folder(folder_name)
        self.client.create_folder(folder)

        # Refresh and get the created folder
        items = self.client.get_meta_items()
        for item in items:
            if isinstance(item, Folder) and item.VissibleName == folder_name:
                return item

        raise RuntimeError(f"Failed to create folder: {folder_name}")

    def upload_pdf(
        self,
        pdf_bytes: bytes,
        filename: str,
        folder: Optional[Folder] = None
    ) -> Document:
        """
        Upload a PDF to reMarkable.

        Args:
            pdf_bytes: PDF content as bytes
            filename: Name for the document
            folder: Optional folder to upload to

        Returns:
            Uploaded Document object
        """
        if not self.is_authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        logger.info(f"Uploading PDF: {filename}")

        # Create document
        doc = Document(filename)

        if folder:
            doc.Parent = folder.ID

        # Upload the document
        with open('/tmp/temp_upload.pdf', 'wb') as f:
            f.write(pdf_bytes)

        self.client.upload(doc)
        self.client.upload_pdf_document('/tmp/temp_upload.pdf', doc)

        logger.info(f"Successfully uploaded: {filename}")
        return doc

    def get_documents_in_folder(self, folder_name: str) -> List[Document]:
        """
        Get all documents in a specific folder.

        Args:
            folder_name: Name of the folder

        Returns:
            List of Document objects
        """
        if not self.is_authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        # Find folder
        folder = None
        items = self.client.get_meta_items()

        for item in items:
            if isinstance(item, Folder) and item.VissibleName == folder_name:
                folder = item
                break

        if not folder:
            logger.warning(f"Folder not found: {folder_name}")
            return []

        # Get documents in folder
        documents = []
        for item in items:
            if isinstance(item, Document) and item.Parent == folder.ID:
                documents.append(item)

        logger.info(f"Found {len(documents)} documents in folder: {folder_name}")
        return documents

    def delete_document(self, document: Document) -> None:
        """
        Delete a document from reMarkable.

        Args:
            document: Document to delete
        """
        if not self.is_authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        logger.info(f"Deleting document: {document.VissibleName}")
        self.client.delete(document)
        logger.info(f"Successfully deleted: {document.VissibleName}")

    def get_all_documents(self) -> List[Document]:
        """
        Get all documents from reMarkable.

        Returns:
            List of all Document objects
        """
        if not self.is_authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        items = self.client.get_meta_items()
        documents = [item for item in items if isinstance(item, Document)]

        logger.info(f"Found {len(documents)} total documents")
        return documents
