const navButtons = document.querySelectorAll('.nav-btn');
const screens = document.querySelectorAll('.screen');

navButtons.forEach(button => {
    button.addEventListener('click', () => {
        // Obtenemos el ID de la pantalla que queremos abrir
        const targetScreenId = button.dataset.screen;

        // Quitamos la clase 'active' de TODAS las pantallas
        screens.forEach(screen => screen.classList.remove('active'));

        // Se la ponemos SOLO a la pantalla pulsada
        const targetScreen = document.getElementById(targetScreenId);
        if (targetScreen) {
            targetScreen.classList.add('active');
        }
    });
});