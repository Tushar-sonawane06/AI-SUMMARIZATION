from flask import Flask, request, jsonify, render_template
import os
import re
import google.generativeai as genai
from PyPDF2 import PdfReader
import docx
from flask import Flask, jsonify
from flask_cors import CORS
import os

# Create Flask app
app = Flask(__name__)

# Enable CORS (so Netlify frontend can call this backend)
CORS(app, origins=["https://aisummarization.netlify.app/"])  
# 👆 replace with your actual Netlify URL
# If you just want to allow ALL origins while testing, use: CORS(app)

# Example API route
@app.route("AIzaSyC7oU_iSJoYRVJhLsqVEy2E8GDGVx9WqbA")
def get_data():
    return jsonify({
        "message": "Hello from Flask backend!",
        "status": "success"
    })

# Run the app (Render will auto-detect PORT)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Google Gemini AI Setup
GOOGLE_API_KEY = "AIzaSyC7oU_iSJoYRVJhLsqVEy2E8GDGVx9WqbA"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# ---------------- Helper Functions ----------------
def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    return "\n\n".join([p.extract_text().strip() for p in reader.pages if p.extract_text()])

def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    return "\n\n".join([p.text.strip() for p in doc.paragraphs if p.text.strip()])

def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        raise ValueError("Unsupported file format. Use PDF, DOCX, or TXT.")

def extract_citations(text):
    apa = re.findall(r'\([A-Za-z]+, \d{4}\)', text)
    nums = re.findall(r'\[\d+\]', text)
    return list(set(apa + nums))

def summarize_with_gemini(text):
    prompt = f'''Summarize this document into concise bullet points with citations (Author, Year). Keep it clear and direct.\n\n{text}'''
    response = model.generate_content(prompt)
    return response.text if response else "Error: No response from Gemini."

# ---------------- Routes ----------------
@app.route('/')
def home():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    filename = file.filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    try:
        text = extract_text(filepath)
        summary = summarize_with_gemini(text)
        citations = extract_citations(text)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"filename": filename, "summary": summary, "citations": citations})

if _name_ == "_main_":
    app.run(debug=True)