/* =========================================================
   Freebuff — Responsive Interactions
   ========================================================= */

(function () {
  "use strict";

  /* ---- Hamburger menu ---- */
  var hamburger = document.getElementById("hamburger");
  var mobileNav = document.getElementById("mobileNav");
  var navOverlay = document.getElementById("navOverlay");
  var navLinks = document.querySelectorAll(".nav-link");

  var focusedEl = null;

  function getFocusableElements(container) {
    return container.querySelectorAll(
      'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );
  }

  function trapFocus(e) {
    var focusable = getFocusableElements(mobileNav);
    if (focusable.length === 0) return;
    var first = focusable[0];
    var last = focusable[focusable.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }

  function toggleNav(force) {
    var isOpen = force !== undefined ? force : hamburger.getAttribute("aria-expanded") === "false";
    hamburger.setAttribute("aria-expanded", isOpen);
    mobileNav.classList.toggle("open", isOpen);
    navOverlay.classList.toggle("open", isOpen);
    // Lock scroll on html to avoid layout shift (body shift is more common)
    document.documentElement.style.overflow = isOpen ? "hidden" : "";

    if (isOpen) {
      focusedEl = document.activeElement;
      setTimeout(function () {
        var focusable = getFocusableElements(mobileNav);
        if (focusable.length > 0) focusable[0].focus();
      }, 100);
      document.addEventListener("keydown", trapFocus);
    } else {
      if (focusedEl) focusedEl.focus();
      focusedEl = null;
      document.removeEventListener("keydown", trapFocus);
    }
  }

  function closeNav() {
    toggleNav(false);
  }

  if (hamburger && mobileNav) {
    hamburger.addEventListener("click", function (e) {
      e.stopPropagation();
      toggleNav();
    });

    // Close on overlay click
    if (navOverlay) {
      navOverlay.addEventListener("click", closeNav);
    }

    // Close on Escape key
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && hamburger.getAttribute("aria-expanded") === "true") {
        closeNav();
      }
    });

    // Close on link click
    for (var i = 0; i < navLinks.length; i++) {
      navLinks[i].addEventListener("click", closeNav);
    }

    // Close on window resize (back to desktop)
    var resizeTimer;
    window.addEventListener("resize", function () {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(function () {
        if (window.innerWidth > 767 && hamburger.getAttribute("aria-expanded") === "true") {
          closeNav();
        }
      }, 200);
    });
  }

  /* ---- Form loading states ---- */
  document.addEventListener("submit", function (event) {
    var form = event.target;
    var submitBtn =
      form.querySelector('button[type="submit"], .btn[type="submit"]') ||
      form.querySelector(".btn, .btn-small");
    if (submitBtn && !submitBtn.classList.contains("is-loading")) {
      submitBtn.classList.add("is-loading");
    }
  });

  /* ---- Touch active state enhancement ---- */
  // Ensure :active works on touch devices for all interactive elements
  document.addEventListener("touchstart", function () {}, { passive: true });

  /* ---- Smooth scroll for anchor links ---- */
  var anchorLinks = document.querySelectorAll('a[href^="#"]');
  for (var a = 0; a < anchorLinks.length; a++) {
    anchorLinks[a].addEventListener("click", function (e) {
      var href = this.getAttribute("href");
      if (href === "#") return;
      var target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        var headerH = 70; // account for sticky header
        var targetPos = target.getBoundingClientRect().top + window.pageYOffset - headerH;
        window.scrollTo({ top: targetPos, behavior: "smooth" });
      }
    });
  }

  /* ---- Content detail modals (tutorials / news) ---- */
  var modalFocusedEl = null;

  function stopVideo(overlay) {
    var iframe = overlay.querySelector("iframe[data-src]");
    if (iframe) iframe.src = "";
  }

  function startVideo(overlay) {
    var iframe = overlay.querySelector("iframe[data-src]");
    if (iframe && !iframe.src) iframe.src = iframe.getAttribute("data-src");
  }

  function closeModal(overlay) {
    overlay.classList.remove("open");
    stopVideo(overlay);
    document.documentElement.style.overflow = "";
    document.removeEventListener("keydown", modalKeydown);
    if (modalFocusedEl) {
      modalFocusedEl.focus();
      modalFocusedEl = null;
    }
  }

  function modalKeydown(e) {
    if (e.key === "Escape") {
      var openOverlay = document.querySelector(".modal-overlay.open");
      if (openOverlay) closeModal(openOverlay);
    }
  }

  function openModal(id) {
    var overlay = document.getElementById("modal-" + id);
    if (!overlay) return;
    modalFocusedEl = document.activeElement;
    overlay.classList.add("open");
    startVideo(overlay);
    document.documentElement.style.overflow = "hidden";
    document.addEventListener("keydown", modalKeydown);
    var closeBtn = overlay.querySelector("[data-close-modal]");
    if (closeBtn) closeBtn.focus();
  }

  var openTriggers = document.querySelectorAll("[data-open-modal]");
  for (var m = 0; m < openTriggers.length; m++) {
    openTriggers[m].addEventListener("click", function () {
      openModal(this.getAttribute("data-open-modal"));
    });
  }

  var closeTriggers = document.querySelectorAll("[data-close-modal]");
  for (var c = 0; c < closeTriggers.length; c++) {
    closeTriggers[c].addEventListener("click", function () {
      closeModal(this.closest(".modal-overlay"));
    });
  }

  var modalOverlays = document.querySelectorAll("[data-modal-overlay]");
  for (var o = 0; o < modalOverlays.length; o++) {
    modalOverlays[o].addEventListener("click", function (e) {
      if (e.target === this) closeModal(this);
    });
  }

  /* ---- Reveal on scroll ---- */
  var revealEls = document.querySelectorAll(".reveal");
  if (revealEls.length) {
    if ("IntersectionObserver" in window) {
      var revealObserver = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              entry.target.classList.add("is-visible");
              revealObserver.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
      );
      for (var r = 0; r < revealEls.length; r++) {
        revealObserver.observe(revealEls[r]);
      }
    } else {
      // Fallback: no IntersectionObserver support, show everything immediately
      for (var f = 0; f < revealEls.length; f++) {
        revealEls[f].classList.add("is-visible");
      }
    }
  }
})();
