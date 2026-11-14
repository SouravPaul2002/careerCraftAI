from pypdf import PdfReader
from docx import Document
import io


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader= PdfReader(io.BytesIO(file_bytes))
    pages= [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()

def extract_text_from_docx(file_bytes: bytes) -> str:
    # in future 
    res= ""
    return res

def parse_document(file_bytes: bytes, document_type: str)-> str:
    doc_type= document_type.upper()
    if doc_type == "PDF":
        return extract_text_from_pdf(file_bytes)
    if doc_type == "DOCX":
        return extract_text_from_docx(file_bytes)
    raise ValueError(f"Unsupported document type: {document_type}")