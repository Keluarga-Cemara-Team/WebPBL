// AntiBurnout Web Presentation Interactivity
document.addEventListener("DOMContentLoaded", () => {
    // Sinkronisasi badge range input real-time
    const rangeInputs = document.querySelectorAll(".range-input");
    rangeInputs.forEach((input) => {
        const badge = document.getElementById(input.id + "_val");
        if (badge) {
            input.addEventListener("input", (e) => {
                badge.textContent = e.target.value;
            });
        }
    });

    console.log("AntiBurnout Web Presentation Layer initialized.");
});
