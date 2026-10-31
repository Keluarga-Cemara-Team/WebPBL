import os
from pathlib import Path
from typing import Optional
import firebase_admin
from firebase_admin import credentials, firestore

class FirebaseClient:
    """
    Infrastruktur koneksi ke Google Cloud Firestore via Firebase Admin SDK.
    Mendukung file credentials path spesifik atau auto-discovery file service account.
    """
    def __init__(self, credentials_path: Path):
        self.credentials_path = Path(credentials_path)
        self.db = None
        self._initialize()

    def _initialize(self):
        target_key = self.credentials_path
        if not target_key.exists():
            root_dir = target_key.parent
            matched = list(root_dir.glob("*firebase-adminsdk*.json"))
            if matched:
                target_key = matched[0]
            else:
                raise FileNotFoundError(
                    f"File service account Firebase tidak ditemukan di: {self.credentials_path}"
                )

        if not firebase_admin._apps:
            cred = credentials.Certificate(str(target_key))
            firebase_admin.initialize_app(cred)

        self.db = firestore.client()

    def get_db(self):
        if self.db is None:
            self._initialize()
        return self.db

