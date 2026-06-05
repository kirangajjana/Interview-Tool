import pypdf
from typing import BinaryIO

class ResumeParser:
    @staticmethod
    def extract_text(file_stream: BinaryIO) -> str:
        """Extracts text from a PDF binary stream."""
        try:
            reader = pypdf.PdfReader(file_stream)
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            return "\n".join(text_parts).strip()
        except Exception as e:
            raise ValueError(f"Failed to parse PDF resume: {str(e)}")
