"""
Standalone ML Microservice API (Gaussian Naive Bayes)
Menyediakan endpoint HTTP di http://127.0.0.1:8000/predict untuk WebPBL
berdasarkan model Gaussian Naive Bayes dari notebook NB_AntiBurnout_Gaussian.ipynb.
Aman dan tanpa mengubah kode sumber asli di direktori project lainnya.
"""

import sys
import os
from pathlib import Path
from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.naive_bayes import GaussianNB

# Pastikan console Windows utf-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

app = Flask(__name__)

# Jalur dataset asli (Hanya dibaca / Read-Only, tanpa mengubah isi file)
DATASET_PATH = Path(r"D:\My Files\File Penting\MACHINE_LEARNING_PBL_REPO\MachineLearningPBL\RandomForest\burnout_dataset1.csv")

# Encoding mapping persis seperti di NB_AntiBurnout_Gaussian.ipynb
ENCODING_MAPS = {
    'Remote_Work': {'No': 0, 'Hybrid': 1, 'Yes': 2},
    'Sleep_Quality': {'Excellent': 0, 'Good': 1, 'Average': 2, 'Poor': 3},
    'Stress_Level': {'Low': 0, 'Moderate': 1, 'High': 2},
    'Exercise_Frequency': {'Daily': 0, 'Weekly': 1, 'Rarely': 2, 'Never': 3},
    'Alcohol_Consumption': {'No': 0, 'Yes': 1},
    'Smoking': {'No': 0, 'Yes': 1},
    'Healthy_Diet': {'No': 1, 'Yes': 0},
    'Chronic_Stress': {'No': 0, 'Yes': 1},
    'Family_History_Mental_Illness': {'No': 0, 'Yes': 1},
    'Therapy_Attendance': {'No': 1, 'Yes': 0},
    'Support_System': {'Poor': 3, 'Average': 2, 'Good': 1, 'Excellent': 0},
    'Mental_Health_Status': {'Healthy': 0, 'Needs Attention': 1, 'Critical': 2}
}

TARGET_MAP = {0: 'Low', 1: 'Moderate', 2: 'High'}

print("=" * 65)
print(">> [ML Server] Memuat dataset dan melatih model Gaussian Naive Bayes...")
if not DATASET_PATH.exists():
    raise FileNotFoundError(f"Dataset tidak ditemukan di: {DATASET_PATH}")

# Baca dataset untuk melatih model GaussianNB
df = pd.read_csv(DATASET_PATH, nrows=5000)

y = df['Burnout_Risk'].map({'Low': 0, 'Moderate': 1, 'High': 2})

numeric_cols = list(df.select_dtypes(include='number').columns.drop(['Person_ID', 'Burnout_Score'], errors='ignore'))
cat_cols = [c for c in ENCODING_MAPS.keys() if c in df.columns]
FEATURE_COLS = numeric_cols + cat_cols

X = df[FEATURE_COLS].copy()
for col, mapping in ENCODING_MAPS.items():
    if col in X.columns:
        X[col] = X[col].map(mapping)

MEAN_IMPUTATION = X.mean()
X = X.fillna(MEAN_IMPUTATION)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

model = GaussianNB(var_smoothing=1e-9)
model.fit(X_scaled, y)

print(">> [ML Server] Model GaussianNB & Scaler BERHASIL dilatih!")
print(f">> [ML Server] Fitur aktif: {len(FEATURE_COLS)} kolom | Target: Burnout_Risk")
print("=" * 65)

@app.route("/", methods=["GET"])
@app.route("/healthz", methods=["GET"])
def health_check():
    return jsonify({
        "status": "online",
        "service": "MachineLearningPBL-Service",
        "algorithm": "Gaussian Naive Bayes (GaussianNB)",
        "features_count": len(FEATURE_COLS),
        "endpoint": "/predict"
    }), 200

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json(force=True) or {}
        
        # Bangun vector input sesuai FEATURE_COLS
        row_dict = {}
        for col in FEATURE_COLS:
            # Cari di data (case-insensitive)
            val = None
            for k in (col, col.lower(), col.upper()):
                if k in data:
                    val = data[k]
                    break
            
            # Jika kolom kategorikal, lakukan mapping
            if col in ENCODING_MAPS:
                if val is not None and str(val) in ENCODING_MAPS[col]:
                    row_dict[col] = ENCODING_MAPS[col][str(val)]
                else:
                    row_dict[col] = MEAN_IMPUTATION.get(col, 0)
            else:
                # Kolom numerik
                try:
                    row_dict[col] = float(val) if val not in (None, "") else MEAN_IMPUTATION.get(col, 0)
                except (ValueError, TypeError):
                    row_dict[col] = MEAN_IMPUTATION.get(col, 0)

        # Ubah ke DataFrame dan standarisasi
        input_df = pd.DataFrame([row_dict], columns=FEATURE_COLS)
        input_scaled = scaler.transform(input_df)

        # Prediksi probabilitas dan kelas
        pred_class_idx = int(model.predict(input_scaled)[0])
        probas = model.predict_proba(input_scaled)[0] # [P(Low), P(Moderate), P(High)]

        pred_risk = TARGET_MAP.get(pred_class_idx, "Moderate")
        
        # Hitung skor burnout proporsional (0 - 100) berbasis probabilitas
        p_low = float(probas[0]) if len(probas) > 0 else 0.33
        p_mod = float(probas[1]) if len(probas) > 1 else 0.33
        p_high = float(probas[2]) if len(probas) > 2 else 0.33
        burnout_score = round(float((p_mod * 50.0) + (p_high * 100.0)), 1)
        burnout_score = max(5.0, min(burnout_score, 98.0))

        if pred_risk == "High":
            status = "Critical"
            badge = "danger"
            rec = "Tingkat risiko burnout tinggi terdeteksi oleh Gaussian Naive Bayes. Segera kurangi jam kerja dan lakukan evaluasi beban tugas."
        elif pred_risk == "Moderate":
            status = "Needs Attention"
            badge = "warning"
            rec = "Terindikasi kelelahan kerja sedang. Atur ritme istirahat secara teratur dan batasi lembur harian."
        else:
            status = "Healthy"
            badge = "success"
            rec = "Pola kerja dan kesehatan mental tergolong prima. Pertahankan keseimbangan aktivitas dan waktu istirahat."

        return jsonify({
            "is_simulation": False,
            "model_name": "Gaussian Naive Bayes (GaussianNB)",
            "burnout_score": burnout_score,
            "burnout_risk": pred_risk,
            "burnout_level": f"{pred_risk} (AI GaussianNB Prediction)",
            "mental_health_status": status,
            "ai_wellness_recommendation": rec,
            "badge_class": badge,
            "probabilities": {
                "low": round(p_low, 3),
                "moderate": round(p_mod, 3),
                "high": round(p_high, 3)
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f">> [ML Server] Berjalan di http://127.0.0.1:{port} (Endpoint: http://127.0.0.1:{port}/predict)")
    app.run(host="127.0.0.1", port=port, debug=False)

