// Theme toggle with localStorage
(function () {
  var body = document.body;
  var saved = localStorage.getItem("bms-theme");
  if (saved === "light") body.classList.replace("theme-dark", "theme-light");
  if (saved === "dark") body.classList.replace("theme-light", "theme-dark");

  var btn = document.getElementById("themeToggle");
  if (btn) {
    btn.addEventListener("click", function () {
      var isDark = body.classList.contains("theme-dark");
      body.classList.toggle("theme-dark", !isDark);
      body.classList.toggle("theme-light", isDark);
      localStorage.setItem("bms-theme", isDark ? "light" : "dark");
    });
  }

  // Active nav highlight
  var here = window.location.pathname;
  document.querySelectorAll(".nav a").forEach(function (a) {
    var p = a.getAttribute("data-path") || a.getAttribute("href");
    if (p && here.startsWith(p)) a.classList.add("active");
  });
})();
