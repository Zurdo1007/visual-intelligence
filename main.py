import webview
import threading
from backend.app import app

def start_server():
    app.run(host='127.0.0.1', port=5000)

if __name__ == '__main__':
    # Flask sunucusunu ayrı bir thread'de başlat
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()

    # Masaüstü penceresini oluştur
    webview.create_window(
        'Görsel Zekâ',
        'http://127.0.0.1:5000',
        width=800,
        height=900,
        resizable=True,
        min_size=(600, 700)
    )
    webview.start() 