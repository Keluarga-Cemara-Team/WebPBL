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

    const prepOptDedup = document.getElementById("prep-opt-dedup");
    const prepDupsBadge = document.getElementById("prep-dups-badge");
    const prepOptImputeNum = document.getElementById("prep-opt-impute-num");
    const prepOptImputeCat = document.getElementById("prep-opt-impute-cat");
    const prepOptOutlier = document.getElementById("prep-opt-outlier");
    const prepOutliersBadge = document.getElementById("prep-outliers-badge");
    const prepOptEncoding = document.getElementById("prep-opt-encoding");
    const prepEncodingPreview = document.getElementById("prep-encoding-preview");
    const prepOptScaling = document.getElementById("prep-opt-scaling");
    const prepSummaryStatus = document.getElementById("prep-summary-status");
    const btnDownloadCleaned = document.getElementById("btn-download-cleaned");

    // State cache
    let currentDataset = null;
    let detectedOutliersInfo = { totalOutliers: 0, columnsWithOutliers: 0, columnBounds: {} };

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

        // Aktifkan tombol
        if (btnEda) btnEda.disabled = false;
        if (btnPrep) btnPrep.disabled = false;

        // Siapkan kontrol Preprocessing
        initPreprocessingControls();

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
    };

    const updateSelectedColsCount = () => {
        const checkboxes = Array.from(prepColumnsGrid.querySelectorAll(".prep-col-check"));
        const checked = checkboxes.filter((checkbox) => checkbox.checked && !checkbox.disabled);
        prepSelectedColsCount.textContent = String(checked.length);
        prepTotalColsCount.textContent = String(checkboxes.filter((checkbox) => !checkbox.disabled).length);
    };

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
        });
    }

    if (btnColDeselectAll) {
        btnColDeselectAll.addEventListener("click", () => {
            prepColumnsGrid.querySelectorAll(".prep-col-check").forEach(cb => cb.checked = false);
            updateSelectedColsCount();
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
        });
    }

    if (prepColumnsGrid) {
        prepColumnsGrid.addEventListener("change", (e) => {
            if (e.target.classList.contains("prep-col-check")) {
                updateSelectedColsCount();
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
            if (btnColRecommend) btnColRecommend.click();
            renderEncodingPreview();
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

        // 2. Baris Duplikat
        const filteredSourceIndices = dataRows
            .map((_, index) => index)
            .filter((index) => !prepOptDedup.checked || !duplicateRows.has(index));
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
