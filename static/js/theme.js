/**
 * Academic Intelligence — Theme Management Engine
 * Handles Light/Dark mode toggling, localStorage persistence,
 * and dynamic Chart.js theme adaptation.
 */

(function () {
  "use strict";

  // 1. Detect saved theme and apply immediately to prevent FOUC (Flash of Unstyled Content)
  function getSavedTheme() {
    try {
      const saved = localStorage.getItem("theme");
      if (saved === "dark" || saved === "light") {
        return saved;
      }
    } catch (e) {
      console.warn("Theme storage access error:", e);
    }
    return "light";
  }

  const initialTheme = getSavedTheme();
  document.documentElement.setAttribute("data-theme", initialTheme);

  // Global Blue Chart Palette Definition
  window.chartPalette = {
    primary: "#2563EB",
    secondary: "#3B82F6",
    light: "#93C5FD",
    success: "#16A34A",
    warning: "#F59E0B",
    danger: "#DC2626",
    dark: {
      primary: "#3B82F6",
      secondary: "#93C5FD",
      light: "#DBEAFE",
      success: "#22C55E",
      warning: "#FBBF24",
      danger: "#F87171"
    }
  };

  // 2. Chart.js theme color updater
  function updateChartsForTheme(theme) {
    if (typeof Chart === "undefined") return;

    const isDark = theme === "dark";
    const textColor = isDark ? "#94A3B8" : "#475569";
    const gridColor = isDark ? "rgba(30, 41, 59, 0.8)" : "rgba(226, 232, 240, 0.8)";
    const tooltipBg = isDark ? "#112240" : "#0F172A";

    Chart.defaults.color = textColor;
    Chart.defaults.borderColor = gridColor;

    // In Chart.js 3+, Chart.instances is an object mapping id -> chart instance
    const instances =
      typeof Chart.instances === "object" && Chart.instances !== null
        ? Object.values(Chart.instances)
        : [];

    instances.forEach(function (chart) {
      if (!chart || !chart.options) return;

      // Update scales
      if (chart.options.scales) {
        Object.keys(chart.options.scales).forEach(function (key) {
          const scale = chart.options.scales[key];
          if (scale) {
            if (scale.ticks) scale.ticks.color = textColor;
            if (scale.grid) scale.grid.color = gridColor;
          }
        });
      }

      // Update plugins
      if (chart.options.plugins) {
        if (chart.options.plugins.legend && chart.options.plugins.legend.labels) {
          chart.options.plugins.legend.labels.color = textColor;
        }
        if (chart.options.plugins.tooltip) {
          chart.options.plugins.tooltip.backgroundColor = tooltipBg;
          chart.options.plugins.tooltip.titleColor = "#ffffff";
          chart.options.plugins.tooltip.bodyColor = "#cbd5e1";
        }
      }

      try {
        chart.update();
      } catch (err) {
        // Chart may still be initializing
      }
    });
  }

  // 3. Update Toggle Button UI (Icon and Label or Pill Switch)
  function updateToggleButtons(theme) {
    const isDark = theme === "dark";
    const buttons = document.querySelectorAll(".theme-toggle-btn, #themeToggleBtn, .theme-toggle-pill");

    buttons.forEach(function (btn) {
      if (btn.classList.contains("theme-toggle-pill")) {
        if (isDark) {
          btn.innerHTML = '<span>🌙 Dark</span><span class="theme-toggle-track"><span class="theme-toggle-thumb"></span></span>';
          btn.setAttribute("aria-label", "Switch to Light Mode");
          btn.setAttribute("title", "Switch to Light Mode");
        } else {
          btn.innerHTML = '<span>☀️ Light</span><span class="theme-toggle-track"><span class="theme-toggle-thumb"></span></span>';
          btn.setAttribute("aria-label", "Switch to Dark Mode");
          btn.setAttribute("title", "Switch to Dark Mode");
        }
      } else {
        if (isDark) {
          btn.innerHTML = '<i class="bi bi-sun-fill text-warning me-1"></i> Light';
          btn.setAttribute("aria-label", "Switch to Light Mode");
          btn.setAttribute("title", "Switch to Light Mode");
        } else {
          btn.innerHTML = '<i class="bi bi-moon-stars-fill text-light me-1"></i> Dark';
          btn.setAttribute("aria-label", "Switch to Dark Mode");
          btn.setAttribute("title", "Switch to Dark Mode");
        }
      }
    });
  }

  // 4. Public Toggle Function
  window.toggleTheme = function () {
    const currentTheme = document.documentElement.getAttribute("data-theme") || "light";
    const nextTheme = currentTheme === "dark" ? "light" : "dark";

    document.documentElement.setAttribute("data-theme", nextTheme);
    try {
      localStorage.setItem("theme", nextTheme);
    } catch (e) {
      console.warn("Could not persist theme to localStorage:", e);
    }

    updateToggleButtons(nextTheme);
    updateChartsForTheme(nextTheme);
  };

  window.getCurrentTheme = function () {
    return document.documentElement.getAttribute("data-theme") || "light";
  };

  window.updateChartsTheme = function () {
    updateChartsForTheme(window.getCurrentTheme());
  };

  // 5. Initialize on DOM ready
  document.addEventListener("DOMContentLoaded", function () {
    const current = getSavedTheme();
    document.documentElement.setAttribute("data-theme", current);
    updateToggleButtons(current);

    // Initial pass for Chart.js if charts are present
    setTimeout(function () {
      updateChartsForTheme(current);
    }, 150);
  });
})();
