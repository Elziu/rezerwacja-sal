document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("reservation-form");
    const dateInput = document.getElementById("date");
    const startTimeInput = document.getElementById("start_time");
    const endTimeInput = document.getElementById("end_time");
    const roomInput = document.getElementById("room");
    const errorBox = document.getElementById("reservation-error");

    function showError(message) {
        errorBox.textContent = message;
    }

    function clearError() {
        errorBox.textContent = "";
    }

    function isWeekend(dateValue) {
        const date = new Date(dateValue);
        const day = date.getDay();

        return day === 0 || day === 6;
    }

    function validateForm() {
        clearError();

        if (!dateInput.value) {
            showError("Wybierz datę.");
            return false;
        }

        if (isWeekend(dateInput.value)) {
            showError("Nie można rezerwować sal w weekend.");
            return false;
        }

        if (!startTimeInput.value || !endTimeInput.value) {
            showError("Wybierz godziny rezerwacji.");
            return false;
        }

        if (startTimeInput.value >= endTimeInput.value) {
            showError("Godzina rozpoczęcia musi być wcześniejsza niż godzina zakończenia.");
            return false;
        }

        if (!roomInput.value) {
            showError("Wybierz salę.");
            return false;
        }

        return true;
    }

    dateInput.addEventListener("change", validateForm);
    startTimeInput.addEventListener("change", validateForm);
    endTimeInput.addEventListener("change", validateForm);
    roomInput.addEventListener("change", validateForm);

    form.addEventListener("submit", function (event) {
        if (!validateForm()) {
            event.preventDefault();
        }
    });
});
