from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import requests
import os
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
# Be more specific with CORS in production for security
CORS(app) 

# --- DATABASE CONFIGURATION ---
db_config = {
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '1234'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'flashcard_app'),
    'pool_name': 'flashcard_pool',
    'pool_size': 5
}

# --- HUGGING FACE API CONFIGURATION ---
HF_TOKEN = os.getenv('HUGGING_FACE_TOKEN')
if not HF_TOKEN:
    raise ValueError("HUGGING_FACE_TOKEN environment variable not set.")
    
HF_API_URL = "https://api-inference.huggingface.co/models/mrm8488/t5-base-finetuned-question-generation-ap"
HF_HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

# --- UTILITY FUNCTIONS ---
def clean_text(text):
    """Clean and preprocess the input text."""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s.,!?;:]', '', text)
    return text.strip()

def split_into_sentences(text):
    """Split text into sentences using basic punctuation."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s for s in sentences if s and len(s.split()) > 5] # Ensure meaningful sentences

def generate_question(context):
    """Generate a question using Hugging Face Inference API with a fallback."""
    try:
        response = requests.post(HF_API_URL, headers=HF_HEADERS, json={"inputs": f"generate question: {context}"}, timeout=10)
        response.raise_for_status()
        result = response.json()
        if result and isinstance(result, list) and 'generated_text' in result[0]:
            return result[0]['generated_text']
    except requests.exceptions.RequestException as e:
        print(f"Hugging Face API error: {e}")
    
    # Fallback if API fails or returns unexpected format
    words = context.split()
    if len(words) > 3:
        blank_index = len(words) // 2
        words[blank_index] = "______"
        return " ".join(words) + "?"
    return f"What is {context}?"

def store_flashcards(flashcards):
    """Store a list of generated flashcards in the database efficiently and securely."""
    if not flashcards:
        return

    # SQL statement with placeholders for security
    sql = "INSERT INTO flashcards (deck_id, question, answer) VALUES (%s, %s, %s)"
    
    # Prepare data for bulk insert
    # Using deck_id = 1 as default; this could be made dynamic
    data_to_insert = [(1, card['question'], card['answer']) for card in flashcards]

    conn = None
    try:
        # Get a connection from the pool
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # Use executemany for efficient bulk insertion
        cursor.executemany(sql, data_to_insert)
        
        conn.commit()
        print(f"{cursor.rowcount} flashcards stored successfully!")
        
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        # Optionally roll back changes if something goes wrong
        if conn:
            conn.rollback()
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# --- API ROUTES ---
@app.route('/generate-flashcards', methods=['POST'])
def generate_flashcards_route():
    try:
        data = request.json
        notes = data.get('notes', '')
        
        if not notes:
            return jsonify({'error': 'No notes provided'}), 400
        
        cleaned_notes = clean_text(notes)
        sentences = split_into_sentences(cleaned_notes)
        
        flashcards = []
        # Limit to the first 10 valid sentences for the demo
        for sentence in sentences[:10]:
            question = generate_question(sentence)
            if question:
                flashcards.append({'question': question, 'answer': sentence})
        
        if not flashcards:
            return jsonify({'error': 'Could not generate flashcards from the provided text.'}), 400
            
        # Store in the database
        store_flashcards(flashcards)
        
        return jsonify({'flashcards': flashcards})
    
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({'error': 'An internal server error occurred.'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify API and DB connectivity."""
    try:
        conn = mysql.connector.connect(**db_config)
        if conn.is_connected():
            conn.close()
            db_status = 'connected'
        else:
            db_status = 'disconnected'
    except mysql.connector.Error:
        db_status = 'error'
        
    return jsonify({'status': 'healthy', 'database_status': db_status})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
