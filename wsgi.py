import os
import threading
import webview
from app import create_app  # <- importa a app configurada

app = create_app()  # <- aqui está a instância correta do Flask com db.init_app(app)

def start_flask():
    app.run(debug=False, use_reloader=False)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()

    webview.create_window('Cavalcanti Rações', 'http://127.0.0.1:5000')
    webview.start()
