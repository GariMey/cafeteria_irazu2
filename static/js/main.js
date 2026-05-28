/* ═══════════════════════════════════════════════════════
   CAFETERÍA IRAZÚ — Main JavaScript
   ═══════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

    // ── Navbar scroll effect ──────────────────────────────
    const navbar = document.getElementById('navbar');
    if (navbar) {
        const onScroll = () => {
            if (window.scrollY > 60) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        };
        window.addEventListener('scroll', onScroll, { passive: true });
    }

    // ── Mobile menu toggle ────────────────────────────────
    const menuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    if (menuBtn && mobileMenu) {
        menuBtn.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
        // Close on link click
        mobileMenu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => mobileMenu.classList.add('hidden'));
        });
    }

    // ── Scroll reveal ─────────────────────────────────────
    const revealEls = document.querySelectorAll('.scroll-reveal');
    if (revealEls.length > 0) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry, i) => {
                if (entry.isIntersecting) {
                    setTimeout(() => {
                        entry.target.classList.add('revealed');
                    }, entry.target.dataset.delay || 0);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.12, rootMargin: '0px 0px -50px 0px' });

        revealEls.forEach((el, i) => {
            el.style.transitionDelay = `${i * 60}ms`;
            observer.observe(el);
        });
    }

    // ── Category filter ───────────────────────────────────
    const categoryTabs = document.querySelectorAll('.category-tab');
    const productCards = document.querySelectorAll('.product-card');

    if (categoryTabs.length > 0) {
        categoryTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // Update active state
                categoryTabs.forEach(t => {
                    t.classList.remove('active', 'bg-espresso', 'text-crema');
                    t.classList.add('border-espresso/30', 'text-espresso');
                });
                tab.classList.add('active', 'bg-espresso', 'text-crema');
                tab.classList.remove('border-espresso/30');

                const filter = tab.dataset.category;

                productCards.forEach(card => {
                    if (filter === 'all' || card.dataset.category === filter) {
                        card.style.display = '';
                        card.style.animation = 'fadeInUp 0.4s ease forwards';
                    } else {
                        card.style.display = 'none';
                    }
                });
            });
        });
    }

    // ── Auto-dismiss messages ──────────────────────────────
    const container = document.getElementById('messages-container');
    if (container) {
        setTimeout(() => {
            container.querySelectorAll('.message-toast').forEach(toast => {
                toast.style.transition = 'opacity 0.5s, transform 0.5s';
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(20px)';
                setTimeout(() => toast.remove(), 500);
            });
        }, 5000);
    }

    // ── Smooth anchor scroll with offset ─────────────────
    document.querySelectorAll('a[href*="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            const hashIndex = href.indexOf('#');
            if (hashIndex === -1) return;

            const hash = href.substring(hashIndex);
            const target = document.querySelector(hash);
            if (!target) return;

            // Only prevent default for same-page anchors
            const path = href.substring(0, hashIndex) || window.location.pathname;
            if (path === window.location.pathname || path === '') {
                e.preventDefault();
                const offsetTop = target.getBoundingClientRect().top + window.pageYOffset - 80;
                window.scrollTo({ top: offsetTop, behavior: 'smooth' });
            }
        });
    });

    // ── Gallery lightbox (basic) ──────────────────────────
    const galleryItems = document.querySelectorAll('.gallery-item');
    galleryItems.forEach(item => {
        item.addEventListener('click', () => {
            const img = item.querySelector('img');
            if (!img) return;

            const overlay = document.createElement('div');
            overlay.className = 'fixed inset-0 z-50 bg-black/90 flex items-center justify-center cursor-zoom-out p-6';
            overlay.innerHTML = `<img src="${img.src}" alt="${img.alt}" class="max-h-full max-w-full rounded-xl shadow-2xl object-contain">`;
            overlay.addEventListener('click', () => overlay.remove());
            document.body.appendChild(overlay);
        });
    });

});
