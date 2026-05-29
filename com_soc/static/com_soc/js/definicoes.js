const saveBtn = document.getElementById("save-ai-thresholds");

saveBtn.addEventListener("click", async () => {

    const ideal = document.querySelector('[name="ideal_threshold"]').value;
    const low = document.querySelector('[name="low_threshold"]').value;
    const medium = document.querySelector('[name="medium_threshold"]').value;
    const high = document.querySelector('[name="high_threshold"]').value;

    const response = await fetch("/com_soc/save_config/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken(),
        },
        body: JSON.stringify({
            ideal_threshold: ideal,
            low_threshold: low,
            medium_threshold: medium,
            high_threshold: high,
        }),
    });

    const data = await response.json();

    if (data.success) {
        showToast();
    } else {
        alert("Erro ao guardar.");
    }
});

function getCSRFToken() {
    return document.cookie
        .split("; ")
        .find(row => row.startsWith("csrftoken="))
        ?.split("=")[1];
}

function showToast() {

    const toast = document.getElementById("toast");

    toast.classList.add("show");

    setTimeout(() => {
        toast.classList.remove("show");
    }, 2500);
}