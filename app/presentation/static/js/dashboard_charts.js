/**
 * AntiBurnout WebPBL - Dashboard Visual Analytics (Chart.js)
 * Merender grafik visual interaktif di halaman utama (Admin Console)
 * Menggunakan palet warna tema phpMyAdmin Classic.
 */

document.addEventListener("DOMContentLoaded", () => {
    const dataElement = document.getElementById("dashboard-analytics-data");
    if (!dataElement) return;

    let analyticsData;
    try {
        analyticsData = JSON.parse(dataElement.textContent || "{}");
    } catch (e) {
        console.error("Gagal mem-parsing data analitik dashboard:", e);
        return;
    }

    if (!analyticsData || !analyticsData.total_respondents) {
        console.log("Belum ada data responden untuk ditampilkan di grafik.");
        return;
    }

    // Pastikan Chart.js sudah termuat
    if (typeof Chart === "undefined") {
        console.warn("Chart.js belum termuat. Grafik tidak dapat diinisialisasi.");
        return;
    }

    // Konfigurasi Global Chart.js (Font & Style phpMyAdmin)
    Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif';
    Chart.defaults.font.size = 12;
    Chart.defaults.color = "#444";

    // Palet Warna Standar phpMyAdmin
    const COLORS = {
        primary: "#235a81",
        primaryLight: "rgba(35, 90, 129, 0.75)",
        success: "#5cb85c",
        successLight: "rgba(92, 184, 92, 0.8)",
        warning: "#f0ad4e",
        warningLight: "rgba(240, 173, 78, 0.8)",
        danger: "#d9534f",
        dangerLight: "rgba(217, 83, 79, 0.8)",
        info: "#5bc0de",
        infoLight: "rgba(91, 192, 222, 0.8)",
        purple: "#9351a6",
        purpleLight: "rgba(147, 81, 166, 0.8)"
    };

    // =========================================================================
    // 1. GRAFIK DOUGHNUT: Distribusi Tingkat Risiko Burnout
    // =========================================================================
    const ctxRisk = document.getElementById("chart-risk-distribution");
    if (ctxRisk && analyticsData.risk_distribution) {
        new Chart(ctxRisk, {
            type: "doughnut",
            data: {
                labels: analyticsData.risk_distribution.labels,
                datasets: [{
                    data: analyticsData.risk_distribution.data,
                    backgroundColor: [COLORS.success, COLORS.warning, COLORS.danger],
                    borderWidth: 2,
                    borderColor: "#ffffff",
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: {
                            boxWidth: 14,
                            padding: 12,
                            font: { size: 11, weight: "bold" }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const val = context.raw || 0;
                                const total = analyticsData.total_respondents || 1;
                                const pct = ((val / total) * 100).toFixed(1);
                                return ` ${context.label}: ${val} responden (${pct}%)`;
                            }
                        }
                    }
                },
                cutout: "62%"
            }
        });
    }

    // =========================================================================
    // 2. GRAFIK GROUPED BAR: Korelasi Jam Kerja vs Jam Tidur per Risiko
    // =========================================================================
    const ctxWorkSleep = document.getElementById("chart-work-sleep");
    if (ctxWorkSleep && analyticsData.work_sleep_by_risk) {
        new Chart(ctxWorkSleep, {
            type: "bar",
            data: {
                labels: analyticsData.work_sleep_by_risk.labels,
                datasets: [
                    {
                        label: "Rata-rata Jam Kerja (Jam/Minggu)",
                        data: analyticsData.work_sleep_by_risk.work_hours,
                        backgroundColor: COLORS.primaryLight,
                        borderColor: COLORS.primary,
                        borderWidth: 1,
                        borderRadius: 3
                    },
                    {
                        label: "Rata-rata Jam Tidur (Jam/Hari)",
                        data: analyticsData.work_sleep_by_risk.sleep_hours,
                        backgroundColor: COLORS.infoLight,
                        borderColor: COLORS.info,
                        borderWidth: 1,
                        borderRadius: 3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: "#ececec" },
                        ticks: { font: { size: 11 } }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { font: { size: 11, weight: "bold" } }
                    }
                },
                plugins: {
                    legend: {
                        position: "top",
                        labels: { boxWidth: 12, font: { size: 11 } }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return ` ${context.dataset.label}: ${context.raw} jam`;
                            }
                        }
                    }
                }
            }
        });
    }

    // =========================================================================
    // 3. GRAFIK HORIZONTAL BAR: Status Kesehatan Mental
    // =========================================================================
    const ctxMental = document.getElementById("chart-mental-health");
    if (ctxMental && analyticsData.mental_health_distribution) {
        new Chart(ctxMental, {
            type: "bar",
            data: {
                labels: ["Healthy (Prima)", "Needs Attention", "Critical"],
                datasets: [{
                    label: "Jumlah Responden",
                    data: analyticsData.mental_health_distribution.data,
                    backgroundColor: [COLORS.successLight, COLORS.warningLight, COLORS.dangerLight],
                    borderColor: [COLORS.success, COLORS.warning, COLORS.danger],
                    borderWidth: 1.5,
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: { color: "#ececec" },
                        ticks: { font: { size: 11 } }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { font: { size: 11, weight: "600" } }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const val = context.raw || 0;
                                const total = analyticsData.total_respondents || 1;
                                const pct = ((val / total) * 100).toFixed(1);
                                return ` ${val} responden (${pct}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    // =========================================================================
    // 4. GRAFIK RADAR: Indikator Pilar Kesejahteraan & Kualitas Kerja
    // =========================================================================
    const ctxPillars = document.getElementById("chart-wellness-pillars");
    if (ctxPillars && analyticsData.wellness_pillars) {
        const wp = analyticsData.wellness_pillars;
        new Chart(ctxPillars, {
            type: "radar",
            data: {
                labels: [
                    "Job Satisfaction (/10)",
                    "Work-Life Balance (/10)",
                    "Life Satisfaction (/10)",
                    "Productivity (/10)"
                ],
                datasets: [{
                    label: "Indeks Responden (Rata-rata)",
                    data: [
                        wp.job_satisfaction,
                        wp.work_life_balance,
                        wp.life_satisfaction,
                        (wp.productivity_score / 10).toFixed(1) // Normalisasi ke skala 10 agar serasi
                    ],
                    backgroundColor: "rgba(35, 90, 129, 0.25)",
                    borderColor: COLORS.primary,
                    borderWidth: 2,
                    pointBackgroundColor: COLORS.primary,
                    pointBorderColor: "#fff",
                    pointHoverBackgroundColor: "#fff",
                    pointHoverBorderColor: COLORS.primary,
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        min: 0,
                        max: 10,
                        ticks: { stepSize: 2, font: { size: 10 } },
                        grid: { color: "#e4e4e4" },
                        angleLines: { color: "#dcdcdc" },
                        pointLabels: { font: { size: 11, weight: "bold" }, color: "#333" }
                    }
                },
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: { boxWidth: 12, font: { size: 11 } }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return ` Skor Rerata: ${context.raw} / 10`;
                            }
                        }
                    }
                }
            }
        });
    }
});

