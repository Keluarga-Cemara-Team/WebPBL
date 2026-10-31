# 🌐 AntiBurnout - WebPBL (Admin Data Entry & Dataset Management Portal)

> **Portal Administrator untuk Penginputan & Kurasi Dataset Primer** berbasis **Flask** dengan tampilan **phpMyAdmin Classic Theme** dan arsitektur **Clean Architecture (Uncle Bob)**. Terhubung langsung dengan backend cloud **Google Cloud Firestore (Firebase)** untuk sinkronisasi multi-platform dengan aplikasi mobile (**MobilePBL**), dan terintegrasi dengan modul prediksi **MachineLearningPBL**.

---

## 📌 Daftar Isi
- [Arsitektur Sistem & Alur Kerja](#-arsitektur-sistem--alur-kerja)
- [Peta Struktur Folder](#-peta-struktur-folder)
- [Integrasi Firebase Cloud Firestore](#-integrasi-firebase-cloud-firestore)
- [Panduan Kustomisasi untuk Programmer](#-panduan-kustomisasi-untuk-programmer)
  - [1. Menambah / Mengubah Pertanyaan Kuesioner](#1-menambah--mengubah-pertanyaan-kuesioner)
  - [2. Menghubungkan ke API Asli MachineLearningPBL](#2-menghubungkan-ke-api-asli-machinelearningpbl)
  - [3. Mengganti Database Engine (Firestore / SQLite / MySQL)](#3-mengganti-database-engine-firestore--sqlite--mysql)
  - [4. Mengubah Tampilan Desain / UI](#4-mengubah-tampilan-desain--ui)
- [Kontrak Integrasi Data (API Contract)](#-kontrak-integrasi-data-api-contract)
- [Cara Instalasi & Menjalankan](#-cara-instalasi--menjalankan)
- [Pengujian Otomatis (Testing)](#-pengujian-otomatis-testing)

---

## 🏛️ Arsitektur Sistem & Alur Kerja

Aplikasi ini mematuhi prinsip **Dependency Rule**: *Lapisan dalam (Domain & Use Cases) tidak boleh bergantung pada lapisan luar (Database/Framework)*.

```text
               ┌────────────────────────────────────────────────────────┐
               │                  PRESENTATION LAYER                    │
               │   • Web Controllers: main_controller, assessment       │
               │   • Views (Templates phpMyAdmin) & Assets (CSS & JS)   │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           ▼ (Memanggil)
               ┌────────────────────────────────────────────────────────┐
               │                    USE CASES LAYER                     │
               │   • SubmitAssessmentUseCase                            │
               │   • ExportDatasetUseCase                               │
               │   • GetAssessmentHistoryUseCase                        │
               └─────────────┬────────────────────────────┬─────────────┘
                             │                            │
                             ▼ (Memakai)                  ▼ (Bergantung pada)
┌──────────────────────────────────────┐   ┌────────────────────────────┐
│             DOMAIN LAYER             │   │      INTERFACES (PORTS)    │
│  • RespondentAssessment (Entity)     │   │  • IAssessmentRepository   │
│  • Validasi Aturan Bisnis Murni      │   │  • IMLPredictorService     │
└──────────────────────────────────────┘   └──────────────▲─────────────┘
                                                          │
                                           Implements     │
               ┌──────────────────────────────────────────┴─────────────┐
               │                 INFRASTRUCTURE LAYER                   │
               │   • FirestoreAssessmentRepository (Firebase Cloud)     │
               │   • SQLiteAssessmentRepository (Local SQLite Fallback) │
               │   • HttpMLPredictorService (Call MachineLearningPBL)   │
               └────────────────────────────────────────────────────────┘
```

---

## 📂 Peta Struktur Folder & Penjelasan Lengkap

```text
WebPBL/
├── run.py                               # 🚀 Entry point aplikasi (Jalankan: python run.py)
├── requirements.txt                     # 📦 Daftar dependensi Python (Flask, firebase-admin, requests)
├── serviceAccountKey.json               # 🔑 Kunci privat Firebase Admin SDK (Dilindungi .gitignore)
├── .env.example                         # ⚙️ Template variabel lingkungan (PORT, ML_API_URL, dll.)
├── .gitignore                           # 🙈 Mengabaikan file sensitif (*firebase*.json, .env, *.db)
├── README.md                            # 📖 Dokumentasi teknis & panduan pengembang
│
├── data/
│   └── antiburnout.db                   # 🗄️ File Database SQLite lokal (cadangan offline fallback)
│
└── app/
    ├── __init__.py                      # 🏭 [APPLICATION FACTORY] DI Wiring & Smart Auto-Switch Database
    ├── config.py                        # ⚙️ [CONFIG] Konfigurasi environment (FIREBASE_KEY, ML_API_URL)
    │
    ├── core/                            # 🧠 [1. CORE DOMAIN LAYER] (Logika Murni - Tanpa dependensi Framework)
    │   ├── entities/                    # -- Data Model Domain --
    │   │   ├── __init__.py
    │   │   └── assessment.py            # Objek RespondentAssessment & aturan validasi data primer
    │   │
    │   ├── interfaces/                  # -- Ports / Kontrak Abstrak --
    │   │   ├── __init__.py
    │   │   ├── repositories.py          # Interface IAssessmentRepository (save, find_all, find_by_id)
    │   │   └── ml_service.py            # Interface IMLPredictorService (predict_burnout)
    │   │
    │   └── use_cases/                   # -- Use Cases (Skenario Bisnis Aplikasi) --
    │       ├── __init__.py
    │       ├── submit_assessment.py     # SubmitAssessmentUseCase: Form -> Validasi -> ML -> Firestore
    │       ├── export_dataset.py        # ExportDatasetUseCase: Ekstraksi seluruh responden ke CSV
    │       └── get_assessment_history.py# GetAssessmentHistoryUseCase: Riwayat data & ringkasan metrik
    │
    ├── infrastructure/                  # 🔌 [2. INFRASTRUCTURE LAYER] (Detail Teknis & External Service)
    │   ├── db/
    │   │   ├── __init__.py
    │   │   ├── firebase_client.py       # 🔥 Inisialisasi Google Cloud Firestore via Firebase Admin SDK
    │   │   └── sqlite_client.py         # 🗄️ Inisialisasi engine SQLite lokal (cadangan offline)
    │   │
    │   ├── repositories/
    │   │   ├── __init__.py
    │   │   ├── firestore_assessment_repo.py # 🔥 Implementasi IAssessmentRepository via Cloud Firestore
    │   │   └── sqlite_assessment_repo.py    # 🗄️ Implementasi IAssessmentRepository via SQLite
    │   │
    │   └── external/
    │       ├── __init__.py
    │       └── http_ml_service.py       # Implementasi konkrit IMLPredictorService ke MachineLearningPBL
    │
    └── presentation/                    # 🖥️ [3. PRESENTATION LAYER] (Tampilan phpMyAdmin UI & Routing)
        ├── web/                         # -- Controllers (Flask Blueprints) --
        │   ├── __init__.py
        │   ├── main_controller.py       # Rute: / (Admin Dashboard) dan /healthz (Health Check)
        │   └── assessment_controller.py # Rute: /assessment (Admin Entry, Dataset Table, Export CSV)
        │
        ├── static/                      # -- Aset Tampilan Statis --
        │   ├── css/
        │   │   └── main.css             # Tema phpMyAdmin Classic (Header abu-abu, sidebar pohon, form grid)
        │   └── js/
        │       └── main.js              # Interaktivitas slider kuesioner real-time
        │
        └── templates/                   # -- Jinja2 HTML Views --
            ├── base.html                # Template kerangka induk phpMyAdmin (Sidebar + Top Tabs)
            ├── main/
            │   └── index.html           # Admin Server Dashboard (4 Panel phpMyAdmin)
            └── assessment/
                ├── form.html            # Halaman Admin Data Entry (Insert format SQL table)
                ├── result.html          # Halaman Hasil Evaluasi Skor Burnout (SQL execution notice)
                └── dataset.html         # Halaman Browse Table (Tabel rekaman dataset + Export CSV)
```

---

### 🔄 Alur Perjalanan Data (*End-to-End Data Flow*)

```text
1. [Admin] Mengisi formulir data kuesioner di browser
       │
       ▼ (HTTP POST /assessment/submit)
2. [presentation/web/assessment_controller.py] 
       Menerima request HTTP -> meneruskan payload ke Use Case
       │
       ▼ (execute raw_data)
3. [core/use_cases/submit_assessment.py] 
       Orkestrator logika bisnis:
       ├─► 4. [core/entities/assessment.py] Memvalidasi aturan domain (jam kerja 1-24h, skala stres 1-5)
       ├─► 5. [infrastructure/external/http_ml_service.py] Meminta inferensi skor ke MachineLearningPBL
       └─► 6. [infrastructure/repositories/firestore_assessment_repo.py] 
              Menyimpan dokumen ke koleksi 'assessments' di Google Cloud Firestore
       │
       ▼ (Mengembalikan objek Entity & Skor Burnout)
7. [presentation/templates/assessment/result.html]
       Merender status eksekusi berhasil dan detail inferensi ke layar Admin
```

---

## 🔥 Integrasi Firebase Cloud Firestore

Proyek ini menggunakan **Google Cloud Firestore** sebagai database backend terpusat.

### 1. Sinkronisasi Multi-Platform (PBL Ecosystem)
* **WebPBL (Admin Portal):** Petugas admin menginput dan mengurasi dataset primer langsung ke koleksi cloud Firestore menggunakan `firebase-admin` (Python).
* **MobilePBL (Flutter App):** Aplikasi mobile pengguna dapat langsung membaca (*real-time listener*) data profil dan riwayat skor burnout dari koleksi Firestore yang sama.

### 2. Struktur Koleksi di Firestore

#### A. Koleksi `assessments` (Data Primer Responden & Skor ML)
```json
// Path: /assessments/{autoDocumentId}
{
  "full_name": "Ahmad Fauzi",
  "role": "Kesehatan / Medis",
  "work_hours": 10.0,
  "sleep_hours": 5.0,
  "stress_level": 5,
  "workload_feeling": 5,
  "physical_fatigue": 5,
  "notes": "Shift malam berturut-turut",
  "burnout_score": 85.0,
  "burnout_level": "Tinggi (High Risk / Burnout)",
  "recommendation": "Tingkat stres tinggi terdeteksi...",
  "operator": "admin@localhost",
  "created_at": "2024-11-01 00:10:00"
}
```

#### B. Koleksi `users` (Pengguna & Operator)
```json
// Path: /users/{userId}
{
  "full_name": "Administrator PBL",
  "email": "admin@antiburnout.com",
  "role": "admin",
  "division": "Pusat Riset PBL",
  "is_active": true,
  "created_at": "2024-11-01 00:00:00"
}
```

### 3. Smart Auto-Switching Database
Di dalam `app/__init__.py`, sistem secara otomatis mendeteksi ketersediaan kunci:
* **Ada file `serviceAccountKey.json` / `*firebase-adminsdk*.json`:** Aplikasi otomatis berjalan menggunakan **Google Cloud Firestore**.
* **Tidak ada kunci Firebase:** Aplikasi otomatis *fallback* menggunakan **SQLite lokal** (`data/antiburnout.db`) sehingga tidak akan *crash* saat dijalankan di lingkungan pengujian tanpa internet.

---

## 🛠️ Panduan Kustomisasi untuk Programmer

### 1. Menambah / Mengubah Pertanyaan Kuesioner
1. **Tambahkan atribut di Domain Entity** (`app/core/entities/assessment.py`).
2. **Perbarui mapping di Repository** (`app/infrastructure/repositories/firestore_assessment_repo.py` pada method `save()` dan `_doc_to_entity()`).
3. **Tambahkan baris kolom di Form HTML** (`app/presentation/templates/assessment/form.html`).
4. **Tangkap parameter di Controller** (`app/presentation/web/assessment_controller.py`).

### 2. Menghubungkan ke API Asli MachineLearningPBL
1. Buka file `.env`.
2. Arahkan variabel `ML_API_URL` ke endpoint ML tim Anda:
   ```env
   ML_API_URL=http://127.0.0.1:8000/predict
   ```
3. Jika modul ML belum siap, fitur *fallback simulation* otomatis aktif memberikan kalkulasi perkiraan.

### 3. Mengganti Database Engine (Firestore / SQLite / MySQL)
Karena arsitektur menggunakan *Repository Pattern*, Anda hanya perlu membuat satu adapter repository baru yang mengimplementasikan `IAssessmentRepository`, lalu menyuntikkannya (*Dependency Injection*) pada `app/__init__.py`. Lapisan Controller dan Template Jinja2 tidak perlu diubah sama sekali.

### 4. Mengubah Tampilan Desain / UI
* Desain tema phpMyAdmin (warna palet, panel card, tombol) diatur terpusat di [app/presentation/static/css/main.css](file:///c:/laragon/www/AntiBurnout/WebPBL/app/presentation/static/css/main.css).
* Tata letak navigasi sidebar dan tab dikelola di [app/presentation/templates/base.html](file:///c:/laragon/www/AntiBurnout/WebPBL/app/presentation/templates/base.html).

---

## 🤝 Kontrak Integrasi Data (API Contract)

### Format JSON yang Dikirim ke `MachineLearningPBL`:
```json
{
  "work_hours": 9.5,
  "sleep_hours": 6.0,
  "stress_level": 4,
  "workload_feeling": 4,
  "physical_fatigue": 3
}
```

### Format JSON yang Diharapkan Kembali dari `MachineLearningPBL`:
```json
{
  "burnout_score": 78.5,
  "burnout_level": "Tinggi (High Risk / Burnout)",
  "badge_class": "danger",
  "recommendation": "Tingkat stres dan jam kerja tinggi terdeteksi. Segera lakukan evaluasi beban kerja."
}
```

---

## 🚀 Cara Instalasi & Menjalankan

### Prasyarat
- Python 3.10+ terpasang di sistem.
- File kredensial Firebase `serviceAccountKey.json` berada di folder root `WebPBL/`.

### Langkah Menjalankan:
1. **Masuk ke direktori WebPBL:**
   ```bash
   cd c:\laragon\www\AntiBurnout\WebPBL
   ```
2. **Install dependensi:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Jalankan server aplikasi:**
   ```bash
   python run.py
   ```
4. **Buka di peramban:**
   - 🏠 **Admin Dashboard:** [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
   - 📝 **Admin Data Entry Form:** [http://127.0.0.1:5000/assessment/](http://127.0.0.1:5000/assessment/)
   - 📋 **Browse Dataset & Export CSV:** [http://127.0.0.1:5000/assessment/dataset](http://127.0.0.1:5000/assessment/dataset)
   - 💓 **Health Check API:** [http://127.0.0.1:5000/healthz](http://127.0.0.1:5000/healthz)

---

## 🧪 Pengujian Otomatis (Testing)

Jalankan perintah berikut untuk menguji koneksi Cloud Firestore dan seluruh use case:

```bash
python -c "from app import create_app; app = create_app(); client = app.test_client(); r = client.get('/healthz'); assert r.status_code == 200; print('Engine:', app.db_engine_name); print('Semua Pengujian Sistem Sukses!')"
```
