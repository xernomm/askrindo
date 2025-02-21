import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from app import create_app
from app.utils import parse_file
from app.file_parsers import read_docx, read_pdf, read_txt, read_xlsx
import cx_Oracle
import ollama
import json
#import chromadb
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

app = create_app()
CORS(app)

#client = chromadb.Client()
#collection = client.create_collection(name="docs")

username = "askrindo"
password = "askrindo"
host = "192.168.30.132"
port = "1531"
service_name = "FREEPDB1"
table = "test_vector2"
chat_table = "chat_history"

# Membuat string koneksi
dsn = cx_Oracle.makedsn(host, port, service_name=service_name)
connection = cx_Oracle.connect(user=username, password=password, dsn=dsn)
cursor = connection.cursor()

DATA_FOLDER = "data/FINANCE"

# Ensure necessary directories exist
os.makedirs(DATA_FOLDER, exist_ok=True)

all_paragraphs = []
filenames = []


def process_files_from_folder(folder_path, table, cursor, connection):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        # Ekstraksi teks berdasarkan format file
        if filename.endswith(".pdf"):
            text = read_pdf(file_path)
        elif filename.endswith(".docx"):
            text = read_docx(file_path)
        elif filename.endswith(".txt"):
            text = read_txt(file_path)
        elif filename.endswith(".xlsx"):
            text = read_xlsx(file_path)
        else:
            print(f"❌ Unsupported file format: {filename}")
            continue

        # Validasi teks
        if not text:
            print(f"⚠ No text extracted from: {filename}")
            continue

        print(f"✅ Processing: {filename}")

        # 🔍 Cek apakah data sudah ada di database
        check_query = f"""
            SELECT text FROM {table} WHERE filename = :filename
        """
        cursor.execute(check_query, {"filename": filename})
        existing_row = cursor.fetchone()

        # Jika file dengan nama yang sama ada
        if existing_row:
            if existing_row[0] == text:
                print(f"⏩ File '{filename}' sudah ada dan tidak berubah. Lewati proses.")
                continue  # Tidak ada perubahan, skip proses
            else:
                print(f"🔄 File '{filename}' diperbarui. Melakukan update data...")

                # 🔥 Embedding dengan ollama untuk teks baru
                response = ollama.embed(
                    model='mxbai-embed-large',
                    input=text,
                )
                embeddings = response["embeddings"]
                embeddings_json = json.dumps(embeddings)

                # 📝 Update data di database
                update_query = f"""
                    UPDATE {table} 
                    SET text = :text, text_vector = :text_vector
                    WHERE filename = :filename
                """
                try:
                    cursor.setinputsizes(text=cx_Oracle.CLOB, text_vector=cx_Oracle.CLOB)
                    cursor.execute(update_query, {"text": text, "text_vector": embeddings_json, "filename": filename})
                    connection.commit()
                    print(f"✅ Data '{filename}' berhasil diperbarui.")
                except cx_Oracle.DatabaseError as e:
                    print(f"❌ Gagal memperbarui '{filename}': {e}")
                    connection.rollback()
                continue

        # 🎯 Jika file baru (tidak ada di database)
        print(f"✨ File '{filename}' adalah data baru. Melakukan insert...")
        response = ollama.embed(
            model='mxbai-embed-large',
            input=text,
        )
        embeddings = response["embeddings"]
        embeddings_json = json.dumps(embeddings)

        # 🔒 Insert data ke Oracle
        insert_query = f"""
            INSERT INTO {table} (filename, text, text_vector) 
            VALUES (:filename, :text, :text_vector)
        """
        try:
            cursor.setinputsizes(text=cx_Oracle.CLOB, text_vector=cx_Oracle.CLOB)
            cursor.execute(insert_query, {"filename": filename, "text": text, "text_vector": embeddings_json})
            connection.commit()
            print(f"🎯 Data '{filename}' berhasil ditambahkan.")
        except cx_Oracle.DatabaseError as e:
            print(f"❌ Gagal menambahkan '{filename}': {e}")
            connection.rollback()



process_files_from_folder(folder_path=DATA_FOLDER, table=table, cursor=cursor, connection=connection)

def save_chat_to_db(user_input, bot_response):
    """Menyimpan pertanyaan user ke database dengan response awal NULL."""
    query = f"""
        INSERT INTO {chat_table} (USER_INPUT, BOT_RESPONSE, TIMESTAMP) 
        VALUES (:1, :2, SYSTIMESTAMP)
        RETURNING ID INTO :3
    """
    chat_id = cursor.var(cx_Oracle.NUMBER)  # Simpan ID yang baru dimasukkan
    cursor.execute(query, (user_input, bot_response, chat_id))
    connection.commit()
    return chat_id.getvalue()[0]  # Mengembalikan ID chat yang baru

