# app.py
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
CORS(app)  # Enable CORS for frontend-backend communication

# Database configuration from environment variables
db_config = {
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '1234'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'flashcard_app')
}

# Hugging Face API configuration
HF_TOKEN = os.getenv('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')
HF_API_URL = "https://api-inference.huggingface.co/models/mrm8488/t5-base-finetuned-question-generation-ap"
HF_HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

@app.route('/generate-flashcards', methods=['POST'])
def generate_flashcards():
    try:
        data = request.json
        notes = data.get('notes', '')
        
        if not notes:
            return jsonify({'error': 'No notes provided'}), 400
        
        # Clean and preprocess the text
        cleaned_notes = clean_text(notes)
        
        # Split into sentences
        sentences = split_into_sentences(cleaned_notes)
        
        flashcards = []
        for sentence in sentences[:10]:  # Limit to 10 flashcards for demo
            if len(sentence.split()) > 5:  # Only process meaningful sentences
                question = generate_question(sentence)
                if question:
                    flashcards.append({
                        'question': question,
                        'answer': sentence
                    })
        
        # Store in database
        store_flashcards(flashcards)
        
        return jsonify({'flashcards': flashcards})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def clean_text(text):
    """Clean and preprocess the input text"""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?;:]', '', text)
    return text.strip()

def split_into_sentences(text):
    """Split text into sentences using punctuation"""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s for s in sentences if s]

def generate_question(context):
    """Generate a question using Hugging Face Inference API"""
    try:
        # Prepare the payload for the API
        payload = {
            "inputs": f"generate question: {context}"
        }
        
        # Send the request to Hugging Face
        response = requests.post(HF_API_URL, headers=HF_HEADERS, json=payload)
        response.raise_for_status()  # Check for HTTP errors
        result = response.json()
        
        return result[0]['generated_text']
        
    except Exception as e:
        print(f"Hugging Face API error: {e}")
        # Fallback: create a simple fill-in-the-blank question
        words = context.split()
        if len(words) > 3:
            blank_index = len(words) // 2
            words[blank_index] = "______"
            return " ".join(words)
        return context

def store_flashcards(flashcards):
    """Store generated flashcards in the database"""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        for card in flashcards:
            # Using deck_id = 1 as default; you might want to make this dynamic
            cursor.execute(
                "INSERT INTO flashcards (deck_id, question, answer) VALUES (%s, %s, %s)",
                (1, card['question'], card['answer'])
            )
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Flashcards stored successfully!")
        
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify the API is running"""
    return jsonify({'status': 'healthy', 'message': 'Flashcard API is running'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)