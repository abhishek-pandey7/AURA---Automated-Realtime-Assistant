document.addEventListener('DOMContentLoaded', () => {
    console.log('Landing page loaded successfully!');

    const nav = document.querySelector('nav');
    const mobileMenu = document.getElementById('mobile-menu');
    const navList = document.getElementById('nav-list');

    // 1. Sticky Navigation Effect
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            nav.classList.add('scrolled');
        } else {
            nav.classList.remove('scrolled');
        }
    });

    // 2. Mobile Menu Toggle
    mobileMenu.addEventListener('click', () => {
        navList.classList.toggle('active');
        
        // Animate hamburger to X
        const bars = mobileMenu.querySelectorAll('.bar');
        bars[0].style.transform = navList.classList.contains('active') 
            ? 'rotate(45deg) translate(5px, 6px)' 
            : 'none';
        bars[1].style.opacity = navList.classList.contains('active') 
            ? '0' 
            : '1';
        bars[2].style.transform = navList.classList.contains('active') 
            ? 'rotate(-45deg) translate(5px, -6px)' 
            : 'none';
    });

    // Close mobile menu when a link is clicked
    document.querySelectorAll('nav a').forEach(link => {
        link.addEventListener('click', () => {
            navList.classList.remove('active');
            const bars = mobileMenu.querySelectorAll('.bar');
            bars.forEach(bar => bar.style.transform = 'none');
            bars[1].style.opacity = '1';
        });
    });

    // Smooth scrolling for navigation links
    document.querySelectorAll('nav a').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 70, // Offset for sticky nav
                    behavior: 'smooth'
                });
            }
        });
    });

    // Simple animation for feature cards on scroll
    const observerOptions = {
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    document.querySelectorAll('.feature-card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'all 0.6s ease-out';
        observer.observe(card);
    });
});