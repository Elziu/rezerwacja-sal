/**
 * Formularze rezerwacji
 */

class ReservationManager {
    constructor(roomReservations, options = {}) {
        this.roomReservations = roomReservations;
        this.options = {
            dateInputId: options.dateInputId || 'reservation-datepicker',
            timeFromId: options.timeFromId || 'time-from',
            timeToId: options.timeToId || 'time-to',
            roomInputId: options.roomInputId || 'selected-room-id',
            hintId: options.hintId || 'room-selection-hint',
            noRoomsMessageId: options.noRoomsMessageId || 'no-rooms-message',
            formId: options.formId || 'reservation-form',
            excludeReservationId: options.excludeReservationId || null
        };
        
        this.init();
    }

    init() {
        this.initDatePicker();
        this.initEventListeners();
        this.initRoomCards();
        this.initFormValidation();
    }

    initDatePicker() {
        new Pikaday({
            field: document.getElementById(this.options.dateInputId),
            format: 'YYYY-MM-DD',
            toString(date, format) {
                const day = ('0' + date.getDate()).slice(-2);
                const month = ('0' + (date.getMonth() + 1)).slice(-2);
                const year = date.getFullYear();
                return `${year}-${month}-${day}`;
            },
            minDate: new Date(),
            disableDayFn: (date) => {
                // Blokuj sobotę (6) i niedzielę (0)
                const day = date.getDay();
                return day === 0 || day === 6;
            },
            onSelect: () => {
                this.filterAvailableRooms();
            }
        });
    }

    initEventListeners() {
        document.getElementById(this.options.timeFromId).addEventListener('change', () => {
            this.filterAvailableRooms();
            this.updateTimeToOptions();
        });
        
        document.getElementById(this.options.timeToId).addEventListener('change', () => {
            this.filterAvailableRooms();
        });
    }

    initRoomCards() {
        document.querySelectorAll('.room-card').forEach(card => {
            card.addEventListener('click', () => this.selectRoom(card));
        });
    }

    initFormValidation() {
        document.getElementById(this.options.formId).addEventListener('submit', (e) => {
            if (!this.validateForm()) {
                e.preventDefault();
            }
        });
    }

    updateTimeToOptions() {
        const timeFrom = document.getElementById(this.options.timeFromId).value;
        const timeToSelect = document.getElementById(this.options.timeToId);
        
        if (!timeFrom) return;
        
        // Wyłącz godziny <= od wybranej "Godzina od"
        Array.from(timeToSelect.options).forEach(opt => {
            if (opt.value && opt.value <= timeFrom) {
                opt.disabled = true;
            } else if (opt.value) {
                opt.disabled = false;
            }
        });
        
        // Jeśli aktualna wartość "do" jest nieprawidłowa, wyczyść ją
        if (timeToSelect.value && timeToSelect.value <= timeFrom) {
            timeToSelect.value = '';
        }
    }

    filterAvailableRooms() {
        const dateInput = document.getElementById(this.options.dateInputId);
        const timeFrom = document.getElementById(this.options.timeFromId).value;
        const timeTo = document.getElementById(this.options.timeToId).value;
        const selectedDate = dateInput.value;

        const hint = document.getElementById(this.options.hintId);
        const noRoomsMessage = document.getElementById(this.options.noRoomsMessageId);
        const allRoomCards = document.querySelectorAll('.room-card');

        // Jeśli nie wybrano wszystkich pól
        if (!selectedDate || !timeFrom || !timeTo) {
            allRoomCards.forEach(card => {
                const badge = card.querySelector('.room-status-badge');
                badge.innerHTML = '<div class="badge badge-neutral gap-2">Sprawdź dostępność</div>';
                card.classList.remove('opacity-50', 'cursor-not-allowed');
                card.classList.add('cursor-pointer');
            });
            if (noRoomsMessage) noRoomsMessage.style.display = 'none';
            return;
        }

        // Sprawdź dostępność każdej sali
        let availableCount = 0;
        allRoomCards.forEach(card => {
            const roomId = card.dataset.roomId;
            const isAvailable = this.checkRoomAvailability(roomId, selectedDate, timeFrom, timeTo);
            const badge = card.querySelector('.room-status-badge');
            
            if (isAvailable) {
                badge.innerHTML = '<div class="badge badge-success gap-2">Dostępna</div>';
                card.classList.remove('opacity-50', 'cursor-not-allowed');
                card.classList.add('cursor-pointer');
                availableCount++;
            } else {
                badge.innerHTML = '<div class="badge badge-error gap-2">Zajęta</div>';
                card.classList.add('opacity-50', 'cursor-not-allowed');
                card.classList.remove('cursor-pointer');
            }
        });

        // Pokaż komunikat jeśli brak dostępnych sal
        if (noRoomsMessage) {
            noRoomsMessage.style.display = availableCount === 0 ? 'block' : 'none';
        }
    }

    checkRoomAvailability(roomId, date, timeFrom, timeTo) {
        const reservations = this.roomReservations[roomId] || [];
        
        // Filtruj rezerwacje dla wybranej daty
        const dayReservations = reservations.filter(r => r.date === date);
        
        // Sprawdź czy jest konflikt (nakładanie przedziałów)
        for (let res of dayReservations) {
            // Algorytm: A[from,to] i B[from,to] nachodzą gdy: A_from < B_to AND A_to > B_from
            if (timeFrom < res.time_to && timeTo > res.time_from) {
                return false; // Jest konflikt
            }
        }
        
        return true; // Brak konfliktu - sala dostępna
    }

    selectRoom(card) {
        // Sprawdź czy sala jest dostępna (nie ma klasy opacity-50)
        if (card.classList.contains('opacity-50')) {
            return; // Nie pozwól wybrać zajętej sali
        }
        
        // Usuń zaznaczenie z innych kart
        document.querySelectorAll('.room-card').forEach(c => {
            c.classList.remove('ring-4', 'ring-primary');
        });
        
        // Zaznacz aktualną kartę
        card.classList.add('ring-4', 'ring-primary');
        
        // Ustaw wartość w hidden input
        const roomId = card.dataset.roomId;
        const roomName = card.dataset.roomName;
        document.getElementById(this.options.roomInputId).value = roomId;
        
        // Zaktualizuj hint
        const hint = document.getElementById(this.options.hintId);
        if (hint) {
            hint.textContent = `Wybrano: ${roomName}`;
        }
    }

    validateForm() {
        const roomId = document.getElementById(this.options.roomInputId).value;
        const timeFrom = document.getElementById(this.options.timeFromId).value;
        const timeTo = document.getElementById(this.options.timeToId).value;
        
        if (!roomId) {
            alert('Proszę wybrać salę klikając na jej kartę');
            return false;
        }
        
        // Sprawdź czy godzina zakończenia jest późniejsza niż rozpoczęcia
        if (timeFrom >= timeTo) {
            alert('Godzina zakończenia musi być późniejsza niż godzina rozpoczęcia');
            return false;
        }
        
        return true;
    }
}
