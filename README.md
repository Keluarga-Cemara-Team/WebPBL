# 🌐 AntiBurnout - WebPBL (Frontend & Data Collection)

> **Antarmuka Pengguna & Pengumpulan Dataset Primer** berbasis **Flask** yang menerapkan **Clean Architecture (Uncle Bob)**. Dirancang khusus untuk memisahkan aturan bisnis survei dari detail teknis database dan integrasi ke modul Machine Learning (**MachineLearningPBL**).

---

## 📌 Daftar Isi
- [Arsitektur Sistem & Alur Kerja](#-arsitektur-sistem--alur-kerja)
- [Peta Struktur Folder](#-peta-struktur-folder)
- [Panduan Kustomisasi untuk Programmer](#-panduan-kustomisasi-untuk-programmer)
  - [1. Menambah / Mengubah Pertanyaan Kuesioner](#1-menambah--mengubah-pertanyaan-kuesioner)
  - [2. Menghubungkan ke API Asli MachineLearningPBL](#2-menghubungkan-ke-api-asli-machinelearningpbl)
  - [3. Mengganti Database (SQLite ke MySQL / PostgreSQL)](#3-mengganti-database-sqlite-ke-mysql--postgresql)
  - [4. Mengubah Tampilan Desain / UI](#4-mengubah-tampilan-desain--ui)
- [Kontrak Integrasi Data (API Contract)](#-kontrak-integrasi-data-api-contract)
- [Cara Instalasi & Menjalankan](#-cara-instalasi--menjalankan)
- [Pengujian Otomatis (Testing)](#-pengujian-otomatis-testing)

---

## 🏛️ Arsitektur Sistem & Alur Kerja

Aplikasi ini mematuhi prinsip **Dependency Rule**: *Lapisan dalam tidak boleh bergantung pada lapisan luar*.

```text
               ┌────────────────────────────────────────────────────────┐
               │                  PRESENTATION LAYER                    │
               │   • Web Controllers: main_controller, assessment       │
               │   • Views (Templates) & Assets (Vanilla CSS & JS)      │
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
               │   • SQLiteAssessmentRepository (data/antiburnout.db)   │
               │   • HttpMLPredictorService (Call MachineLearningPBL)   │
               └────────────────────────────────────────────────────────┘
```

---

## 📂 Peta Struktur Folder & Penjelasan Lengkap

Berikut adalah peta struktur seluruh file dan direktori di dalam **WebPBL** beserta perannya masing-masing:

```text
WebPBL/
├── run.py                               # 🚀 Entry point aplikasi (Jalankan: python run.py)
├── requirements.txt                     # 📦 Daftar dependensi Python (Flask, python-dotenv)
├── .env.example                         # ⚙️ Template variabel lingkungan (PORT, ML_API_URL, dll.)
├── .gitignore                           # 🙈 Konfigurasi file yang diabaikan Git
├── README.md                            # 📖 Dokumentasi teknis & panduan pengembang
│
├── data/
│   └── antiburnout.db                   # 🗄️ File Database SQLite lokal (dibuat otomatis)
│
└── app/
    ├── __init__.py                      # 🏭 [APPLICATION FACTORY] Inisialisasi Flask & Dependency Injection
    ├── config.py                        # ⚙️ [CONFIG] Konfigurasi environment (DB_PATH, ML_API_URL)
    │
    ├── core/                            # 🧠 [1. CORE DOMAIN LAYER] (Logika Murni - Tanpa dependensi Flask/DB)
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
    │       ├── submit_assessment.py     # SubmitAssessmentUseCase: Orkestrasi Form -> Validasi -> ML -> Simpan DB
    │       ├── export_dataset.py        # ExportDatasetUseCase: Ekstraksi seluruh responden ke format CSV
    │       └── get_assessment_history.py# GetAssessmentHistoryUseCase: Riwayat data & ringkasan metrik
    │
    ├── infrastructure/                  # 🔌 [2. INFRASTRUCTURE LAYER] (Detail Teknis & External Service)
    │   ├── db/
    │   │   ├── __init__.py
    │   │   └── sqlite_client.py         # Koneksi engine SQLite & inisialisasi tabel 'assessments'
    │   │
    │   ├── repositories/
    │   │   ├── __init__.py
    │   │   └── sqlite_assessment_repo.py# Implementasi konkrit IAssessmentRepository via SQLite
    │   │
    │   └── external/
    │       ├── __init__.py
    │       └── http_ml_service.py       # Implementasi konkrit IMLPredictorService via HTTP ke MachineLearningPBL
    │
    └── presentation/                    # 🖥️ [3. PRESENTATION LAYER] (Tampilan Antarmuka & Routing Web)
        ├── web/                         # -- Controllers (Flask Blueprints) --
        │   ├── __init__.py
        │   ├── main_controller.py       # Rute: / (Beranda) dan /healthz (Health Check)
        │   └── assessment_controller.py # Rute: /assessment (Form, Submit, Dataset, Export CSV, API JSON)
        │
        ├── static/                      # -- Aset Tampilan Statis --
        │   ├── css/
        │   │   └── main.css             # Desain antarmuka (Dark mode modern, card, grid form, badges)
        │   └── js/
        │       └── main.js              # Interaktivitas slider kuesioner real-time
        │
        └── templates/                   # -- Jinja2 HTML Views --
            ├── base.html                # Template kerangka induk (Navbar, Footer, Notifikasi)
            ├── main/
            │   └── index.html           # Halaman Beranda (Pengenalan Proyek AntiBurnout)
            └── assessment/
                ├── form.html            # Halaman Formulir Kuesioner Dataset Primer
                ├── result.html          # Halaman Hasil Evaluasi Skor Burnout & Saran
                └── dataset.html         # Halaman Tabel Kumpulan Dataset Primer + Tombol Download CSV
```

---

### 🔄 Alur Perjalanan Data (*End-to-End Data Flow*)

Agar lebih mudah dibayangkan, berikut adalah alur ketika seorang responden mengisi formulir di web:

```text
1. [User] Mengisi formulir kuesioner di browser
       │
       ▼ (HTTP POST /assessment/submit)
2. [presentation/web/assessment_controller.py] 
       Menerima request HTTP -> meneruskan payload ke Use Case
       │
       ▼ (execute raw_data)
3. [core/use_cases/submit_assessment.py] 
       Orkestrator logika bisnis:
       ├─► 4. [core/entities/assessment.py] Memvalidasi batas input (misal jam kerja 1-24h)
       ├─► 5. [infrastructure/external/http_ml_service.py] Mengirim data ke MachineLearningPBL
       └─► 6. [infrastructure/repositories/sqlite_assessment_repo.py] Menyimpan ke database SQLite
       │
       ▼ (Mengembalikan objek Entity & Hasil Prediksi)
7. [presentation/templates/assessment/result.html]
       Merender kartu hasil evaluasi tingkat risiko burnout ke layar pengguna
```

---

## 🛠️ Panduan Kustomisasi untuk Programmer

Clean Architecture dirancang agar **sangat mudah dikustomisasi** tanpa merusak bagian lain. Berikut panduan skenario umum:

### 1. Menambah / Mengubah Pertanyaan Kuesioner
Jika Anda ingin menambahkan pertanyaan baru (misalnya: `umur` atau `gender`):

1. **Tambahkan field di Domain Entity** (`app/core/entities/assessment.py`):
   ```python
   @dataclass
   class RespondentAssessment:
       full_name: str
       age: int  # <-- Field baru
       ...
       def validate(self):
           if self.age < 15:
               raise ValueError("Usia minimal 15 tahun.")
   ```
2. **Perbarui Skema Tabel & Query Repository** (`app/infrastructure/repositories/sqlite_assessment_repo.py` dan `sqlite_client.py`):
   * Tambahkan kolom `age INTEGER` pada query `CREATE TABLE` dan `INSERT INTO`.
3. **Tambahkan Input pada Tampilan Form** (`app/presentation/templates/assessment/form.html`):
   ```html
   <div class="form-group">
       <label for="age">Usia Responden</label>
       <input type="number" id="age" name="age" class="form-control" required>
   </div>
   ```
4. **Tangkap di Controller** (`app/presentation/web/assessment_controller.py`):
   * Tambahkan `"age": request.form.get("age", type=int)` ke dalam dictionary `raw_data`.

---

### 2. Menghubungkan ke API Asli MachineLearningPBL
Secara *default*, sistem memiliki fitur **fallback simulation**. Jika server ML belum aktif, sistem tetap berjalan normal dengan kalkulasi perkiraan.

Ketika tim **MachineLearningPBL** sudah siap dengan modelnya:
1. Buka file `.env` (atau buat dari `.env.example`).
2. Arahkan variabel `ML_API_URL` ke endpoint ML mereka:
   ```env
   ML_API_URL=http://127.0.0.1:8000/predict
   ```
3. Jika tim ML memerlukan format JSON khusus, sesuaikan *payload mapping* di:
   [app/infrastructure/external/http_ml_service.py](file:///c:/laragon/www/AntiBurnout/WebPBL/app/infrastructure/external/http_ml_service.py) pada method `predict_burnout()`.

---

### 3. Mengganti Database (SQLite ke MySQL / PostgreSQL)
Karena arsitektur ini menggunakan pola *Repository Pattern*:
1. Buat file baru di `app/infrastructure/repositories/mysql_assessment_repo.py`.
2. Implementasikan kelas yang mewarisi `IAssessmentRepository`:
   ```python
   from app.core.interfaces.repositories import IAssessmentRepository

   class MySQLAssessmentRepository(IAssessmentRepository):
       def save(self, assessment): ...
       def find_all(self): ...
       def find_by_id(self, id): ...
   ```
3. Ubah **1 baris saja** pada Dependency Injection di [app/\_\_init\_\_.py](file:///c:/laragon/www/AntiBurnout/WebPBL/app/__init__.py):
   ```python
   # Ganti SQLiteAssessmentRepository dengan MySQLAssessmentRepository:
   assessment_repo = MySQLAssessmentRepository(...)
   ```
   *(Lapisan Controller, Use Case, dan Template tidak perlu diubah sama sekali!)*

---

### 4. Mengubah Tampilan Desain / UI
* **Styling Warna & Komponen:** Seluruh token warna, margin, dan komponen card diatur di satu file: [app/presentation/static/css/main.css](file:///c:/laragon/www/AntiBurnout/WebPBL/app/presentation/static/css/main.css).
* **Navigasi & Header:** Dikelola di [app/presentation/templates/base.html](file:///c:/laragon/www/AntiBurnout/WebPBL/app/presentation/templates/base.html).

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

### Langkah-langkah:
1. **Masuk ke folder WebPBL:**
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
4. **Akses antarmuka web di peramban:**
   - 🏠 **Beranda:** [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
   - 📝 **Input Kuesioner:** [http://127.0.0.1:5000/assessment/](http://127.0.0.1:5000/assessment/)
   - 📊 **Dataset & Unduh CSV:** [http://127.0.0.1:5000/assessment/dataset](http://127.0.0.1:5000/assessment/dataset)
   - 💓 **Health Check API:** [http://127.0.0.1:5000/healthz](http://127.0.0.1:5000/healthz)

---

## 🧪 Pengujian Otomatis (Testing)

Untuk memastikan seluruh use case, validasi domain, dan database berjalan normal, jalankan perintah uji cepat berikut:

```bash
python -c "from app import create_app; app = create_app(); client = app.test_client(); r = client.get('/healthz'); assert r.status_code == 200; print('Semua Pengujian Sistem Sukses!')"
```
