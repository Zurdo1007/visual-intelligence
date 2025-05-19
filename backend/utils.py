from collections import Counter
import re
import cv2
import numpy as np
from pyzbar.pyzbar import decode as zbar_decode
from sklearn.feature_extraction.text import TfidfVectorizer

# Türkçe stopword listesi
TURKISH_STOPWORDS = set([
    've', 'bir', 'bu', 'ile', 'de', 'da', 'için', 'ama', 'gibi', 'daha', 'çok', 'en', 'mi', 'ne', 'veya', 'ya', 'ki',
    'ben', 'sen', 'o', 'biz', 'siz', 'onlar', 'şu', 'şimdi', 'her', 'hiç', 'hep', 'yani', 'ise', 'ile', 've', 'de', 'da',
    'mı', 'mu', 'mü', 'mi', 'bir', 'iki', 'üç', 'dört', 'beş', 'altı', 'yedi', 'sekiz', 'dokuz', 'on', 'var', 'yok',
    'ol', 'olsun', 'olmaz', 'oldu', 'olacak', 'olabilir', 'olduğunu', 'olarak', 'olduğu', 'olmadı', 'olması', 'olsa',
    'olsaydı', 'olmuş', 'olmamış', 'olmadığı', 'olmazsa', 'olmadıysa', 'olmayacak', 'olmayabilir', 'olmayınca', 'olmazdı',
    'olmazken', 'olmazmış', 'olmazsan', 'olmazsın', 'olmazsınız', 'olmazlar', 'olmazsak', 'olmazsanız', 'olmazlarsa',
    'olmazlarmış', 'olmazlarmışsınız', 'olmazlarmışlar', 'olmazlarmışsak', 'olmazlarmışsanız', 'olmazlarmışlarsa',
    'olmazlarmışmış', 'olmazlarmışmışsınız', 'olmazlarmışmışlar', 'olmazlarmışmışsak', 'olmazlarmışmışsanız', 'olmazlarmışmışlarsa'
])

def simple_summarize(text, max_sentences=2):
    sentences = re.split(r'(?<=[.!?]) +', text)
    return ' '.join(sentences[:max_sentences])

def extract_keywords(text, num_keywords=5):
    # Temizle ve stopword'leri çıkar
    words = [w for w in re.findall(r'\w+', text.lower()) if w not in TURKISH_STOPWORDS and len(w) > 2]
    if not words:
        return []
    # TF-IDF ile anahtar kelime çıkar
    try:
        vectorizer = TfidfVectorizer(stop_words=list(TURKISH_STOPWORDS), max_features=30)
        tfidf = vectorizer.fit_transform([' '.join(words)])
        scores = zip(vectorizer.get_feature_names_out(), tfidf.toarray()[0])
        sorted_keywords = sorted(scores, key=lambda x: x[1], reverse=True)
        return [w for w, s in sorted_keywords[:num_keywords]]
    except Exception:
        # Fallback: en sık geçen kelimeler
        common = Counter(words).most_common(num_keywords)
        return [w for w, _ in common]

# HuggingFace ile Türkçe özetleme
from transformers import pipeline
_summarizer = None
def get_summarizer():
    global _summarizer
    if _summarizer is None:
        _summarizer = pipeline("summarization", model="csebuetnlp/mT5_multilingual_XLSum")
    return _summarizer

def huggingface_summarize(text):
    summarizer = get_summarizer()
    summary = summarizer(text, max_length=60, min_length=10, do_sample=False)
    return summary[0]['summary_text']

def detect_qr_and_barcodes(image):
    # image: PIL Image
    cv_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    decoded = zbar_decode(cv_img)
    results = []
    for obj in decoded:
        results.append({'type': obj.type, 'data': obj.data.decode('utf-8')})
    return results

def detect_tables(image):
    # Basit tablo tespiti: Yatay ve dikey çizgileri bul
    cv_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(cv_img, (3,3), 0)
    thresh = cv2.adaptiveThreshold(blur,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY_INV,15,4)
    # Dikey çizgiler
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 30))
    vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
    # Yatay çizgiler
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 1))
    horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    # Çizgileri birleştir
    table_mask = cv2.addWeighted(vertical_lines, 0.5, horizontal_lines, 0.5, 0.0)
    # Kontur bul
    contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    table_boxes = [cv2.boundingRect(cnt) for cnt in contours if cv2.contourArea(cnt) > 1000]
    return table_boxes 