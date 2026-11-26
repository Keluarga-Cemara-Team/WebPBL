document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.getElementById("dataset-file");
    const filename = document.getElementById("dataset-filename");
    const status = document.getElementById("dataset-status");
    const results = document.getElementById("dataset-results");
    const previewHead = document.getElementById("preview-head");
    const previewBody = document.getElementById("preview-body");
    const typesBody = document.getElementById("types-body");
    const btnLoadDb = document.getElementById("btn-load-db");
    const btnSaveDb = document.getElementById("btn-save-db");
    const btnSaveDbSummary = document.getElementById("btn-save-db-summary");
    const btnViewDataset = document.getElementById("btn-view-dataset");
    const dbSaveFeedback = document.getElementById("db-save-feedback");
    const targetReadiness = document.getElementById("target-readiness");

    // EDA Elements
    const btnEda = document.getElementById("btn-eda");
    const sectionEda = document.getElementById("section-eda");
    const edaTargetBars = document.getElementById("eda-target-bars");
    const edaStatsBody = document.getElementById("eda-stats-body");
    const edaInsightsGrid = document.getElementById("eda-insights-grid");

    // Preprocessing Elements
    const btnPrep = document.getElementById("btn-preprocessing");
    const sectionPrep = document.getElementById("section-preprocessing");
    const btnPrepResetDefault = document.getElementById("btn-prep-reset-default");
    const prepColumnsGrid = document.getElementById("prep-columns-grid");
    const btnColSelectAll = document.getElementById("btn-col-select-all");
    const btnColDeselectAll = document.getElementById("btn-col-deselect-all");
    const btnColRecommend = document.getElementById("btn-col-recommend");
    const prepSelectedColsCount = document.getElementById("prep-selected-cols-count");
    const prepTotalColsCount = document.getElementById("prep-total-cols-count");
    const btnOpenTraining = document.getElementById("btn-train-models");
    const btnRunTraining = document.getElementById("btn-run-training");
    const sectionTraining = document.getElementById("section-training");
    const trainingStatus = document.getElementById("training-status");
    const trainingResults = document.getElementById("training-results");
    const trainingTrainPercent = document.getElementById("training-train-percent");
    const trainingValidationPercent = document.getElementById("training-validation-percent");
    const trainingTestPercent = document.getElementById("training-test-percent");
    const trainingPercentTotal = document.getElementById("training-percent-total");
    const trainingPresets = Array.from(document.querySelectorAll(".training-preset"));
    const trainingClassChart = document.getElementById("training-class-chart");
    const trainingMetricsBody = document.getElementById("training-metrics-body");
    const trainingConfusionMatrices = document.getElementById("training-confusion-matrices");
    const trainingLeakageAudit = document.getElementById("training-leakage-audit");
    const toggleRawMetrics = document.getElementById("toggle-raw-metrics");
    const trainingVerificationDetails = document.getElementById("training-verification-details");
    const trainingFinalTestSamples = document.getElementById("training-final-test-samples");
    const finalModelBadge = document.getElementById("final-model-badge");
    const finalModelStatusBody = document.getElementById("final-model-status-body");
    const finalModelReconfirmNotice = document.getElementById("final-model-reconfirm-notice");
    const finalizeModelSelect = document.getElementById("finalize-model-select");
    const finalizeConfirmCheck = document.getElementById("finalize-confirm-check");
    const btnSaveFinalModel = document.getElementById("btn-save-final-model");
    const finalizeStatus = document.getElementById("finalize-status");

    const prepOptDedup = document.getElementById("prep-opt-dedup");
    const prepDupsBadge = document.getElementById("prep-dups-badge");
    const prepOptImputeNum = document.getElementById("prep-opt-impute-num");
    const prepOptImputeCat = document.getElementById("prep-opt-impute-cat");
    const prepOptOutlier = document.getElementById("prep-opt-outlier");
    const prepOutliersBadge = document.getElementById("prep-outliers-badge");
    const prepOptEncoding = document.getElementById("prep-opt-encoding");
    const prepEncodingPreview = document.getElementById("prep-encoding-preview");
    const prepOptScaling = document.getElementById("prep-opt-scaling");
    const prepOptSampling = document.getElementById("prep-opt-sampling");
    const prepOptSamplingCustom = document.getElementById("prep-opt-sampling-custom");
    const prepSamplingBadge = document.getElementById("prep-sampling-badge");
    const prepSummaryStatus = document.getElementById("prep-summary-status");
    const btnDownloadCleaned = document.getElementById("btn-download-cleaned");
    const btnGoTraining = document.getElementById("btn-go-training");

    // State cache
    let currentDataset = null;
    let trainingValidationMethod = "cross_validation";
    let detectedOutliersInfo = { totalOutliers: 0, columnsWithOutliers: 0, columnBounds: {} };
    let lastComparisonData = null;
    let lastTrainingRequestPayload = null;
    let lastComparedSignature = null;
    let lastFinalizedSignature = null;

    if (!fileInput || !status || !results) return;

    const setStatus = (message, state = "") => {
        status.textContent = message;
        if (state) status.dataset.state = state;
        else delete status.dataset.state;
    };

    // Parser CSV standar
    const parseCsv = (text) => {
        const rows = [];
        let row = [];
        let cell = "";
        let quoted = false;
        const source = text.replace(/^\uFEFF/, "");

        for (let index = 0; index < source.length; index += 1) {
            const char = source[index];
            if (quoted) {
                if (char === '"' && source[index + 1] === '"') {
                    cell += '"';
                    index += 1;
                } else if (char === '"') {
                    quoted = false;
                } else {
                    cell += char;
                }
            } else if (char === '"' && cell.length === 0) {
                quoted = true;
            } else if (char === ",") {
                row.push(cell);
                cell = "";
            } else if (char === "\n" || char === "\r") {
                if (char === "\r" && source[index + 1] === "\n") index += 1;
                row.push(cell);
                if (row.some((value) => value.trim() !== "") || row.length > 1) rows.push(row);
                row = [];
                cell = "";
            } else {
                cell += char;
            }
        }

        if (quoted) throw new Error("CSV memiliki tanda kutip yang belum ditutup.");
        row.push(cell);
        if (row.some((value) => value.trim() !== "") || row.length > 1) rows.push(row);
        return rows;
    };

    const makeCell = (tag, value, scope) => {
        const cell = document.createElement(tag);
        cell.textContent = value;
        if (scope) cell.scope = scope;
        return cell;
    };

    const detectType = (values) => {
        const present = values.map((value) => (value ?? "").trim()).filter(Boolean);
        if (!present.length) return "Kosong";
        if (present.every((value) => /^(true|false)$/i.test(value))) return "Boolean";
        if (present.every((value) => /^[-+]?\d+$/.test(value))) return "Integer";
        if (present.every((value) => /^[-+]?(?:\d+\.?\d*|\.\d+)$/.test(value))) return "Numerik";
        if (present.every((value) => !Number.isNaN(Date.parse(value)) && /[-/]/.test(value))) return "Tanggal/teks";
        return "Teks";
    };

    const normalizeHeader = (header) => (header || "").trim().toLowerCase().replace(/[^a-z0-9]/g, "");
    const findTargetColumnIndex = (headers) => {
        const riskIndex = headers.findIndex((header) => normalizeHeader(header) === "burnoutrisk");
        if (riskIndex !== -1) return riskIndex;
        return headers.findIndex((header) => normalizeHeader(header) === "burnoutlevel");
    };
    const isTargetColumn = (header, index, targetColumnIndex) =>
        index === targetColumnIndex
        || ["burnoutrisk", "burnoutlevel"].includes(normalizeHeader(header));
    const normalizeBurnoutLabel = (value) => {
        const label = (value ?? "").trim().toLowerCase();
        if (label === "low") return "Low";
        if (label === "moderate") return "Moderate";
        if (label === "high") return "High";
        return null;
    };

    // Render Ringkasan & Pratinjau Dataset Awal
    const renderDataset = (fileOrName, rows) => {
        if (!rows.length || !rows[0].some((value) => value.trim())) {
            throw new Error("CSV tidak memiliki header kolom.");
        }

        const headers = rows[0].map((value) => value.trim());
        if (headers.some((header) => !header)) throw new Error("Nama kolom tidak boleh kosong.");
        if (rows.slice(1).some((values) => values.length > headers.length)) {
            throw new Error("Ada baris yang memiliki kolom lebih banyak dari header.");
        }
        const dataRows = rows.slice(1).map((values) => headers.map((_, index) => values[index] ?? ""));
        const missingByColumn = headers.map((_, column) => dataRows.reduce(
            (count, values) => count + ((values[column] ?? "").trim() === "" ? 1 : 0), 0
        ));
        const targetColumnIndex = findTargetColumnIndex(headers);
        const targetCounts = { Low: 0, Moderate: 0, High: 0 };
        let invalidTargetCount = 0;
        if (targetColumnIndex !== -1) {
            dataRows.forEach((row) => {
                const label = normalizeBurnoutLabel(row[targetColumnIndex]);
                if (label) targetCounts[label] += 1;
                else invalidTargetCount += 1;
            });
        }
        const duplicateRows = new Set();
        const seenRows = new Set();

        dataRows.forEach((values, index) => {
            const signature = JSON.stringify(values.map((value) => (value ?? "").trim()));
            if (seenRows.has(signature)) duplicateRows.add(index);
            else seenRows.add(signature);
        });

        const fname = typeof fileOrName === "string" ? fileOrName : fileOrName.name;
        filename.textContent = fname;
        document.getElementById("summary-filename").textContent = fname;
        document.getElementById("summary-rows").textContent = String(dataRows.length);
        document.getElementById("summary-columns").textContent = String(headers.length);
        const totalMissing = missingByColumn.reduce((a, b) => a + b, 0);
        document.getElementById("summary-missing").textContent = `${totalMissing} nilai kosong`;
        document.getElementById("summary-duplicates").textContent = `${duplicateRows.size} baris`;
        
        document.getElementById("summary-target").textContent = targetColumnIndex === -1
            ? "Tidak ditemukan"
            : `${headers[targetColumnIndex]} (${dataRows.length - invalidTargetCount}/${dataRows.length} label valid)`;

        const candidateFeatureCount = headers.filter((header, index) =>
            !isTargetColumn(header, index, targetColumnIndex) && !isDefaultDroppedColumn(header)
        ).length;
        const missingClasses = Object.entries(targetCounts)
            .filter(([, count]) => count === 0)
            .map(([label]) => label);
        const targetIsReady = targetColumnIndex !== -1
            && missingClasses.length === 0
            && candidateFeatureCount > 0;
        if (targetReadiness) {
            targetReadiness.className = targetIsReady ? "pma-alert-success" : "pma-alert-warning";
            if (targetColumnIndex === -1) {
                targetReadiness.textContent = "Dataset belum memiliki kolom target Burnout_Risk (atau Burnout_Level). Label target tidak akan dibuat otomatis; tambahkan label kelas Low, Moderate, atau High sebelum pelatihan.";
            } else {
                const classSummary = Object.entries(targetCounts)
                    .map(([label, count]) => `${label}: ${count}`)
                    .join(" • ");
                const readinessMessage = targetIsReady
                    ? "Target ditemukan. Label kosong atau di luar kelas yang didukung harus dikecualikan saat pelatihan."
                    : "Dataset belum siap: pastikan label kelas Low, Moderate, High tersedia dan setidaknya satu calon fitur.";
                const classWarning = missingClasses.length
                    ? ` Kelas belum tersedia: ${missingClasses.join(", ")}.`
                    : "";
                targetReadiness.textContent = `${readinessMessage} Distribusi label — ${classSummary}. Label kosong/tidak valid: ${invalidTargetCount}; calon fitur: ${candidateFeatureCount}.`;
                if (classWarning) targetReadiness.textContent += classWarning;
                if (!targetIsReady) targetReadiness.className = "pma-alert-warning";
            }
        }

        previewHead.replaceChildren(...headers.map((header) => makeCell("th", header, "col")));
        previewBody.replaceChildren(...dataRows.slice(0, 10).map((values) => {
            const tr = document.createElement("tr");
            tr.append(...values.map((value) => makeCell("td", value || "—")));
            return tr;
        }));
        document.getElementById("preview-count").textContent = `(${Math.min(dataRows.length, 10)} dari ${dataRows.length} baris)`;

        const columnTypes = headers.map((header, column) => detectType(dataRows.map((values) => values[column])));

        typesBody.replaceChildren(...headers.map((header, column) => {
            const tr = document.createElement("tr");
            tr.append(
                makeCell("td", header),
                makeCell("td", columnTypes[column]),
                makeCell("td", String(missingByColumn[column]))
            );
            return tr;
        }));

        // Simpan state aktif
        currentDataset = {
            filename: fname,
            headers,
            columnTypes,
            dataRows,
            targetColumnIndex,
            missingByColumn,
            duplicateRows,
            totalMissing
        };
        if (sectionTraining) sectionTraining.hidden = true;
        if (trainingResults) trainingResults.hidden = true;
        if (trainingStatus) {
            trainingStatus.textContent = "Muat dataset berlabel lengkap, pilih fitur, lalu jalankan perbandingan.";
            delete trainingStatus.dataset.state;
        }

        // Aktifkan tombol
        if (btnEda) btnEda.disabled = false;
        if (btnPrep) btnPrep.disabled = false;

        // Siapkan kontrol Preprocessing
        initPreprocessingControls();
        invalidateComparisonIfConfigChanged("Dataset baru");

        results.hidden = false;
        setStatus("CSV berhasil dibaca. Anda dapat melihat ringkasan atau membuka tombol EDA & Preprocessing di bawah.", "success");
    };

    // =========================================================================
    // MODUL 1: EDA (Exploratory Data Analysis)
    // =========================================================================
    const runEda = () => {
        if (!currentDataset) return;
        const { headers, dataRows, columnTypes } = currentDataset;

        // 1. Distribusi Target
        const targetColIdx = headers.findIndex(h => /burnout[_\s]?(risk|level)/i.test(h));
        edaTargetBars.innerHTML = "";

        if (targetColIdx !== -1) {
            const counts = { Low: 0, Moderate: 0, High: 0 };
            dataRows.forEach(row => {
                const val = (row[targetColIdx] || "").toLowerCase();
                if (val.includes("high") || val.includes("tinggi") || val.includes("critical")) counts.High += 1;
                else if (val.includes("low") || val.includes("rendah") || val.includes("healthy")) counts.Low += 1;
                else counts.Moderate += 1;
            });

            const total = dataRows.length || 1;
            const items = [
                { label: "Low Risk (Rendah)", count: counts.Low, cls: "eda-bar-fill-low" },
                { label: "Moderate Risk (Sedang)", count: counts.Moderate, cls: "eda-bar-fill-mod" },
                { label: "High Risk (Tinggi)", count: counts.High, cls: "eda-bar-fill-high" }
            ];

            items.forEach(it => {
                const pct = Math.round((it.count / total) * 100);
                const rowDiv = document.createElement("div");
                rowDiv.className = "eda-bar-row";
                rowDiv.innerHTML = `
                    <div class="eda-bar-label">${it.label}</div>
                    <div class="eda-bar-track">
                        <div class="eda-bar-fill ${it.cls}" style="width: ${pct}%;"></div>
                    </div>
                    <div class="eda-bar-meta">${it.count} (${pct}%)</div>
                `;
                edaTargetBars.appendChild(rowDiv);
            });
        } else {
            edaTargetBars.innerHTML = `<div class="pma-badge pma-badge-warning">Kolom target Burnout_Risk tidak terdeteksi di dataset ini.</div>`;
        }

        // 2. Statistik Deskriptif Kolom Numerik
        edaStatsBody.innerHTML = "";
        let numCount = 0;

        headers.forEach((header, colIdx) => {
            const colType = columnTypes[colIdx];
            if (colType === "Numerik" || colType === "Integer") {
                numCount += 1;
                const numbers = dataRows.map(r => parseFloat(r[colIdx])).filter(v => !isNaN(v)).sort((a, b) => a - b);
                if (numbers.length > 0) {
                    const min = numbers[0];
                    const max = numbers[numbers.length - 1];
                    const sum = numbers.reduce((a, b) => a + b, 0);
                    const mean = (sum / numbers.length).toFixed(1);
                    const mid = Math.floor(numbers.length / 2);
                    const median = numbers.length % 2 !== 0 ? numbers[mid] : ((numbers[mid - 1] + numbers[mid]) / 2).toFixed(1);

                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td><strong>${header}</strong></td>
                        <td><span class="pma-badge ${colType === 'Integer' ? 'pma-badge-success' : 'pma-badge-warning'}">${colType}</span></td>
                        <td style="text-align: right; font-family: monospace;">${min}</td>
                        <td style="text-align: right; font-family: monospace; color: #235a81; font-weight: bold;">${mean}</td>
                        <td style="text-align: right; font-family: monospace;">${median}</td>
                        <td style="text-align: right; font-family: monospace;">${max}</td>
                    `;
                    edaStatsBody.appendChild(tr);
                }
            }
        });

        if (numCount === 0) {
            edaStatsBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #777;">Tidak ada fitur numerik yang terdeteksi.</td></tr>`;
        }

        // 3. Wawasan Pola Responden
        const workIdx = headers.findIndex(h => /work[_\s]?hours/i.test(h));
        const sleepIdx = headers.findIndex(h => /sleep[_\s]?hours/i.test(h));
        
        let avgWorkHigh = "-", avgWorkLow = "-", avgSleepHigh = "-", avgSleepLow = "-";

        if (targetColIdx !== -1 && workIdx !== -1) {
            const workHigh = [], workLow = [];
            dataRows.forEach(r => {
                const w = parseFloat(r[workIdx]);
                if (isNaN(w)) return;
                const risk = (r[targetColIdx] || "").toLowerCase();
                if (risk.includes("high") || risk.includes("tinggi")) workHigh.push(w);
                else workLow.push(w);
            });
            if (workHigh.length) avgWorkHigh = (workHigh.reduce((a,b)=>a+b,0)/workHigh.length).toFixed(1) + " jam/mgg";
            if (workLow.length) avgWorkLow = (workLow.reduce((a,b)=>a+b,0)/workLow.length).toFixed(1) + " jam/mgg";
        }

        if (targetColIdx !== -1 && sleepIdx !== -1) {
            const sleepHigh = [], sleepLow = [];
            dataRows.forEach(r => {
                const s = parseFloat(r[sleepIdx]);
                if (isNaN(s)) return;
                const risk = (r[targetColIdx] || "").toLowerCase();
                if (risk.includes("high") || risk.includes("tinggi")) sleepHigh.push(s);
                else sleepLow.push(s);
            });
            if (sleepHigh.length) avgSleepHigh = (sleepHigh.reduce((a,b)=>a+b,0)/sleepHigh.length).toFixed(1) + " jam/hari";
            if (sleepLow.length) avgSleepLow = (sleepLow.reduce((a,b)=>a+b,0)/sleepLow.length).toFixed(1) + " jam/hari";
        }

        edaInsightsGrid.innerHTML = `
            <div class="pma-card" style="margin-bottom: 0;">
                <div class="pma-card-header"><span>⏱️</span><span>Beban Jam Kerja vs Risiko</span></div>
                <div class="pma-card-body">
                    <ul class="pma-list">
                        <li class="pma-list-item">
                            <span>Rata-rata Jam Kerja (High Risk):</span>
                            <strong style="color: #c00000;">${avgWorkHigh}</strong>
                        </li>
                        <li class="pma-list-item">
                            <span>Rata-rata Jam Kerja (Low/Mod):</span>
                            <strong style="color: #274e13;">${avgWorkLow}</strong>
                        </li>
                    </ul>
                </div>
            </div>
            <div class="pma-card" style="margin-bottom: 0;">
                <div class="pma-card-header"><span>🌙</span><span>Durasi Tidur vs Risiko</span></div>
                <div class="pma-card-body">
                    <ul class="pma-list">
                        <li class="pma-list-item">
                            <span>Rata-rata Tidur (High Risk):</span>
                            <strong style="color: #c00000;">${avgSleepHigh}</strong>
                        </li>
                        <li class="pma-list-item">
                            <span>Rata-rata Tidur (Low/Mod):</span>
                            <strong style="color: #274e13;">${avgSleepLow}</strong>
                        </li>
                    </ul>
                </div>
            </div>
        `;

        sectionEda.hidden = false;
        sectionEda.scrollIntoView({ behavior: "smooth", block: "start" });
    };

    // =========================================================================
    // MODUL 2: PREPROCESSING PIPELINE INTERAKTIF
    // =========================================================================

    // Helper mengecek kolom yang di-drop secara default sesuai spesifikasi pipeline ML
    const isDefaultDroppedColumn = (colName) => {
        const norm = normalizeHeader(colName);
        const droppedCols = new Set([
            "burnoutscore",
            "gender",
            "country",
            "occupation",
            "aiwellnessrecommendation",
            "mentalhealthstatus",
            "burnoutrisk",
            "burnoutlevel",
            "education_level",
            "educationlevel",
            "employmentstatus",
            "personid",
            "id",
            "notes",
            "catatan"
        ]);
        return droppedCols.has(norm);
    };

    // Inisialisasi kontrol dan deteksi outlier
    const initPreprocessingControls = () => {
        if (!currentDataset) return;
        const { headers, dataRows, columnTypes, duplicateRows } = currentDataset;

        // Update duplikat badge
        prepDupsBadge.textContent = `${duplicateRows.size} baris`;

        // 1. Render Checkbox Seleksi Kolom (Default mengecualikan kolom target, demografi, & ID)
        prepColumnsGrid.innerHTML = "";
        headers.forEach((h, idx) => {
            const colType = columnTypes[idx];
            const isTarget = isTargetColumn(h, idx, currentDataset.targetColumnIndex);
            const shouldDrop = isTarget || isDefaultDroppedColumn(h);

            const label = document.createElement("label");
            label.className = "prep-col-item";
            label.innerHTML = `
                <input type="checkbox" class="prep-col-check" data-col-idx="${idx}" ${!shouldDrop ? 'checked' : ''} ${isTarget ? "disabled" : ""}>
                <span class="prep-col-name" title="${h}">${h}</span>
                <span class="pma-badge ${colType.startsWith('Int') || colType.startsWith('Num') ? 'pma-badge-warning' : 'pma-badge-success'}" style="font-size: 10px; padding: 1px 4px;">
                    ${colType}
                </span>
                ${isTarget ? '<span class="pma-badge pma-badge-success" style="font-size: 10px; padding: 1px 4px;">Label target; tidak diproses sebagai fitur</span>' : ""}
            `;
            prepColumnsGrid.appendChild(label);
        });

        // Set default imputasi numerik ke Mean
        if (prepOptImputeNum) prepOptImputeNum.value = "mean";

        updateSelectedColsCount();

        // 2. Deteksi Outlier dengan IQR Method
        let totalOutliers = 0;
        let columnsWithOutliers = 0;
        const columnBounds = {};

        headers.forEach((h, colIdx) => {
            const colType = columnTypes[colIdx];
            if (colType === "Numerik" || colType === "Integer") {
                const numbers = dataRows.map(r => parseFloat(r[colIdx])).filter(v => !isNaN(v)).sort((a,b)=>a-b);
                if (numbers.length >= 4) {
                    const q1Idx = Math.floor(numbers.length * 0.25);
                    const q3Idx = Math.floor(numbers.length * 0.75);
                    const q1 = numbers[q1Idx];
                    const q3 = numbers[q3Idx];
                    const iqr = q3 - q1;
                    const lower = q1 - 1.5 * iqr;
                    const upper = q3 + 1.5 * iqr;

                    let outCount = 0;
                    numbers.forEach(v => {
                        if (v < lower || v > upper) outCount += 1;
                    });

                    if (outCount > 0) {
                        totalOutliers += outCount;
                        columnsWithOutliers += 1;
                        columnBounds[colIdx] = { lower, upper, outCount };
                    }
                }
            }
        });

        detectedOutliersInfo = { totalOutliers, columnsWithOutliers, columnBounds };
        if (totalOutliers > 0) {
            prepOutliersBadge.textContent = `${totalOutliers} outlier terdeteksi di ${columnsWithOutliers} kolom`;
            prepOutliersBadge.className = "pma-badge pma-badge-danger";
        } else {
            prepOutliersBadge.textContent = "0 outlier terdeteksi (Data Bersih)";
            prepOutliersBadge.className = "pma-badge pma-badge-success";
        }

        // 3. Render Preview Encoding Kategorikal
        renderEncodingPreview();
        updateSamplingBadge();
    };

    const updateSelectedColsCount = () => {
        const checkboxes = Array.from(prepColumnsGrid.querySelectorAll(".prep-col-check"));
        const checked = checkboxes.filter((checkbox) => checkbox.checked && !checkbox.disabled);
        prepSelectedColsCount.textContent = String(checked.length);
        prepTotalColsCount.textContent = String(checkboxes.filter((checkbox) => !checkbox.disabled).length);
    };

    const getTrainingSplitPercentages = () => {
        const values = [
            Number(trainingTrainPercent.value),
            Number(trainingValidationPercent.value),
            Number(trainingTestPercent.value)
        ];
        if (values.some((value) => !Number.isInteger(value))) return null;
        const [train, validation, test] = values;
        if (trainingValidationMethod === "cross_validation") {
            if (train < 50 || train > 95 || validation !== 0 || test < 5 || test > 50) {
                return null;
            }
            return train + test === 100 ? { train, validation, test } : null;
        }
        if (train < 50 || train > 90 || validation < 5 || validation > 45 || test < 5 || test > 45) {
            return null;
        }
        return train + validation + test === 100 ? { train, validation, test } : null;
    };

    const updateTrainingSplitTotal = () => {
        const validationIsCrossValidation = trainingValidationMethod === "cross_validation";
        trainingValidationPercent.disabled = validationIsCrossValidation;
        trainingValidationPercent.placeholder = validationIsCrossValidation ? "CV" : "5–45";
        trainingTrainPercent.max = validationIsCrossValidation ? "95" : "90";
        trainingTrainPercent.placeholder = validationIsCrossValidation ? "50–95" : "50–90";
        trainingTestPercent.max = validationIsCrossValidation ? "50" : "45";
        trainingTestPercent.placeholder = validationIsCrossValidation ? "5–50" : "5–45";
        const values = [
            Number(trainingTrainPercent.value),
            Number(trainingValidationPercent.value),
            Number(trainingTestPercent.value)
        ];
        if ([trainingTrainPercent, trainingValidationPercent, trainingTestPercent]
            .every((input) => input.value === "")) {
            trainingPercentTotal.textContent = "Pilih atau isi pembagian";
            trainingPercentTotal.className = "pma-badge";
            btnRunTraining.disabled = true;
            return;
        }
        const total = validationIsCrossValidation
            ? values[0] + values[2]
            : values.reduce((sum, value) => sum + (Number.isFinite(value) ? value : 0), 0);
        const valid = getTrainingSplitPercentages() !== null;
        const totalLabel = validationIsCrossValidation ? "Total latih + uji" : "Total";
        const requirement = validationIsCrossValidation
            ? " — latih + uji harus 100% (latih ≥50%, uji ≥5%)"
            : " — harus 100% (latih ≥50%, validasi/uji ≥5%)";
        trainingPercentTotal.textContent = `${totalLabel}: ${total}%${valid ? "" : requirement}`;
        trainingPercentTotal.className = valid ? "pma-badge pma-badge-success" : "pma-badge pma-badge-warning";
        btnRunTraining.disabled = !valid;
    };

    const getSelectedSampleSize = () => {
        if (!prepOptSampling || prepOptSampling.value === "all") return null;
        const raw = prepOptSampling.value === "custom"
            ? Number(prepOptSamplingCustom?.value)
            : Number(prepOptSampling.value);
        if (!Number.isInteger(raw) || raw < 15) return null;
        return raw;
    };

    const updateSamplingBadge = () => {
        if (!prepSamplingBadge) return;
        const totalRows = currentDataset?.dataRows?.length || 0;
        const isCustom = prepOptSampling && prepOptSampling.value === "custom";
        if (prepOptSamplingCustom) {
            prepOptSamplingCustom.hidden = !isCustom;
        }
        const sampleSize = getSelectedSampleSize();
        if (isCustom && sampleSize === null) {
            prepSamplingBadge.textContent = "Isi jumlah sampel (minimal 15 baris)";
            prepSamplingBadge.className = "pma-badge pma-badge-warning";
            return;
        }
        if (sampleSize === null || (totalRows > 0 && sampleSize >= totalRows)) {
            prepSamplingBadge.textContent = totalRows
                ? `Semua baris aktif (${totalRows.toLocaleString("id-ID")} baris)`
                : "Semua baris aktif (Tanpa sampling)";
            prepSamplingBadge.className = "pma-badge pma-badge-success";
        } else {
            prepSamplingBadge.textContent = `Stratified sampling: ${sampleSize.toLocaleString("id-ID")} dari ${totalRows.toLocaleString("id-ID")} baris`;
            prepSamplingBadge.className = "pma-badge pma-badge-warning";
        }
    };

    const getCurrentConfigSignature = () => {
        if (!currentDataset) return "";
        const featureColumns = Array.from(prepColumnsGrid.querySelectorAll(".prep-col-check:checked"))
            .map((checkbox) => currentDataset.headers[Number(checkbox.dataset.colIdx)]);
        return JSON.stringify({
            filename: currentDataset.filename || "",
            rowCount: currentDataset.dataRows ? currentDataset.dataRows.length : 0,
            headers: currentDataset.headers || [],
            featureColumns,
            deduplicate: Boolean(prepOptDedup?.checked),
            numericImputation: prepOptImputeNum?.value,
            categoricalImputation: prepOptImputeCat?.value,
            outlierHandling: prepOptOutlier?.value,
            encoding: prepOptEncoding?.value,
            scaling: prepOptScaling?.value,
            sampleSize: getSelectedSampleSize(),
            validationMethod: trainingValidationMethod,
            trainPercent: trainingTrainPercent?.value,
            validationPercent: trainingValidationPercent?.value,
            testPercent: trainingTestPercent?.value,
        });
    };

    const syncFinalizeButtonState = () => {
        if (!btnSaveFinalModel) return;
        const confirmed = Boolean(finalizeConfirmCheck && finalizeConfirmCheck.checked);
        const hasValidComparison = Boolean(
            lastComparisonData &&
            lastComparedSignature &&
            getCurrentConfigSignature() === lastComparedSignature
        );
        btnSaveFinalModel.disabled = !(confirmed && hasValidComparison);
    };

    const invalidateComparisonIfConfigChanged = (reason = "pengaturan") => {
        if (!currentDataset) return;
        const currentSig = getCurrentConfigSignature();

        if (lastComparedSignature && currentSig !== lastComparedSignature) {
            lastComparisonData = null;
            lastTrainingRequestPayload = null;
            lastComparedSignature = null;
            if (trainingResults) trainingResults.hidden = true;
            if (finalizeConfirmCheck) finalizeConfirmCheck.checked = false;
            if (finalizeStatus) {
                finalizeStatus.hidden = true;
                finalizeStatus.textContent = "";
                delete finalizeStatus.dataset.state;
            }
            if (trainingStatus) {
                trainingStatus.textContent =
                    `⚠️ ${reason} berubah. Hasil perbandingan sebelumnya tidak lagi berlaku — jalankan ulang perbandingan model sebelum menetapkan Model Final.`;
                trainingStatus.dataset.state = "error";
            }
        }

        if (finalModelReconfirmNotice) {
            if (lastFinalizedSignature && currentSig !== lastFinalizedSignature) {
                finalModelReconfirmNotice.hidden = false;
                finalModelReconfirmNotice.innerHTML =
                    `<strong>⚠️ Perlu Ditetapkan Ulang:</strong> ${reason} berubah sejak Model Final terakhir ditetapkan. Jalankan ulang perbandingan model dan tetapkan ulang Model Final.`;
            } else {
                finalModelReconfirmNotice.hidden = true;
            }
        }
        syncFinalizeButtonState();
    };

    const renderMetricsTable = (payload) => {
        const showRaw = Boolean(toggleRawMetrics && toggleRawMetrics.checked);
        const activeSelection = finalizeModelSelect ? finalizeModelSelect.value : payload.top_evaluated_model;
        trainingMetricsBody.replaceChildren(...payload.results.map((result) => {
            const row = document.createElement("tr");

            const selectCell = document.createElement("td");
            selectCell.style.textAlign = "center";
            const radio = document.createElement("input");
            radio.type = "radio";
            radio.name = "final-model-radio";
            radio.value = result.model_name;
            radio.checked = result.model_name === (activeSelection || payload.top_evaluated_model);
            radio.title = `Pilih ${result.model_name} sebagai kandidat model final`;
            radio.addEventListener("change", () => {
                if (radio.checked && finalizeModelSelect) {
                    finalizeModelSelect.value = result.model_name;
                }
            });
            selectCell.appendChild(radio);

            const modelCell = makeCell("th", result.model_name, "row");
            if (result.model_name === payload.top_evaluated_model) {
                modelCell.appendChild(document.createTextNode(" (F1 tertinggi)"));
            }
            const raw = result.raw_validation_metrics || {};
            const accText = showRaw && raw.accuracy !== undefined
                ? String(raw.accuracy)
                : `${(result.validation_accuracy * 100).toFixed(2)}%`;
            const precText = showRaw && raw.precision_macro !== undefined
                ? String(raw.precision_macro)
                : result.validation_precision_macro.toFixed(4);
            const recText = showRaw && raw.recall_macro !== undefined
                ? String(raw.recall_macro)
                : result.validation_recall_macro.toFixed(4);
            const f1Text = showRaw && raw.f1_macro !== undefined
                ? String(raw.f1_macro)
                : result.validation_f1_macro.toFixed(4);
            const timeText = showRaw && raw.training_time_seconds !== undefined
                ? String(raw.training_time_seconds)
                : result.training_time_seconds.toFixed(4);
            row.append(
                selectCell,
                modelCell,
                makeCell("td", accText),
                makeCell("td", precText),
                makeCell("td", recText),
                makeCell("td", f1Text),
                makeCell("td", timeText)
            );
            return row;
        }));
    };

    if (toggleRawMetrics) {
        toggleRawMetrics.addEventListener("change", () => {
            if (lastComparisonData) {
                renderMetricsTable(lastComparisonData);
            }
        });
    }

    if (finalizeModelSelect) {
        finalizeModelSelect.addEventListener("change", () => {
            const radios = trainingMetricsBody.querySelectorAll('input[name="final-model-radio"]');
            radios.forEach((radio) => {
                radio.checked = radio.value === finalizeModelSelect.value;
            });
        });
    }

    if (finalizeConfirmCheck) {
        finalizeConfirmCheck.addEventListener("change", syncFinalizeButtonState);
    }

    const renderTrainingResults = (data) => {
        const validationLabel = data.validation_method === "cross_validation"
            ? `validasi silang ${data.validation_folds}-fold`
            : "validasi";
        document.getElementById("training-rows-received").textContent = String(data.rows_received);
        document.getElementById("training-rows-used").textContent = String(data.rows_used);
        const trainingSplitLabel = document.getElementById("training-split-label");
        if (data.validation_method === "cross_validation") {
            trainingSplitLabel.textContent = "Baris latih / validasi silang / uji";
            document.getElementById("training-split").textContent =
                `${data.train_rows} / ${data.validation_folds}-fold CV / ${data.test_rows} baris ` +
                `(target latih/uji ${data.split_percentages.train}/${data.split_percentages.test}%; ` +
                `aktual ${data.actual_split_percentages.train}/${data.actual_split_percentages.test}%)`;
        } else {
            trainingSplitLabel.textContent = "Baris latih / validasi / uji";
            document.getElementById("training-split").textContent =
                `${data.train_rows} / ${data.validation_rows} / ${data.test_rows} baris ` +
                `(target ${data.split_percentages.train}/${data.split_percentages.validation}/${data.split_percentages.test}%; ` +
                `aktual ${data.actual_split_percentages.train}/${data.actual_split_percentages.validation}/${data.actual_split_percentages.test}%)`;
        }
        document.getElementById("training-invalid-labels").textContent = String(data.invalid_label_rows_excluded);
        document.getElementById("training-duplicates").textContent = String(data.duplicate_rows_removed);
        document.getElementById("training-missing-removed").textContent =
            String(data.missing_feature_rows_removed);
        document.getElementById("training-outliers-removed").textContent =
            String(data.final_training_outliers_removed);
        const preprocessingLabels = {
            numeric_imputation: {
                mean: "imputasi numerik: mean",
                median: "imputasi numerik: median",
                mode: "imputasi numerik: modus",
                zero: "imputasi numerik: 0",
                drop: "nilai kosong: hapus baris"
            },
            categorical_imputation: {
                mode: "imputasi kategori: modus",
                unknown: 'imputasi kategori: "Unknown"',
                drop: "nilai kosong: hapus baris"
            },
            outlier_handling: {
                none: "outlier: dibiarkan",
                iqr_cap: "outlier: IQR capping",
                drop: "outlier: dihapus dari data latih"
            },
            encoding: {
                label: "encoding: label",
                onehot: "encoding: one-hot",
                none: "tanpa encoding"
            },
            scaling: {
                none: "tanpa scaling",
                minmax: "scaling: Min-Max",
                standard: "scaling: StandardScaler"
            }
        };
        document.getElementById("training-preprocessing").textContent = [
            preprocessingLabels.numeric_imputation[data.preprocessing.numeric_imputation],
            preprocessingLabels.categorical_imputation[data.preprocessing.categorical_imputation],
            preprocessingLabels.outlier_handling[data.preprocessing.outlier_handling],
            preprocessingLabels.encoding[data.preprocessing.encoding],
            preprocessingLabels.scaling[data.preprocessing.scaling]
        ].join("; ");
        document.getElementById("training-top-model").textContent = data.top_evaluated_model;
        document.getElementById("training-feature-list").textContent = data.feature_columns.join(", ");
        document.getElementById("training-accuracy-heading").textContent = `Akurasi ${validationLabel}`;
        document.getElementById("training-f1-heading").textContent = `F1 Macro ${validationLabel}`;

        const classCounts = data.class_distribution;
        const largestClass = Math.max(...data.labels.map((label) => classCounts[label]), 1);
        trainingClassChart.replaceChildren(...data.labels.map((label) => {
            const row = document.createElement("div");
            row.className = "training-class-row";
            const labelCell = makeCell("span", label);
            const track = document.createElement("div");
            track.className = "training-class-track";
            const fill = document.createElement("div");
            fill.className = "training-class-fill";
            fill.style.width = `${(classCounts[label] / largestClass) * 100}%`;
            track.appendChild(fill);
            const countCell = makeCell("span", `${classCounts[label]} baris`);
            row.append(labelCell, track, countCell);
            return row;
        }));

        const buildConfusionMatrixTable = (labels, matrix) => {
            const table = document.createElement("table");
            table.className = "training-confusion-table";
            const head = document.createElement("thead");
            const headerRow = document.createElement("tr");
            headerRow.append(makeCell("th", "Aktual \\ Prediksi"));
            labels.forEach((label) => headerRow.appendChild(makeCell("th", label, "col")));
            head.appendChild(headerRow);
            const body = document.createElement("tbody");
            labels.forEach((label, rowIndex) => {
                const row = document.createElement("tr");
                row.appendChild(makeCell("th", label, "row"));
                (matrix[rowIndex] || []).forEach((count) => {
                    row.appendChild(makeCell("td", String(count)));
                });
                body.appendChild(row);
            });
            table.append(head, body);
            return table;
        };

        const buildPredictionSamplesTable = (samples) => {
            const wrapper = document.createElement("div");
            wrapper.className = "pma-table-container";
            const table = document.createElement("table");
            table.className = "pma-table";
            table.style.fontSize = "11px";
            const thead = document.createElement("thead");
            const headRow = document.createElement("tr");
            headRow.append(
                makeCell("th", "Baris #"),
                makeCell("th", "Label Aktual"),
                makeCell("th", "Prediksi Model"),
                makeCell("th", "Hasil")
            );
            thead.appendChild(headRow);
            const tbody = document.createElement("tbody");
            samples.forEach((item) => {
                const tr = document.createElement("tr");
                const statusCell = makeCell("td", item.correct ? "✅ Cocok" : "❌ Meleset");
                statusCell.style.color = item.correct ? "#274e13" : "#cc0000";
                statusCell.style.fontWeight = "600";
                tr.append(
                    makeCell("td", String(item.row_index)),
                    makeCell("td", item.actual),
                    makeCell("td", item.predicted),
                    statusCell
                );
                tbody.appendChild(tr);
            });
            table.append(thead, tbody);
            wrapper.appendChild(table);
            return wrapper;
        };

        lastComparisonData = data;
        renderMetricsTable(data);

        if (trainingLeakageAudit && data.leakage_check) {
            const excludedCols = data.leakage_check.excluded_leakage_columns || [];
            trainingLeakageAudit.hidden = false;
            trainingLeakageAudit.innerHTML = `
                <strong>🛡️ Audit Anti-Data-Leakage: LOLOS</strong><br>
                <span>${data.leakage_check.message}</span><br>
                <span style="font-size: 11px;">Kolom target &amp; turunan yang dikecualikan dari fitur: <code>${excludedCols.length ? excludedCols.join(", ") : "-"}</code></span>
            `;
        }

        if (trainingVerificationDetails) {
            trainingVerificationDetails.replaceChildren(...data.results.map((result, idx) => {
                const details = document.createElement("details");
                details.className = "training-verify-card";
                if (idx === 0) details.open = true;

                const summary = document.createElement("summary");
                summary.className = "training-verify-summary";
                const raw = result.raw_validation_metrics || {};
                const dist = result.prediction_distribution || {};
                const distText = data.labels.map((l) => `${l}: ${dist[l] ?? 0}`).join(" | ");
                summary.innerHTML = `
                    <span>${idx + 1}. ${result.model_name}${result.model_name === data.top_evaluated_model ? " ⭐" : ""}</span>
                    <span style="font-weight: normal; font-size: 11px; color: #555;">F1 Mentah: <code>${raw.f1_macro ?? result.validation_f1_macro}</code> &bull; Distribusi Prediksi: ${distText}</span>
                `;

                const body = document.createElement("div");
                body.className = "training-verify-body";

                const rawBox = document.createElement("div");
                rawBox.style.cssText = "background: #f9fbfd; border: 1px solid #d6e2ec; padding: 8px 10px; border-radius: 2px; margin-bottom: 10px; font-family: monospace; font-size: 11px;";
                rawBox.innerHTML = `
                    <strong>Nilai Metrik Mentah (Sebelum Pembulatan):</strong><br>
                    Accuracy: ${raw.accuracy ?? result.validation_accuracy} |
                    Precision Macro: ${raw.precision_macro ?? result.validation_precision_macro} |
                    Recall Macro: ${raw.recall_macro ?? result.validation_recall_macro} |
                    F1 Macro: ${raw.f1_macro ?? result.validation_f1_macro} |
                    Waktu: ${raw.training_time_seconds ?? result.training_time_seconds}s
                `;
                body.appendChild(rawBox);

                if (Array.isArray(result.fold_scores) && result.fold_scores.length) {
                    const foldTitle = document.createElement("div");
                    foldTitle.style.cssText = "font-weight: 600; color: #235a81; margin-bottom: 4px;";
                    foldTitle.textContent = `Skor Per Fold (${result.fold_scores.length}-Fold Cross-Validation, nilai mentah):`;
                    body.appendChild(foldTitle);

                    const foldWrap = document.createElement("div");
                    foldWrap.className = "pma-table-container";
                    foldWrap.style.marginBottom = "10px";
                    const foldTable = document.createElement("table");
                    foldTable.className = "pma-table";
                    foldTable.style.fontSize = "11px";
                    const fHead = document.createElement("thead");
                    const fHeadRow = document.createElement("tr");
                    fHeadRow.append(
                        makeCell("th", "Fold"),
                        makeCell("th", "Baris Latih / Val"),
                        makeCell("th", "Accuracy"),
                        makeCell("th", "Precision Macro"),
                        makeCell("th", "Recall Macro"),
                        makeCell("th", "F1 Macro")
                    );
                    fHead.appendChild(fHeadRow);
                    const fBody = document.createElement("tbody");
                    result.fold_scores.forEach((fold) => {
                        const tr = document.createElement("tr");
                        tr.append(
                            makeCell("td", `Fold ${fold.fold}`),
                            makeCell("td", `${fold.train_rows} / ${fold.validation_rows}`),
                            makeCell("td", String(fold.accuracy)),
                            makeCell("td", String(fold.precision_macro)),
                            makeCell("td", String(fold.recall_macro)),
                            makeCell("td", String(fold.f1_macro))
                        );
                        fBody.appendChild(tr);
                    });
                    foldTable.append(fHead, fBody);
                    foldWrap.appendChild(foldTable);
                    body.appendChild(foldWrap);
                }

                const grid = document.createElement("div");
                grid.className = "training-verify-grid";

                const cmCard = document.createElement("div");
                cmCard.className = "training-confusion-card";
                const cmTitle = document.createElement("h4");
                cmTitle.textContent = data.validation_method === "cross_validation"
                    ? "Confusion Matrix Out-of-Fold (80% Latih)"
                    : "Confusion Matrix Validasi";
                cmCard.append(cmTitle, buildConfusionMatrixTable(data.labels, result.validation_confusion_matrix || []));

                const sampleCard = document.createElement("div");
                const sampleTitle = document.createElement("div");
                sampleTitle.style.cssText = "font-weight: 600; color: #235a81; margin-bottom: 4px;";
                sampleTitle.textContent = "Sampel Prediksi vs Aktual (10 baris pertama):";
                sampleCard.append(sampleTitle, buildPredictionSamplesTable(result.sample_predictions || []));

                grid.append(cmCard, sampleCard);
                body.appendChild(grid);
                details.append(summary, body);
                return details;
            }));
        }

        const finalMetrics = data.final_test_metrics;
        const rawTest = finalMetrics.raw_metrics || {};
        document.getElementById("training-final-test-summary").textContent =
            `${data.final_test_model} — akurasi ${(finalMetrics.accuracy * 100).toFixed(2)}% ` +
            `(mentah: ${rawTest.accuracy ?? finalMetrics.accuracy}), ` +
            `precision macro ${finalMetrics.precision_macro.toFixed(4)}, recall macro ${finalMetrics.recall_macro.toFixed(4)}, ` +
            `F1 macro ${finalMetrics.f1_macro.toFixed(4)} (mentah: ${rawTest.f1_macro ?? finalMetrics.f1_macro}) pada ${data.test_rows} baris uji.`;

        const card = document.createElement("section");
        card.className = "training-confusion-card";
        const title = document.createElement("h4");
        title.textContent = data.final_test_model;
        card.append(title, buildConfusionMatrixTable(data.labels, finalMetrics.confusion_matrix));
        trainingConfusionMatrices.replaceChildren(card);

        if (trainingFinalTestSamples) {
            const sampleTitle = document.createElement("div");
            sampleTitle.style.cssText = "font-weight: 600; color: #235a81; margin-bottom: 4px; font-size: 12px;";
            sampleTitle.textContent = `Sampel Prediksi Data Uji (${data.final_test_model}, maksimal 10 baris):`;
            trainingFinalTestSamples.replaceChildren(
                sampleTitle,
                buildPredictionSamplesTable(finalMetrics.sample_predictions || [])
            );
        }

        if (finalizeModelSelect) {
            finalizeModelSelect.replaceChildren(...data.results.map((result) => {
                const opt = document.createElement("option");
                opt.value = result.model_name;
                opt.textContent = `${result.model_name} (F1: ${result.validation_f1_macro.toFixed(4)})`;
                if (result.model_name === data.top_evaluated_model) {
                    opt.selected = true;
                }
                return opt;
            }));
            const radios = trainingMetricsBody.querySelectorAll('input[name="final-model-radio"]');
            radios.forEach((radio) => {
                radio.checked = radio.value === finalizeModelSelect.value;
            });
        }
        if (finalizeConfirmCheck) {
            finalizeConfirmCheck.checked = false;
        }
        if (finalizeStatus) {
            finalizeStatus.hidden = true;
            finalizeStatus.textContent = "";
            delete finalizeStatus.dataset.state;
        }
        syncFinalizeButtonState();

        trainingResults.hidden = false;
        trainingStatus.textContent =
            `Evaluasi selesai. Preprocessing dari panel diterapkan; kandidat dipilih berdasarkan ${validationLabel}. ` +
            "Data uji dipakai sekali untuk evaluasi akhir dan tidak ikut mempelajari preprocessing.";
        trainingStatus.dataset.state = "success";
    };

    const renderFinalModelStatus = (statusData) => {
        if (!finalModelStatusBody || !finalModelBadge) return;
        if (!statusData || !statusData.is_saved || !statusData.metadata) {
            finalModelBadge.textContent = "Belum Disimpan";
            finalModelBadge.className = "pma-badge pma-badge-warning";
            finalModelStatusBody.innerHTML = `
                <span>Belum ada pipeline model final yang tersimpan di server. Jalankan perbandingan model di bawah lalu klik <strong>Tetapkan Model Final</strong>.</span>
            `;
            return;
        }

        const meta = statusData.metadata;
        const ds = meta.dataset_info || {};
        const evalRes = meta.evaluation_results || {};
        const testMetrics = evalRes.final_test_metrics || {};
        const prep = meta.preprocessing || {};

        finalModelBadge.textContent = `Model Final: ${meta.model_name}`;
        finalModelBadge.className = "pma-badge pma-badge-success";
        finalModelStatusBody.innerHTML = `
            <dl class="dataset-summary-grid" style="margin-bottom: 8px;">
                <div class="dataset-summary-item"><dt>Nama Model Final</dt><dd><strong>${meta.model_name}</strong></dd></div>
                <div class="dataset-summary-item"><dt>Tanggal Disimpan</dt><dd>${meta.saved_at || "-"}</dd></div>
                <div class="dataset-summary-item"><dt>Dataset &amp; Versi</dt><dd>${ds.dataset_name || "-"} (<code>${ds.dataset_version || "-"}</code>, ${ds.rows_used ?? "-"} baris)</dd></div>
                <div class="dataset-summary-item"><dt>Hasil Uji Akhir (20% Test)</dt><dd>Akurasi ${((testMetrics.accuracy || 0) * 100).toFixed(2)}% &bull; F1 Macro ${(testMetrics.f1_macro ?? 0).toFixed(4)}</dd></div>
                <div class="dataset-summary-item"><dt>Preprocessing Pipeline</dt><dd>num: ${prep.numeric_imputation}, cat: ${prep.categorical_imputation}, outlier: ${prep.outlier_handling}, enc: ${prep.encoding}, scale: ${prep.scaling}</dd></div>
                <div class="dataset-summary-item"><dt>Fitur Aktif (${(meta.feature_columns || []).length})</dt><dd style="word-break: break-word;">${(meta.feature_columns || []).join(", ")}</dd></div>
            </dl>
            <div style="font-size: 11px; color: #274e13;">
                📁 Artifact Pipeline: <code>${statusData.pipeline_path}</code> &bull; Metadata: <code>${statusData.metadata_path}</code>
            </div>
        `;
    };

    const fetchFinalModelStatus = async () => {
        try {
            const resp = await fetch("/dataset-management/final-model");
            const payload = await resp.json();
            if (resp.ok && payload.status === "success") {
                renderFinalModelStatus(payload.data);
            }
        } catch (err) {
            if (finalModelBadge) finalModelBadge.textContent = "Gagal Memuat";
        }
    };

    const saveFinalModelPipeline = async () => {
        if (!lastTrainingRequestPayload || !lastComparisonData || lastComparedSignature !== getCurrentConfigSignature()) {
            alert("Hasil perbandingan tidak berlaku atau belum dijalankan. Jalankan ulang perbandingan model terlebih dahulu.");
            invalidateComparisonIfConfigChanged("Dataset atau pengaturan");
            return;
        }
        if (finalizeConfirmCheck && !finalizeConfirmCheck.checked) {
            alert("Silakan centang kotak konfirmasi verifikasi terlebih dahulu.");
            return;
        }

        const selectedModelName = finalizeModelSelect ? finalizeModelSelect.value : lastComparisonData.top_evaluated_model;
        const confirmed = confirm(
            `Konfirmasi Tetapkan Model Final:\n\n` +
            `• Model: ${selectedModelName}\n` +
            `• Dataset: ${currentDataset?.filename || "dataset.csv"}\n` +
            `• Fitur: ${(lastTrainingRequestPayload.feature_columns || []).length} kolom\n\n` +
            `Apakah Anda yakin ingin menetapkan dan menyimpan pipeline ini sebagai Model Final?`
        );
        if (!confirmed) return;

        const selectedCandidateResult = (lastComparisonData.results || []).find(
            (item) => item.model_name === selectedModelName
        );

        btnSaveFinalModel.disabled = true;
        btnSaveFinalModel.textContent = "⏳ Menetapkan & Menyimpan...";
        if (finalizeStatus) {
            finalizeStatus.hidden = false;
            finalizeStatus.textContent = `Melatih ulang pipeline '${selectedModelName}' dan menetapkan sebagai Model Final...`;
            finalizeStatus.dataset.state = "loading";
        }

        try {
            const resp = await fetch("/dataset-management/finalize", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    ...lastTrainingRequestPayload,
                    dataset_name: currentDataset?.filename || "dataset.csv",
                    selected_model_name: selectedModelName,
                    validation_summary: selectedCandidateResult
                        ? {
                              validation_method: lastComparisonData.validation_method,
                              validation_folds: lastComparisonData.validation_folds,
                              raw_validation_metrics: selectedCandidateResult.raw_validation_metrics,
                              fold_scores: selectedCandidateResult.fold_scores || [],
                          }
                        : null,
                }),
            });
            const result = await resp.json();
            if (!resp.ok || result.status !== "success") {
                throw new Error(result.message || `Gagal menetapkan model final (HTTP ${resp.status}).`);
            }
            lastFinalizedSignature = lastComparedSignature;
            if (finalModelReconfirmNotice) {
                finalModelReconfirmNotice.hidden = true;
            }
            renderFinalModelStatus(result.data);
            if (finalizeStatus) {
                finalizeStatus.hidden = false;
                finalizeStatus.textContent = `✅ Model Final '${selectedModelName}' (${result.data.metadata.dataset_info.dataset_version}) berhasil ditetapkan & disimpan!`;
                finalizeStatus.dataset.state = "success";
            }
        } catch (err) {
            if (finalizeStatus) {
                finalizeStatus.hidden = false;
                finalizeStatus.textContent = `❌ ${err instanceof Error ? err.message : "Gagal menetapkan model final."}`;
                finalizeStatus.dataset.state = "error";
            }
        } finally {
            btnSaveFinalModel.textContent = "✅ Tetapkan Model Final";
            syncFinalizeButtonState();
        }
    };

    const trainAndCompareModels = async () => {
        if (!currentDataset) return;
        sectionTraining.hidden = false;
        sectionTraining.scrollIntoView({ behavior: "smooth", block: "start" });
        trainingResults.hidden = true;

        if (currentDataset.targetColumnIndex === -1) {
            trainingStatus.textContent = "Kolom Burnout_Risk atau Burnout_Level tidak ditemukan.";
            trainingStatus.dataset.state = "error";
            return;
        }

        const featureColumns = Array.from(prepColumnsGrid.querySelectorAll(".prep-col-check:checked"))
            .map((checkbox) => {
                const index = Number(checkbox.dataset.colIdx);
                return { header: currentDataset.headers[index], index };
            })
            .filter(({ header, index }) => !isTargetColumn(
                header, index, currentDataset.targetColumnIndex
            ))
            .map(({ header }) => header);
        if (!featureColumns.length) {
            trainingStatus.textContent = "Pilih minimal satu fitur sebelum menjalankan pelatihan.";
            trainingStatus.dataset.state = "error";
            return;
        }
        const splitPercentages = getTrainingSplitPercentages();
        if (!splitPercentages) {
            trainingStatus.textContent = trainingValidationMethod === "cross_validation"
                ? "Pembagian tidak valid: data latih minimal 50%, data uji minimal 5%, dan total latih + uji harus tepat 100%."
                : "Persentase tidak valid: data latih minimal 50%, validasi dan uji minimal 5%, serta total harus tepat 100%.";
            trainingStatus.dataset.state = "error";
            return;
        }
        const trainingColumnIndices = featureColumns.map((column) =>
            currentDataset.headers.indexOf(column)
        );
        trainingColumnIndices.push(currentDataset.targetColumnIndex);
        const trainingHeaders = trainingColumnIndices.map((index) => currentDataset.headers[index]);
        const trainingRows = currentDataset.dataRows.map((row) =>
            trainingColumnIndices.map((index) => row[index])
        );

        const selectedSampleSize = getSelectedSampleSize();
        if (prepOptSampling && prepOptSampling.value === "custom" && selectedSampleSize === null) {
            trainingStatus.textContent = "Jumlah baris sampling kustom harus berupa bilangan bulat minimal 15.";
            trainingStatus.dataset.state = "error";
            return;
        }

        const requestPayload = {
            headers: trainingHeaders,
            rows: trainingRows,
            feature_columns: featureColumns,
            deduplicate: prepOptDedup.checked,
            sample_size: selectedSampleSize,
            train_percent: splitPercentages.train,
            validation_percent: splitPercentages.validation,
            test_percent: splitPercentages.test,
            validation_method: trainingValidationMethod,
            preprocessing: {
                numeric_imputation: prepOptImputeNum.value,
                categorical_imputation: prepOptImputeCat.value,
                outlier_handling: prepOptOutlier.value,
                encoding: prepOptEncoding.value,
                scaling: prepOptScaling.value
            }
        };
        lastTrainingRequestPayload = requestPayload;
        const requestSignature = getCurrentConfigSignature();

        btnRunTraining.disabled = true;
        btnRunTraining.textContent = "⏳ Melatih dan membandingkan...";
        trainingStatus.textContent = trainingValidationMethod === "cross_validation"
            ? `Membagi data latih/uji ${splitPercentages.train}/${splitPercentages.test} dan mengevaluasi lima kandidat dengan validasi silang.`
            : `Membagi data ${splitPercentages.train}/${splitPercentages.validation}/${splitPercentages.test} (latih/validasi/uji) dan mengevaluasi lima kandidat.`;
        trainingStatus.dataset.state = "loading";

        try {
            const response = await fetch("/dataset-management/train", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(requestPayload)
            });
            const result = await response.json();
            if (!response.ok || result.status !== "success") {
                throw new Error(result.message || `Pelatihan gagal (HTTP ${response.status}).`);
            }
            lastComparedSignature = requestSignature;
            renderTrainingResults(result.data);
        } catch (error) {
            trainingStatus.textContent = error instanceof Error
                ? `Gagal melatih model: ${error.message}`
                : "Gagal melatih model karena terjadi kesalahan.";
            trainingStatus.dataset.state = "error";
        } finally {
            btnRunTraining.textContent = "▶ Terapkan Pembagian & Bandingkan Model";
            btnRunTraining.disabled = getTrainingSplitPercentages() === null;
        }
    };

    if (btnSaveFinalModel) {
        btnSaveFinalModel.addEventListener("click", saveFinalModelPipeline);
    }
    fetchFinalModelStatus();

    if (btnOpenTraining) {
        btnOpenTraining.addEventListener("click", () => {
            sectionTraining.hidden = false;
            sectionTraining.scrollIntoView({ behavior: "smooth", block: "start" });
            if (trainingResults.hidden) {
                trainingStatus.textContent = currentDataset
                    ? "Pengaturan default 80/20 + Cross-Validation 5-Fold sudah aktif. Klik tombol perbandingan untuk memulai, atau pilih template lain."
                    : "Muat dataset terlebih dahulu untuk menjalankan perbandingan model (default: 80/20 + Cross-Validation 5-Fold).";
                delete trainingStatus.dataset.state;
            }
        });
    }
    if (btnRunTraining) {
        btnRunTraining.addEventListener("click", trainAndCompareModels);
    }
    trainingPresets.forEach((preset) => {
        preset.addEventListener("click", () => {
            trainingValidationMethod = preset.dataset.strategy || "holdout";
            trainingTrainPercent.value = preset.dataset.train;
            trainingValidationPercent.value = preset.dataset.validation;
            trainingTestPercent.value = preset.dataset.test;
            trainingPresets.forEach((option) => {
                option.setAttribute("aria-pressed", String(option === preset));
            });
            updateTrainingSplitTotal();
            invalidateComparisonIfConfigChanged("Pembagian data");
        });
    });
    [trainingTrainPercent, trainingValidationPercent, trainingTestPercent].forEach((input) => {
        input.addEventListener("input", () => {
            if (input === trainingValidationPercent) {
                trainingValidationMethod = "holdout";
            }
            trainingPresets.forEach((preset) => preset.setAttribute("aria-pressed", "false"));
            updateTrainingSplitTotal();
            invalidateComparisonIfConfigChanged("Pembagian data");
        });
    });
    updateTrainingSplitTotal();

    [
        prepOptDedup,
        prepOptImputeNum,
        prepOptImputeCat,
        prepOptOutlier,
        prepOptEncoding,
        prepOptScaling
    ].forEach((control) => {
        if (control) {
            control.addEventListener("change", () => {
                invalidateComparisonIfConfigChanged("Pengaturan preprocessing");
            });
        }
    });

    if (prepOptSampling) {
        prepOptSampling.addEventListener("change", () => {
            updateSamplingBadge();
            invalidateComparisonIfConfigChanged("Sampling data");
        });
    }
    if (prepOptSamplingCustom) {
        prepOptSamplingCustom.addEventListener("input", () => {
            updateSamplingBadge();
            invalidateComparisonIfConfigChanged("Sampling data");
        });
    }

    // Render Preview Mapping Encoding
    const renderEncodingPreview = () => {
        if (!currentDataset) return;
        const { headers, dataRows, columnTypes } = currentDataset;
        const mode = prepOptEncoding.value;

        if (mode === "none") {
            prepEncodingPreview.innerHTML = `<em>Teks fitur kategorikal akan dibiarkan dalam bentuk aslinya.</em>`;
            return;
        }

        if (mode === "onehot") {
            prepEncodingPreview.innerHTML = `<em>Setiap nilai kategori akan dimekarkan menjadi kolom biner baru (contoh: <code>Remote_Work_Hybrid</code>, <code>Remote_Work_Yes</code> bertipe 0 atau 1).</em>`;
            return;
        }

        // Label encoding preview
        const catCols = [];
        headers.forEach((h, idx) => {
            if ((columnTypes[idx] === "Teks" || /risk|level|status/i.test(h)) && !isDefaultDroppedColumn(h)) {
                catCols.push({ name: h, idx });
            }
        });

        if (!catCols.length) {
            prepEncodingPreview.innerHTML = `<em>Fitur kategorikal terpilih siap di-encode.</em>`;
            return;
        }

        let previewHtml = `<div style="font-weight: bold; margin-bottom: 4px; color: #235a81;">Rencana Label Encoding Fitur Terpilih:</div><ul style="padding-left: 18px; margin: 0;">`;
        catCols.slice(0, 4).forEach(col => {
            const uniques = Array.from(new Set(dataRows.map(r => (r[col.idx] ?? "").trim()).filter(Boolean))).slice(0, 4);
            const mapping = uniques.map((u, i) => `<code>${u}</code>=${i}`).join(", ");
            previewHtml += `<li><strong>${col.name}:</strong> ${mapping} ${uniques.length < 4 ? '' : '...'}</li>`;
        });
        previewHtml += `</ul>`;
        prepEncodingPreview.innerHTML = previewHtml;
    };

    // Tombol Pilih Semua / Hilangkan Semua / Rekomendasi
    if (btnColSelectAll) {
        btnColSelectAll.addEventListener("click", () => {
            prepColumnsGrid.querySelectorAll(".prep-col-check").forEach(cb => {
                if (!cb.disabled) cb.checked = true;
            });
            updateSelectedColsCount();
            invalidateComparisonIfConfigChanged("Seleksi kolom fitur");
        });
    }

    if (btnColDeselectAll) {
        btnColDeselectAll.addEventListener("click", () => {
            prepColumnsGrid.querySelectorAll(".prep-col-check").forEach(cb => cb.checked = false);
            updateSelectedColsCount();
            invalidateComparisonIfConfigChanged("Seleksi kolom fitur");
        });
    }

    if (btnColRecommend) {
        btnColRecommend.addEventListener("click", () => {
            if (!currentDataset) return;
            const { headers } = currentDataset;
            prepColumnsGrid.querySelectorAll(".prep-col-check").forEach((cb, idx) => {
                const h = headers[idx];
                cb.checked = !isTargetColumn(h, idx, currentDataset.targetColumnIndex)
                    && !isDefaultDroppedColumn(h);
            });
            updateSelectedColsCount();
            invalidateComparisonIfConfigChanged("Seleksi kolom fitur");
        });
    }

    if (prepColumnsGrid) {
        prepColumnsGrid.addEventListener("change", (e) => {
            if (e.target.classList.contains("prep-col-check")) {
                updateSelectedColsCount();
                invalidateComparisonIfConfigChanged("Seleksi kolom fitur");
            }
        });
    }

    // Reset ke Settingan Default ML
    if (btnPrepResetDefault) {
        btnPrepResetDefault.addEventListener("click", () => {
            prepOptDedup.checked = true;
            prepOptImputeNum.value = "mean";
            prepOptImputeCat.value = "mode";
            prepOptOutlier.value = "iqr_cap";
            prepOptEncoding.value = "label";
            prepOptScaling.value = "none";
            if (prepOptSampling) prepOptSampling.value = "all";
            if (prepOptSamplingCustom) prepOptSamplingCustom.value = "";
            if (btnColRecommend) btnColRecommend.click();
            renderEncodingPreview();
            updateSamplingBadge();
            invalidateComparisonIfConfigChanged("Reset pengaturan preprocessing");
            setStatus("Pengaturan pra-pemrosesan telah direset ke rekomendasi default ML (Mean Imputation & Feature Selection).", "success");
        });
    }

    if (prepOptEncoding) {
        prepOptEncoding.addEventListener("change", renderEncodingPreview);
    }

    // Buka Tampilan Preprocessing
    if (btnPrep) {
        btnPrep.addEventListener("click", () => {
            sectionPrep.hidden = false;
            sectionPrep.scrollIntoView({ behavior: "smooth", block: "start" });
        });
    }
    if (btnGoTraining) {
        btnGoTraining.addEventListener("click", () => {
            sectionTraining.hidden = false;
            sectionTraining.scrollIntoView({ behavior: "smooth", block: "start" });
            if (trainingResults.hidden) {
                trainingStatus.textContent =
                    "Pilih pembagian data, lalu tekan “Terapkan Pengaturan & Bandingkan Model”. " +
                    "Pengaturan preprocessing yang dipilih akan ikut digunakan.";
                delete trainingStatus.dataset.state;
            } else {
                trainingStatus.textContent =
                    "Pengaturan preprocessing terbaru akan digunakan saat Anda menjalankan perbandingan kembali.";
                trainingStatus.dataset.state = "loading";
            }
        });
    }

    // =========================================================================
    // EKSEKUSI PIPELINE & DOWNLOAD CSV BERSIH
    // =========================================================================
    const executePreprocessingAndDownload = () => {
        if (!currentDataset) return;
        const { headers, dataRows, columnTypes, duplicateRows, targetColumnIndex } = currentDataset;

        // 1. Seleksi Kolom
        const selectedCheckboxes = Array.from(prepColumnsGrid.querySelectorAll(".prep-col-check:checked"))
            .filter((checkbox) => {
                const index = Number(checkbox.dataset.colIdx);
                return !isTargetColumn(headers[index], index, targetColumnIndex);
            });
        if (!selectedCheckboxes.length) {
            alert("Harap pilih minimal 1 kolom untuk diikutsertakan dalam dataset.");
            return;
        }

        const selectedColIndices = selectedCheckboxes.map(cb => parseInt(cb.dataset.colIdx, 10));
        const selectedHeaders = selectedColIndices.map(idx => headers[idx]);

        // 2. Baris Duplikat & Sampling Opsional
        let filteredSourceIndices = dataRows
            .map((_, index) => index)
            .filter((index) => !prepOptDedup.checked || !duplicateRows.has(index));
        const requestedSampleSize = getSelectedSampleSize();
        if (requestedSampleSize !== null && requestedSampleSize < filteredSourceIndices.length) {
            const step = filteredSourceIndices.length / requestedSampleSize;
            const sampledIndices = [];
            for (let i = 0; i < requestedSampleSize; i += 1) {
                sampledIndices.push(filteredSourceIndices[Math.floor(i * step)]);
            }
            filteredSourceIndices = sampledIndices;
        }
        const filteredRows = filteredSourceIndices.map((index) => dataRows[index]);

        // 3. Imputasi Nilai Kosong
        const imputeNumMode = prepOptImputeNum.value;
        const imputeCatMode = prepOptImputeCat.value;

        // Hitung statistik untuk imputasi
        const colMedians = {};
        const colMeans = {};
        const colModes = {};

        selectedColIndices.forEach(colIdx => {
            const colType = columnTypes[colIdx];
            const vals = filteredRows.map(r => r[colIdx]).filter(v => (v ?? "").trim() !== "");

            if (colType === "Numerik" || colType === "Integer") {
                const nums = vals.map(v => parseFloat(v)).filter(v => !isNaN(v)).sort((a,b)=>a-b);
                if (nums.length) {
                    const mid = Math.floor(nums.length / 2);
                    colMedians[colIdx] = nums.length % 2 !== 0 ? nums[mid] : ((nums[mid-1]+nums[mid])/2);
                    colMeans[colIdx] = (nums.reduce((a,b)=>a+b,0) / nums.length).toFixed(2);

                    // Hitung modus untuk numerik
                    const numFreq = {};
                    let maxNumCount = 0;
                    let numModeVal = nums[0];
                    nums.forEach(n => {
                        numFreq[n] = (numFreq[n] || 0) + 1;
                        if (numFreq[n] > maxNumCount) {
                            maxNumCount = numFreq[n];
                            numModeVal = n;
                        }
                    });
                    colModes[colIdx] = numModeVal;
                } else {
                    colMedians[colIdx] = 0;
                    colMeans[colIdx] = 0;
                    colModes[colIdx] = 0;
                }
            } else {
                // Mode
                const freq = {};
                let maxCount = 0;
                let modeVal = "Unknown";
                vals.forEach(v => {
                    freq[v] = (freq[v] || 0) + 1;
                    if (freq[v] > maxCount) {
                        maxCount = freq[v];
                        modeVal = v;
                    }
                });
                colModes[colIdx] = modeVal;
            }
        });

        // Filter / Imputasi
        let processedRows = [];
        let processedSourceIndices = [];
        let imputedValuesCount = 0;

        for (const [filteredRowIndex, row] of filteredRows.entries()) {
            let dropThisRow = false;
            const newRow = [];

            for (const colIdx of selectedColIndices) {
                let cellVal = (row[colIdx] ?? "").trim();
                const colType = columnTypes[colIdx];
                const isNum = colType === "Numerik" || colType === "Integer";

                if (cellVal === "") {
                    imputedValuesCount += 1;
                    if (isNum) {
                        if (imputeNumMode === "drop") { dropThisRow = true; break; }
                        else if (imputeNumMode === "mean") cellVal = String(colMeans[colIdx]);
                        else if (imputeNumMode === "median") cellVal = String(colMedians[colIdx]);
                        else if (imputeNumMode === "mode") cellVal = String(colModes[colIdx]);
                        else if (imputeNumMode === "zero") cellVal = "0";
                    } else {
                        if (imputeCatMode === "drop") { dropThisRow = true; break; }
                        else if (imputeCatMode === "mode") cellVal = String(colModes[colIdx]);
                        else cellVal = "Unknown";
                    }
                }
                newRow.push(cellVal);
            }

            if (!dropThisRow) {
                processedRows.push(newRow);
                processedSourceIndices.push(filteredSourceIndices[filteredRowIndex]);
            }
        }

        // 4. Penanganan Outlier
        const outlierMode = prepOptOutlier.value;
        if (outlierMode !== "none") {
            const newProcessed = [];
            const newSourceIndices = [];
            processedRows.forEach((row, rowIndex) => {
                let hasOutlier = false;
                const modifiedRow = [...row];

                selectedColIndices.forEach((origColIdx, newColIdx) => {
                    const bounds = detectedOutliersInfo.columnBounds[origColIdx];
                    if (bounds) {
                        const numVal = parseFloat(modifiedRow[newColIdx]);
                        if (!isNaN(numVal)) {
                            if (numVal < bounds.lower || numVal > bounds.upper) {
                                hasOutlier = true;
                                if (outlierMode === "iqr_cap") {
                                    modifiedRow[newColIdx] = String(numVal < bounds.lower ? bounds.lower : bounds.upper);
                                }
                            }
                        }
                    }
                });

                if (outlierMode === "drop" && hasOutlier) {
                    // skip baris ini
                } else {
                    newProcessed.push(modifiedRow);
                    newSourceIndices.push(processedSourceIndices[rowIndex]);
                }
            });
            processedRows = newProcessed;
            processedSourceIndices = newSourceIndices;
        }

        // 5. Penskalaan / Feature Scaling
        const scalingMode = prepOptScaling.value;
        if (scalingMode !== "none") {
            selectedColIndices.forEach((origColIdx, newColIdx) => {
                const colType = columnTypes[origColIdx];
                if (colType === "Numerik" || colType === "Integer") {
                    const nums = processedRows.map(r => parseFloat(r[newColIdx])).filter(v => !isNaN(v));
                    if (nums.length) {
                        const min = Math.min(...nums);
                        const max = Math.max(...nums);
                        const mean = nums.reduce((a,b)=>a+b,0) / nums.length;
                        const variance = nums.reduce((a,b)=>a + Math.pow(b - mean, 2), 0) / nums.length;
                        const std = Math.sqrt(variance) || 1;

                        processedRows.forEach(r => {
                            const v = parseFloat(r[newColIdx]);
                            if (!isNaN(v)) {
                                if (scalingMode === "minmax") {
                                    r[newColIdx] = max === min ? "0.0" : ((v - min) / (max - min)).toFixed(4);
                                } else if (scalingMode === "standard") {
                                    r[newColIdx] = ((v - mean) / std).toFixed(4);
                                }
                            }
                        });
                    }
                }
            });
        }

        // 6. Encoding Kategorikal
        const encodingMode = prepOptEncoding.value;
        let finalHeaders = [...selectedHeaders];
        let finalRows = processedRows;

        if (encodingMode === "label") {
            selectedColIndices.forEach((origColIdx, newColIdx) => {
                const colType = columnTypes[origColIdx];
                const headerName = headers[origColIdx];

                if (colType === "Teks" || /risk|level/i.test(headerName)) {
                    // Cek order khusus jika Burnout Risk / Stress Level
                    const uniqueVals = Array.from(new Set(finalRows.map(r => r[newColIdx])));
                    const valMap = {};

                    if (/burnout[_\s]?(risk|level)/i.test(headerName) || /stress[_\s]?level/i.test(headerName)) {
                        uniqueVals.forEach(v => {
                            const low = v.toLowerCase();
                            if (low.includes("high") || low.includes("tinggi")) valMap[v] = 2;
                            else if (low.includes("low") || low.includes("rendah")) valMap[v] = 0;
                            else valMap[v] = 1;
                        });
                    } else if (/gender/i.test(headerName)) {
                        uniqueVals.forEach(v => {
                            valMap[v] = v.toLowerCase().startsWith("m") ? 1 : 0;
                        });
                    } else {
                        uniqueVals.sort().forEach((v, idx) => {
                            valMap[v] = idx;
                        });
                    }

                    finalRows.forEach(r => {
                        r[newColIdx] = valMap[r[newColIdx]] !== undefined ? String(valMap[r[newColIdx]]) : "0";
                    });
                }
            });
        } else if (encodingMode === "onehot") {
            // One hot encoding
            const expandedHeaders = [];
            const colTransformers = [];

            selectedColIndices.forEach((origColIdx, newColIdx) => {
                const colType = columnTypes[origColIdx];
                const headerName = headers[origColIdx];

                if (colType === "Teks") {
                    const uniqueVals = Array.from(new Set(finalRows.map(r => r[newColIdx]))).sort();
                    uniqueVals.forEach(uv => {
                        expandedHeaders.push(`${headerName}_${uv.replace(/[^a-zA-Z0-9]/g, '_')}`);
                    });
                    colTransformers.push({ isOneHot: true, uniqueVals, origIdx: newColIdx });
                } else {
                    expandedHeaders.push(headerName);
                    colTransformers.push({ isOneHot: false, origIdx: newColIdx });
                }
            });

            const oneHotRows = finalRows.map(row => {
                const newRow = [];
                colTransformers.forEach(tf => {
                    if (tf.isOneHot) {
                        const cellVal = row[tf.origIdx];
                        tf.uniqueVals.forEach(uv => {
                            newRow.push(cellVal === uv ? "1" : "0");
                        });
                    } else {
                        newRow.push(row[tf.origIdx]);
                    }
                });
                return newRow;
            });

            finalHeaders = expandedHeaders;
            finalRows = oneHotRows;
        }

        let validOutputLabels = 0;
        let invalidOutputLabels = 0;
        if (targetColumnIndex !== -1) {
            finalHeaders.push("Burnout_Risk");
            finalRows = finalRows.map((row, index) => {
                const rawLabel = dataRows[processedSourceIndices[index]][targetColumnIndex].trim();
                const normalizedLabel = normalizeBurnoutLabel(rawLabel);
                if (normalizedLabel) validOutputLabels += 1;
                else invalidOutputLabels += 1;
                return [...row, normalizedLabel || rawLabel];
            });
        }

        // 7. Generate & Download CSV
        const escapeCsv = (str) => {
            const s = String(str ?? "");
            if (s.includes(",") || s.includes('"') || s.includes("\n")) {
                return `"${s.replace(/"/g, '""')}"`;
            }
            return s;
        };

        const csvContent = [
            finalHeaders.map(escapeCsv).join(","),
            ...finalRows.map(r => r.map(escapeCsv).join(","))
        ].join("\n");

        const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", `cleaned_preprocessed_${currentDataset.filename || "dataset.csv"}`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        // Update status info
        prepSummaryStatus.innerHTML = `
            <span style="color: #274e13; font-weight: bold;">
                ✅ Ekspor sukses! ${finalRows.length} baris & ${finalHeaders.length} kolom berhasil diproses dan diunduh.
            </span>
            ${targetColumnIndex === -1
                ? '<div style="color: #8a5a00; margin-top: 4px;">Kolom target Burnout_Risk tidak ditemukan; file belum memiliki label untuk pelatihan klasifikasi.</div>'
                : `<div style="color: #555; margin-top: 4px;">Label valid: ${validOutputLabels}; label kosong/tidak valid: ${invalidOutputLabels}. Label tetap terpisah dari fitur dan tidak diimputasi atau diskalakan. Baris berlabel tidak valid harus dikecualikan saat pelatihan.</div>`}
        `;
    };

    // Event listeners
    if (btnDownloadCleaned) {
        btnDownloadCleaned.addEventListener("click", executePreprocessingAndDownload);
    }

    if (btnEda) {
        btnEda.addEventListener("click", runEda);
    }

    // Tombol Muat dari Database lokal antiburnout_db
    if (btnLoadDb) {
        btnLoadDb.addEventListener("click", async () => {
            setStatus("Mengambil data responden dari database antiburnout_db...", "loading");
            if (btnSaveDb) btnSaveDb.style.display = "none";
            if (btnViewDataset) btnViewDataset.style.display = "inline-block";
            if (dbSaveFeedback) {
                dbSaveFeedback.textContent = "Data saat ini dimuat langsung dari tabel database.";
                dbSaveFeedback.style.color = "#235a81";
            }
            try {
                const resp = await fetch("/assessment/export/csv");
                if (!resp.ok) throw new Error(`Gagal mengambil data dari server (HTTP ${resp.status})`);
                const csvText = await resp.text();
                const rows = parseCsv(csvText);
                renderDataset("antiburnout_db_assessments.csv", rows);
            } catch (err) {
                setStatus("Gagal memuat dari database: " + err.message, "error");
            }
        });
    }

    // Fungsi upload dan simpan file CSV ke database
    const handleUploadToDatabase = async () => {
        const file = fileInput.files?.[0];
        if (!file) {
            alert("Silakan pilih file CSV terlebih dahulu.");
            return;
        }

        const confirmSave = confirm(`Apakah Anda yakin ingin memasukkan seluruh baris data dari "${file.name}" ke database?`);
        if (!confirmSave) return;

        const setButtonsLoading = (loading) => {
            if (btnSaveDb) {
                btnSaveDb.disabled = loading;
                btnSaveDb.textContent = loading ? "⏳ Menyimpan..." : "💾 Simpan ke Database";
            }
            if (btnSaveDbSummary) {
                btnSaveDbSummary.disabled = loading;
                btnSaveDbSummary.textContent = loading ? "⏳ Memproses Ingestion..." : "💾 Masukkan Seluruh Data CSV ke Database";
            }
        };

        setButtonsLoading(true);
        if (dbSaveFeedback) {
            dbSaveFeedback.textContent = "Sedang mengunggah dan menyimpan data ke database...";
            dbSaveFeedback.style.color = "#235a81";
        }
        setStatus("Mengunggah file CSV dan menyimpan ke database...", "loading");

        const formData = new FormData();
        formData.append("file", file);

        try {
            const resp = await fetch("/dataset-management/upload", {
                method: "POST",
                body: formData
            });

            const data = await resp.json();

            if (!resp.ok || data.status !== "success") {
                throw new Error(data.message || `Gagal menyimpan data (HTTP ${resp.status})`);
            }

            setStatus(`✅ ${data.message}`, "success");
            if (dbSaveFeedback) {
                dbSaveFeedback.textContent = `✅ ${data.message}`;
                dbSaveFeedback.style.color = "#2e7d32";
            }
            if (btnViewDataset) {
                btnViewDataset.style.display = "inline-block";
            }
            alert(`Sukses!\n${data.message}`);
        } catch (err) {
            setStatus(`❌ Gagal menyimpan ke database: ${err.message}`, "error");
            if (dbSaveFeedback) {
                dbSaveFeedback.textContent = `❌ ${err.message}`;
                dbSaveFeedback.style.color = "#c62828";
            }
            alert(`Terjadi Kesalahan:\n${err.message}`);
        } finally {
            setButtonsLoading(false);
        }
    };

    if (btnSaveDb) {
        btnSaveDb.addEventListener("click", handleUploadToDatabase);
    }
    if (btnSaveDbSummary) {
        btnSaveDbSummary.addEventListener("click", handleUploadToDatabase);
    }

    // Input File CSV dari laptop
    fileInput.addEventListener("change", async () => {
        const file = fileInput.files?.[0];
        results.hidden = true;
        if (btnSaveDb) btnSaveDb.style.display = "none";
        if (btnViewDataset) btnViewDataset.style.display = "none";
        if (dbSaveFeedback) dbSaveFeedback.textContent = "";

        if (!file) {
            filename.textContent = "Belum ada file dipilih";
            setStatus("Pilih file CSV atau klik 'Muat dari Database' untuk memulai.");
            return;
        }

        filename.textContent = file.name;
        if (!file.name.toLowerCase().endsWith(".csv")) {
            setStatus("Pilih file dengan ekstensi .csv.", "error");
            return;
        }

        setStatus("Membaca dan memeriksa CSV di browser…", "loading");
        try {
            renderDataset(file, parseCsv(await file.text()));
            if (btnSaveDb) btnSaveDb.style.display = "inline-block";
        } catch (error) {
            setStatus(error instanceof Error ? error.message : "CSV tidak dapat dibaca.", "error");
        }
    });
});
