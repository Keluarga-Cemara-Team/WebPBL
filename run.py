import os
import sys
from dotenv import load_dotenv
from app import create_app

# Pastikan output console di Windows mendukung utf-8 tanpa crash
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Muat variabel lingkungan dari .env jika ada
load_dotenv()

config_name = os.getenv("FLASK_ENV", "development")
app = create_app(config_name)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    print(f">> AntiBurnout Web Frontend berjalan di http://127.0.0.1:{port} (Debug={debug})")
    app.run(host="127.0.0.1", port=port, debug=debug)
