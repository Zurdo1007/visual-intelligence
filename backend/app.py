from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pytesseract
from PIL import Image
import io
import base64
import os
from .utils import simple_summarize, extract_keywords, huggingface_summarize, detect_qr_and_barcodes, detect_tables
import fitz  # PyMuPDF

app = Flask(__name__, static_folder='../frontend')
CORS(app)

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/extract-text', methods=['POST'])
def extract_text():
    try:
        image_data = request.json.get('image')
        lang = request.json.get('lang', 'tur+eng')
        filetype = request.json.get('filetype', 'image')
        if not image_data:
            return jsonify({'error': 'No image data provided'}), 400
        if filetype == 'pdf':
            pdf_bytes = base64.b64decode(image_data.split(',')[1] if ',' in image_data else image_data)
            with open('temp.pdf', 'wb') as f:
                f.write(pdf_bytes)
            doc = fitz.open('temp.pdf')
            all_text = []
            for page in doc:
                all_text.append(page.get_text())
            doc.close()
            os.remove('temp.pdf')
            text = '\n'.join(all_text)
            return jsonify({'success': True, 'text': text.strip(), 'qr_barcodes': [], 'tables': []})
        else:
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(image, lang=lang)
            qr_barcodes = detect_qr_and_barcodes(image)
            tables = detect_tables(image)
            return jsonify({'success': True, 'text': text.strip(), 'qr_barcodes': qr_barcodes, 'tables': tables})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/summarize', methods=['POST'])
def summarize():
    text = request.json.get('text', '')
    if len(text.split()) < 30:
        summary = simple_summarize(text)
    else:
        try:
            summary = huggingface_summarize(text)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Gelişmiş özetleme başarısız: {str(e)}'}), 500
    return jsonify({'success': True, 'summary': summary})

@app.route('/keywords', methods=['POST'])
def extract_keywords_api():
    text = request.json.get('text', '')
    keywords = extract_keywords(text)
    return jsonify({'success': True, 'keywords': keywords})

if __name__ == '__main__':
    app.run(debug=True) 