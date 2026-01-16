"""
Convert newsletter HTML content to PDF format for reMarkable.
"""
from weasyprint import HTML, CSS
from io import BytesIO
from typing import Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PDFConverter:
    """Convert newsletter content to PDF."""

    # CSS styling optimized for reMarkable e-ink display
    REMARKABLE_CSS = """
    @page {
        size: A4;
        margin: 1cm;
    }

    body {
        font-family: 'Georgia', 'Times New Roman', serif;
        font-size: 12pt;
        line-height: 1.6;
        color: #000000;
        max-width: 800px;
        margin: 0 auto;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Arial', 'Helvetica', sans-serif;
        font-weight: bold;
        margin-top: 1em;
        margin-bottom: 0.5em;
    }

    h1 { font-size: 18pt; }
    h2 { font-size: 16pt; }
    h3 { font-size: 14pt; }

    p {
        margin-bottom: 1em;
        text-align: justify;
    }

    a {
        color: #000000;
        text-decoration: underline;
    }

    img {
        max-width: 100%;
        height: auto;
        display: block;
        margin: 1em 0;
    }

    .newsletter-header {
        border-bottom: 2px solid #000000;
        padding-bottom: 0.5em;
        margin-bottom: 1em;
    }

    .newsletter-title {
        font-size: 20pt;
        font-weight: bold;
        margin-bottom: 0.2em;
    }

    .newsletter-meta {
        font-size: 10pt;
        color: #666666;
        font-style: italic;
    }

    blockquote {
        border-left: 3px solid #000000;
        padding-left: 1em;
        margin-left: 0;
        font-style: italic;
    }

    pre, code {
        font-family: 'Courier New', monospace;
        background-color: #f0f0f0;
        padding: 0.2em 0.4em;
        font-size: 10pt;
    }

    pre {
        padding: 1em;
        overflow-x: auto;
    }

    table {
        border-collapse: collapse;
        width: 100%;
        margin: 1em 0;
    }

    th, td {
        border: 1px solid #000000;
        padding: 0.5em;
        text-align: left;
    }

    th {
        background-color: #e0e0e0;
        font-weight: bold;
    }
    """

    def __init__(self):
        self.css = CSS(string=self.REMARKABLE_CSS)

    def convert_newsletter_to_pdf(
        self,
        subject: str,
        sender: str,
        date: datetime,
        html_body: str,
        text_body: str
    ) -> bytes:
        """
        Convert newsletter to PDF.

        Args:
            subject: Newsletter subject
            sender: Sender email/name
            date: Newsletter date
            html_body: HTML content
            text_body: Plain text fallback

        Returns:
            PDF as bytes
        """
        logger.info(f"Converting newsletter to PDF: {subject}")

        # Use HTML if available, otherwise convert text to HTML
        if html_body:
            content = self._wrap_html(subject, sender, date, html_body)
        else:
            content = self._text_to_html(subject, sender, date, text_body)

        # Convert to PDF
        pdf_bytes = self._html_to_pdf(content)
        logger.info(f"Successfully converted newsletter to PDF ({len(pdf_bytes)} bytes)")

        return pdf_bytes

    def _wrap_html(self, subject: str, sender: str, date: datetime, html_body: str) -> str:
        """Wrap HTML content with header and styling."""
        date_str = date.strftime("%B %d, %Y")

        # Add header with newsletter info
        header = f"""
        <div class="newsletter-header">
            <div class="newsletter-title">{self._escape_html(subject)}</div>
            <div class="newsletter-meta">
                From: {self._escape_html(sender)}<br/>
                Date: {date_str}
            </div>
        </div>
        """

        # Wrap in complete HTML document
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{self._escape_html(subject)}</title>
        </head>
        <body>
            {header}
            {html_body}
        </body>
        </html>
        """

        return html

    def _text_to_html(self, subject: str, sender: str, date: datetime, text_body: str) -> str:
        """Convert plain text to HTML."""
        date_str = date.strftime("%B %d, %Y")

        # Convert text to HTML paragraphs
        paragraphs = text_body.split('\n\n')
        html_paragraphs = ''.join(f'<p>{self._escape_html(p)}</p>' for p in paragraphs if p.strip())

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{self._escape_html(subject)}</title>
        </head>
        <body>
            <div class="newsletter-header">
                <div class="newsletter-title">{self._escape_html(subject)}</div>
                <div class="newsletter-meta">
                    From: {self._escape_html(sender)}<br/>
                    Date: {date_str}
                </div>
            </div>
            {html_paragraphs}
        </body>
        </html>
        """

        return html

    def _html_to_pdf(self, html_content: str) -> bytes:
        """Convert HTML to PDF bytes."""
        html = HTML(string=html_content)
        pdf_buffer = BytesIO()
        html.write_pdf(pdf_buffer, stylesheets=[self.css])
        return pdf_buffer.getvalue()

    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
