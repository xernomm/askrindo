import PyPDF2
from docx import Document
import pandas as pd

# Reading file functions
def read_txt(filename):
    try:
        with open(filename, "r", encoding="utf-8-sig") as f:
            content = f.read().strip()
            if not content:
                raise ValueError(f"{filename} is empty.")
            return content
    except Exception as e:
        print(f"Error reading TXT file {filename}: {e}")
        return ""

def read_pdf(filename):
    try:
        with open(filename, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            if not text.strip():
                raise ValueError(f"{filename} is empty.")
            return text
    except Exception as e:
        print(f"Error reading PDF file {filename}: {e}")
        return ""

def read_docx(filename):
    try:
        doc = Document(filename)
        text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
        if not text.strip():
            raise ValueError(f"{filename} is empty.")
        return text
    except Exception as e:
        print(f"Error reading DOCX file {filename}: {e}")
        return ""

def read_xlsx(filename):
    try:
        df = pd.read_excel(filename)
        text = "\n".join(df.astype(str).apply(lambda row: " ".join(row), axis=1))
        if not text.strip():
            raise ValueError(f"{filename} is empty.")
        return text
    except Exception as e:
        print(f"Error reading XLSX file {filename}: {e}")
        return ""
    
