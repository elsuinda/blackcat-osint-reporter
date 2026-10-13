// BLACKCAT - confirmacion de acciones destructivas (sin JS inline, CSP-friendly)
(function () {
  "use strict";
  document.addEventListener("submit", function (ev) {
    var f = ev.target;
    if (f && f.classList && f.classList.contains("confirmar")) {
      var msg = f.getAttribute("data-msg") || "Confirmar esta accion?";
      if (!window.confirm(msg)) {
        ev.preventDefault();
      }
    }
  });
})();
