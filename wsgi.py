import os
import threading
import webview
from app import create_app  

app = create_app() 

def start_flask():
    app.run(debug=False, use_reloader=False)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()

    webview.create_window('Cavalcanti Rações', 'http://127.0.0.1:5000')
    webview.start()
