from flask import Flask, request, jsonify, render_template
import os
import re
import google.generativeai as genai
from PyPDF2 import PdfReader
import docx


app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- Google API Setup ----------------
# ⚡ Directly put your API key here
GOOGLE_API_KEY = "AIzaSyBaljQZjcjUKUwVbT0tSody9AITPU429mc" 
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


# ---------------- Helper Functions ----------------
def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    text_chunks = [page.extract_text().strip() for page in reader.pages if page.extract_text()]
    return "\n\n".join(text_chunks)

def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    text_chunks = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
    return "\n\n".join(text_chunks)

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
    citations_apa = re.findall(r'\([A-Za-z]+, \d{4}\)', text)
    citations_num = re.findall(r'\[\d+\]', text)
    return list(set(citations_apa + citations_num))

def summarize_with_gemini(text):
    prompt = f'''Task: Summarize the following document into clear, concise bullet points. The document may be in PDF, DOCX, or TXT format.

Requirements:

Summarize all key information without losing meaning.

Present the summary directly in bullet points, jumping straight to them.

Include citations in author-year style at the end of each bullet where relevant.

Normalize/format citations consistently, even if the original text is inconsistent.

Ensure the summary is concise, refined, and usable for general purposes.

Output format:

Bullet points for key information.

Citations included at the end of each bullet in parentheses (Author, Year).

Avoid extra explanations or introductions.\n\n{text}'''
    
    response = model.generate_content(prompt)
    return response.text if response else "Error: No response from Gemini."

# ---------------- Routes ----------------
@app.route('/')
def home():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get("file")
    if not file or file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    filename = file.filename
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    try:
        text = extract_text(file_path)
        summary = summarize_with_gemini(text)
        citations = extract_citations(text)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "filename": filename,
        "summary": summary,
        "citations": citations
    })

if __name__ == "__main__":
    app.run(debug=True)