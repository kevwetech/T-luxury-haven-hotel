"use strict"

const hamburger = document.getElementById('hamburger');
const mobDrawer = document.getElementById('mobDrawer');
const mobOverlay = document.getElementById('mobOverlay');
const mobClose = document.getElementById('mobClose');

function openMenu() {
  mobDrawer.classList.add('active');
  mobOverlay.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeMenu() {
  mobDrawer.classList.remove('active');
  mobOverlay.classList.remove('active');
  document.body.style.overflow = '';
}

hamburger.addEventListener('click', openMenu);
mobClose.addEventListener('click', closeMenu);
mobOverlay.addEventListener('click', closeMenu);


/* ── T-LUXURY HAVEN — SCROLL ANIMATIONS ── */

const ANIMATION_CLASSES = {
  fadeUp:    'anim-fade-up',
  fadeLeft:  'anim-fade-left',
  fadeRight: 'anim-fade-right',
  fadeIn:    'anim-fade-in',
  scaleUp:   'anim-scale-up',
};

// Elements to animate and which animation to apply
const SELECTORS = [
  // Generic reveal
  { sel: '.home-about-text',        anim: 'fadeLeft',  delay: 0   },
  { sel: '.home-stats-grid',        anim: 'fadeRight', delay: 100 },
  { sel: '.home-stat-card',         anim: 'fadeUp',    delay: 100, stagger: true },
  { sel: '.home-section-header',    anim: 'fadeUp',    delay: 0   },
  { sel: '.home-service-card',      anim: 'fadeUp',    delay: 0},
  { sel: '.home-room-card',         anim: 'fadeUp',    delay: 0,   stagger: true },
  { sel: '.home-gallery-item',      anim: 'scaleUp',   delay: 0,   stagger: true },
  { sel: '.testimonial-card',       anim: 'fadeUp',    delay: 0,   stagger: true },
  { sel: '.home-contact-info',      anim: 'fadeLeft',  delay: 0   },
  { sel: '.home-contact-form-card', anim: 'fadeRight', delay: 100 },

  // About page
  { sel: '.about-story-text',       anim: 'fadeLeft',  delay: 0   },
  { sel: '.about-story-img-wrap',   anim: 'fadeRight', delay: 100 },
  { sel: '.about-stat-item',        anim: 'fadeUp',    delay: 0,   stagger: true },
  { sel: '.about-value-card',       anim: 'fadeUp',    delay: 0,   stagger: true },
  { sel: '.about-section-header',   anim: 'fadeUp',    delay: 0   },
  { sel: '.about-cta-heading',      anim: 'fadeUp',    delay: 0   },

  // Rooms page
  { sel: '.room-card',              anim: 'fadeUp',    delay: 0,   stagger: true },
  { sel: '.detail-hero-content',    anim: 'fadeUp',    delay: 0   },
  { sel: '.detail-body',            anim: 'fadeUp',    delay: 100 },
  { sel: '.booking-sidebar',        anim: 'fadeRight', delay: 200 },

  // Gallery page
  { sel: '.gallery-item',           anim: 'scaleUp',   delay: 0,   stagger: true },
  { sel: '.gallery-filters',        anim: 'fadeUp',    delay: 0   },

  // Contact page
  { sel: '.contact-layout > div',   anim: 'fadeUp',    delay: 0,   stagger: true },

  // My Bookings
  { sel: '.booking-card',           anim: 'fadeUp',    delay: 0,   stagger: true },
  { sel: '.page-header',            anim: 'fadeUp',    delay: 0   },

  // Booking form
  { sel: '.booking-form',           anim: 'fadeUp',    delay: 100 },
  { sel: '.form-wrap',              anim: 'fadeUp',    delay: 0   },
];

// Add base CSS via JS so no extra file needed
const style = document.createElement('style');
style.textContent = `
  .anim-ready {
    opacity: 0;
    transition: opacity 0.7s ease, transform 0.7s ease;
  }
  .anim-fade-up   { transform: translateY(40px); }
  .anim-fade-left { transform: translateX(-40px); }
  .anim-fade-right{ transform: translateX(40px); }
  .anim-fade-in   { transform: none; }
  .anim-scale-up  { transform: scale(0.92); }

  .anim-visible {
    opacity: 1 !important;
    transform: none !important;
  }
`;
document.head.appendChild(style);

// Initialize all elements
function initAnimations() {
  SELECTORS.forEach(({ sel, anim, delay, stagger }) => {
    const els = document.querySelectorAll(sel);
    els.forEach((el, i) => {
      // Skip if already animated
      if (el.dataset.animated) return;
      el.dataset.animated = 'true';
      el.dataset.anim = anim;
      el.dataset.delay = stagger ? delay + i * 100 : delay;
      el.classList.add('anim-ready', ANIMATION_CLASSES[anim]);
    });
  });
}

// Intersection Observer
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (!entry.isIntersecting) return;
    const el = entry.target;
    const delay = parseInt(el.dataset.delay) || 0;
    setTimeout(() => {
      el.classList.add('anim-visible');
    }, delay);
    observer.unobserve(el);
  });
}, {
  threshold: 0.12,
  rootMargin: '0px 0px -40px 0px'
});

// Observe all animated elements
function observeAll() {
  document.querySelectorAll('.anim-ready').forEach(el => observer.observe(el));
}

// Run on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => { initAnimations(); observeAll(); });
} else {
  initAnimations();
  observeAll();
}