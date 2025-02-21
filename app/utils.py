import os
import cx_Oracle
import pandas as pd
from app.file_parsers import read_txt, read_pdf, read_docx, read_xlsx  # Pastikan fungsi ini tersedia

DATA_FOLDER = "data"
OUTPUT_FOLDER = "output_txt"
FULL_CONTEXT_FILE = "full_context.txt"

# Konfigurasi koneksi Oracle
ORACLE_USERNAME = "askrindo"
ORACLE_PASSWORD = "askrindo"
ORACLE_HOST = "192.168.30.132"
ORACLE_PORT = "1531"
ORACLE_SERVICE_NAME = "FREEPDB1"

dsn = cx_Oracle.makedsn(ORACLE_HOST, ORACLE_PORT, service_name=ORACLE_SERVICE_NAME)
connection = cx_Oracle.connect(user=ORACLE_USERNAME, password=ORACLE_PASSWORD, dsn=dsn)
cursor = connection.cursor()

def parse_file(file_path):
    """
    Parse a file based on its extension and return the content as a list of paragraphs.
    """
    file_extension = file_path.lower()
    if file_extension.endswith(".txt"):
        return read_txt(file_path)
    elif file_extension.endswith(".pdf"):
        return read_pdf(file_path)
    elif file_extension.endswith(".docx"):
        return read_docx(file_path)
    elif file_extension.endswith(".xlsx"):
        return read_xlsx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path}")

# def save_documents_to_db():
#     """
#     Save the content of all files in the data folder into the Document database table.
#     """
#     try:
#         cursor.execute("DELETE FROM documents")  # Hapus semua data lama
#         connection.commit()

#         for file in os.listdir(DATA_FOLDER):
#             file_path = os.path.join(DATA_FOLDER, file)
#             if file.lower().endswith((".txt", ".pdf", ".docx", ".xlsx")):
#                 paragraphs = parse_file(file_path)
#                 content = "\n".join(paragraphs)
#                 cursor.execute("INSERT INTO documents (name, content) VALUES (:1, :2)", (file, content))
        
#         connection.commit()
#     except Exception as e:
#         connection.rollback()
#         print(f"Error saving documents to the database: {e}")

# def process_files_and_create_tables():
#     """Process all CSV and Excel files in the DATA_FOLDER and create corresponding database tables."""
#     try:
#         for file in os.listdir(DATA_FOLDER):
#             file_path = os.path.join(DATA_FOLDER, file)
#             if not file.lower().endswith((".csv", ".xlsx", ".xls")):
#                 continue

#             table_name = os.path.splitext(file)[0]
#             if file.lower().endswith(".csv"):
#                 df = pd.read_csv(file_path)
#             else:
#                 df = pd.read_excel(file_path)

#             columns = ", ".join([f"{col} VARCHAR2(4000)" for col in df.columns])
#             cursor.execute(f"CREATE TABLE {table_name} ({columns})")
            
#             for _, row in df.iterrows():
#                 values = tuple(row.astype(str).fillna("NULL"))
#                 placeholders = ", ".join([":" + str(i+1) for i in range(len(values))])
#                 cursor.execute(f"INSERT INTO {table_name} VALUES ({placeholders})", values)
            
#             connection.commit()
#             print(f"Tabel '{table_name}' berhasil dibuat dari file '{file}'.")
#     except Exception as e:
#         connection.rollback()
#         print(f"Error processing files: {e}")

# def save_data_to_txt():
#     """Read all xlsx and csv files, then write their contents to .txt files."""
#     try:
#         for file in os.listdir(DATA_FOLDER):
#             file_path = os.path.join(DATA_FOLDER, file)
#             if not file.lower().endswith((".csv", ".xlsx", ".xls")):
#                 continue

#             output_file_path = os.path.join(OUTPUT_FOLDER, f"{os.path.splitext(file)[0]}.txt")
#             if file.lower().endswith(".csv"):
#                 df = pd.read_csv(file_path)
#             else:
#                 df = pd.read_excel(file_path)

#             with open(output_file_path, "w", encoding="utf-8") as f:
#                 f.write(df.to_string(index=False))
#             print(f"File '{file}' berhasil disimpan ke '{output_file_path}'.")
#     except Exception as e:
#         print(f"Error processing files: {e}")

def update_full_context(system_prompt, context_from_embeddings):
    """Update full_context.txt with combined data."""
    try:
        additional_context = ""
        for txt_file in os.listdir(OUTPUT_FOLDER):
            txt_file_path = os.path.join(OUTPUT_FOLDER, txt_file)
            if txt_file.lower().endswith(".txt"):
                with open(txt_file_path, "r", encoding="utf-8") as f:
                    additional_context += f"\n\n---\n\nFile: {txt_file}\n" + f.read()

        full_context = f"{system_prompt}\n\n{context_from_embeddings}\n\n{additional_context}"
        with open(FULL_CONTEXT_FILE, "w", encoding="utf-8") as f:
            f.write(full_context)
        print(f"Full context berhasil diperbarui di '{FULL_CONTEXT_FILE}'.")
    except Exception as e:
        print(f"Error updating full context: {e}")

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
