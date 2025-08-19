import PyPDF2
from docx import Document as DocxDocument
import xml.etree.ElementTree as ET
from fastapi import HTTPException




class DocumentProcessor:
    @staticmethod
    def process_pdf(file_path: str) -> str:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text

    @staticmethod
    def process_docx(file_path: str) -> str:
        doc = DocxDocument(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text

    @staticmethod
    def process_txt(file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

    @staticmethod
    def process_xml(file_path: str) -> str:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        def extract_text(element):
            text = element.text or ""
            for child in element:
                text += extract_text(child)
            return text + (element.tail or "")
        
        return extract_text(root)

def extract_text_from_file(file_path: str, filename: str) -> str:
    """Extract text from various file formats."""
    file_ext = filename.lower().split('.')[-1]
    
    try:
        if file_ext == 'pdf':
            return DocumentProcessor.process_pdf(file_path)
        elif file_ext in ['docx', 'doc']:
            return DocumentProcessor.process_docx(file_path)
        elif file_ext == 'txt':
            return DocumentProcessor.process_txt(file_path)
        elif file_ext == 'xml':
            return DocumentProcessor.process_xml(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process {filename}: {str(e)}")



