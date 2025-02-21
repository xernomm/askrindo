import ollama
import pypdf
import cx_Oracle

print(cx_Oracle.clientversion()) 
# Konfigurasi koneksi
username = "testuser1"
password = "testuser1"
host = "192.168.30.77"
port = "1521"
service_name = "FREEPDB1"
table = "test_vector2"

# Membuat string koneksi
dsn = cx_Oracle.makedsn(host, port, service_name=service_name)
connection = cx_Oracle.connect(user=username, password=password, dsn=dsn)
cursor = connection.cursor()


def upload_pdf(file_path):
    with open(file_path, "rb") as file:
        pdf_reader = pypdf.PdfReader(file)
        
        for page in pdf_reader.pages:
            page_text = page.extract_text()

            # Amankan teks
            if page_text:
                insert_query = f"""
                    INSERT INTO {table} (text, text_vector) 
                    VALUES (
                        :text, 
                        vector_embedding(all_minilm_l12_v2 USING :text AS data)
                    )
                """
                cursor.execute(insert_query, {"text": page_text})
                connection.commit()


upload_pdf("docs/teguh.pdf")

query = input(">>> ")

# Ambil dokumen paling relevan berdasarkan vector distance
cursor.execute(f"""
    SELECT vector_distance(TEXT_VECTOR, (vector_embedding(all_minilm_l12_v2 using :query as data))) as distance, text 
    FROM {table} 
    ORDER BY 1 DESC 
    FETCH FIRST 3 ROWS ONLY
""", {"query": query})

rows = cursor.fetchall()
result = []
for row in rows:
    vector_value = row[0]  # Kolom VECTOR
    clob_object = row[1]  # Kolom CLOB
    
    # Pastikan membaca CLOB dengan aman
    clob_content = clob_object.read() if hasattr(clob_object, "read") else clob_object
    
    # Tambahkan ke result
    result.append({"vector": vector_value, "text": clob_content})

# Chat dengan Ollama
response = ollama.chat(
    model="llama3:latest",
    messages=[
        {"role": "system", "content": "Gunakan informasi berikut untuk menjawab dengan akurat."},
        {"role": "assistant", "content": result[0]["text"] if len(result) > 0 else ""},
        {"role": "assistant", "content": result[1]["text"] if len(result) > 1 else ""},
        {"role": "user", "content": query},
    ]
)

print(response["message"]["content"])
print("===================================================")

cursor.close()
connection.close()
