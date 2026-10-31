document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.getElementById("dataset-file");
    const filename = document.getElementById("dataset-filename");
    const status = document.getElementById("dataset-status");
    const results = document.getElementById("dataset-results");
    const previewHead = document.getElementById("preview-head");
    const previewBody = document.getElementById("preview-body");
    const typesBody = document.getElementById("types-body");

    if (!fileInput || !status || !results) return;

    const setStatus = (message, state = "") => {
        status.textContent = message;
        if (state) status.dataset.state = state;
        else delete status.dataset.state;
    };

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
        const present = values.map((value) => value.trim()).filter(Boolean);
        if (!present.length) return "Kosong";
        if (present.every((value) => /^(true|false)$/i.test(value))) return "Boolean";
        if (present.every((value) => /^[-+]?\d+$/.test(value))) return "Integer";
        if (present.every((value) => /^[-+]?(?:\d+\.?\d*|\.\d+)$/.test(value))) return "Numerik";
        if (present.every((value) => !Number.isNaN(Date.parse(value)) && /[-/]/.test(value))) return "Tanggal/teks";
        return "Teks";
    };

    const renderDataset = (file, rows) => {
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
            (count, values) => count + (values[column].trim() === "" ? 1 : 0), 0
        ));
        const duplicateRows = new Set();
        const seenRows = new Set();

        dataRows.forEach((values, index) => {
            const signature = JSON.stringify(values.map((value) => value.trim()));
            if (seenRows.has(signature)) duplicateRows.add(index);
            else seenRows.add(signature);
        });

        document.getElementById("summary-filename").textContent = file.name;
        document.getElementById("summary-rows").textContent = String(dataRows.length);
        document.getElementById("summary-columns").textContent = String(headers.length);
        document.getElementById("summary-missing").textContent = `${missingByColumn.reduce((a, b) => a + b, 0)} nilai kosong`;
        document.getElementById("summary-duplicates").textContent = `${duplicateRows.size} baris`;
        document.getElementById("summary-target").textContent = headers.includes("Burnout_Risk") ? "Tersedia" : "Tidak ditemukan";

        previewHead.replaceChildren(...headers.map((header) => makeCell("th", header, "col")));
        previewBody.replaceChildren(...dataRows.slice(0, 10).map((values) => {
            const tr = document.createElement("tr");
            tr.append(...values.map((value) => makeCell("td", value || "—")));
            return tr;
        }));
        document.getElementById("preview-count").textContent = `(${Math.min(dataRows.length, 10)} dari ${dataRows.length} baris)`;

        typesBody.replaceChildren(...headers.map((header, column) => {
            const tr = document.createElement("tr");
            tr.append(
                makeCell("td", header),
                makeCell("td", detectType(dataRows.map((values) => values[column]))),
                makeCell("td", String(missingByColumn[column]))
            );
            return tr;
        }));

        results.hidden = false;
        setStatus("CSV berhasil dibaca untuk pratinjau lokal.", "success");
    };

    fileInput.addEventListener("change", async () => {
        const file = fileInput.files?.[0];
        results.hidden = true;
        if (!file) {
            filename.textContent = "Belum ada file dipilih";
            setStatus("Pilih file CSV untuk memulai pemeriksaan.");
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
        } catch (error) {
            setStatus(error instanceof Error ? error.message : "CSV tidak dapat dibaca.", "error");
        }
    });
});
