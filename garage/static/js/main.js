document.addEventListener('DOMContentLoaded', () => {
    const nav = document.getElementById('mainNav');
    if (!nav || !nav.classList.contains('navbar-transparent')) return;

    const toggle = () => {
        nav.classList.toggle('scrolled', window.scrollY > 50);
    };

    toggle();
    window.addEventListener('scroll', toggle);
});