def update_chat_response(chat_id, bot_response):
    """Memperbarui response dari bot berdasarkan chat_id."""
    query = f"""
        UPDATE {chat_table} 
        SET BOT_RESPONSE = :1
        WHERE ID = :2
    """
    cursor.execute(query, (bot_response, chat_id))
    connection.commit()

def get_chat_history():
    """Mengambil seluruh riwayat chat dari database."""
    
    query = f"SELECT ID, USER_INPUT, BOT_RESPONSE, TIMESTAMP FROM {chat_table} ORDER BY TIMESTAMP ASC"

    cursor.execute(query)
    rows = cursor.fetchall()

    messages = []
    for row in rows:
        _, user_input, bot_response, _ = row  # Abaikan ID & TIMESTAMP
        
        # Pastikan LOB dikonversi ke string
        if isinstance(user_input, cx_Oracle.LOB):
            user_input = user_input.read()
        if isinstance(bot_response, cx_Oracle.LOB):
            bot_response = bot_response.read()
        
        messages.append({"role": "user", "content": user_input})
        messages.append({"role": "assistant", "content": bot_response})
    
    return messages



@app.route('/chat-history', methods=['GET'])
def get_chat_history_endpoint():
    try:
        chat_history = get_chat_history()
        return jsonify({"chat_history": chat_history})
    except Exception as e:
        app.logger.error(f"Error retrieving chat history: {str(e)}")
        return jsonify({"error": "Failed to retrieve chat history"}), 500

    
@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.json.get('question')
    if not user_input:
        return jsonify({"error": "Pertanyaan wajib diisi."}), 400

    try:
        # 🎯 1. Simpan user input ke database terlebih dahulu dengan response NULL
        chat_id = save_chat_to_db(user_input, None)  # Response masih kosong

        # 🔍 2. Embedding pertanyaan user
        embed_response = ollama.embed(
            model='mxbai-embed-large',
            input=user_input,
        )
        user_embedding = np.array(embed_response["embeddings"]).reshape(1, -1)  # 💡 Ke numpy array

        # 🔎 3. Ambil semua embedding dari DB
        query = f"SELECT text, text_vector FROM {table}"
        cursor.execute(query)
        rows = cursor.fetchall()

        if not rows:
            bot_response = "Maaf, saya tidak menemukan informasi relevan."
            update_chat_response(chat_id, bot_response)  # ✅ Update response ke DB
            return jsonify({"response": bot_response})

        # 🧮 4. Hitung cosine similarity di Python
        similarities = []
        for text, vector_json in rows:
            if hasattr(vector_json, 'read'):
                vector_json = vector_json.read()  # ✅ Baca isi CLOB ke string

            db_embedding = np.array(json.loads(vector_json)).reshape(1, -1)
            similarity = cosine_similarity(user_embedding, db_embedding)[0][0]
            similarities.append((similarity, text))

        # 🔝 5. Ambil 3 teratas berdasarkan similarity
        top_contexts = sorted(similarities, key=lambda x: x[0], reverse=True)[:3]
        context_texts = "\n".join([ctx[1] for ctx in top_contexts if ctx[0] > 0.75])

        if not context_texts:
            context_texts = "Tidak ada konteks relevan yang ditemukan."

        print(f"🔗 Konteks dokumen yang ditemukan: {len(context_texts)} karakter")

        # 💬 6. Generasi jawaban
        generation_prompt = f"""
        Berikut adalah beberapa informasi terkait:
        {context_texts}

        Pertanyaan: {user_input}
        Jawablah pertanyaan di atas secara lengkap dan jelas dengan menggunakan informasi yang relevan. Jangan melakukan riset atau pencarian dari sumber lain selain informasi terkait yang disediakan.
        Jangan awali jawaban dengan kata-kata seperti: \"Berdasarkan informasi yang tersedia\" atau \"Dari data yang ada\".
        """
        response = ollama.generate(
            model="llama3:latest",
            prompt=generation_prompt
        )
        bot_response = response["response"].strip()

        # ✅ 7. Update response di database
        update_chat_response(chat_id, bot_response)

        return jsonify({"response": bot_response})

    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(f"❌ Oracle Error: {error.message}")
        return jsonify({"error": "Kesalahan pada database: " + error.message}), 500

    except Exception as e:
        print(f"❌ General Error: {str(e)}")
        return jsonify({"error": "Terjadi kesalahan internal: " + str(e)}), 500

    

@app.route('/truncate-chat-history', methods=['POST'])
def truncate_chat_history():
    try:
        cursor.execute(f'TRUNCATE TABLE {chat_table}')
        connection.commit()
        return jsonify({"message": "Tabel chat_history berhasil di-truncate."}), 200
    except Exception as e:
        connection.rollback()
        app.logger.error(f"Error truncating chat_history table: {str(e)}")
        return jsonify({"error": "Gagal melakukan truncate pada tabel chat_history."}), 500

if __name__ == "__main__":
    app.run(debug=True)
