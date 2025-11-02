document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menuToggle');
    const sideNav = document.getElementById('sideNav');
    const overlay = document.getElementById('overlay');
    const mainContainer = document.getElementById('mainContainer');

    // Toggle menu when clicking the menu button
    menuToggle.addEventListener('click', function(e) {
        e.stopPropagation();
        sideNav.classList.toggle('minimized');
        overlay.classList.toggle('active');
    });

    // Close menu when clicking the overlay
    overlay.addEventListener('click', function() {
        sideNav.classList.add('minimized');
        overlay.classList.remove('active');
    });

    // Close menu when clicking the main container
    mainContainer.addEventListener('click', function(e) {
        if (!sideNav.contains(e.target) && !menuToggle.contains(e.target)) {
            sideNav.classList.add('minimized');
            overlay.classList.remove('active');
        }
    });
});