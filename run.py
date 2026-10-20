import os
from dotenv import load_dotenv
from app import create_app

# Muat variabel lingkungan dari .env jika ada
load_dotenv()

config_name = os.getenv("FLASK_ENV", "development")
app = create_app(config_name)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    print(f"🚀 AntiBurnout Web Frontend berjalan di http://127.0.0.1:{port} (Debug={debug})")
    app.run(host="127.0.0.1", port=port, debug=debug)
