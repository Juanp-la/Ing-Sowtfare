/* Utilidades JS del núcleo (sin dependencias). */
window.Copiloto = (function () {
  // Pide confirmación en formularios con data-confirmar="mensaje".
  document.addEventListener("submit", function (evento) {
    var form = evento.target;
    var mensaje = form.getAttribute && form.getAttribute("data-confirmar");
    if (mensaje && !window.confirm(mensaje)) { evento.preventDefault(); }
  });

  // Consulta periódicamente una URL JSON sin bloquear la interfaz (NF01).
  function sondear(url, opciones) {
    var intervalo = (opciones && opciones.intervalo) || 1500;
    var alActualizar = (opciones && opciones.alActualizar) || function () {};
    var alTerminar = (opciones && opciones.alTerminar) || function () { window.location.reload(); };
    function paso() {
      fetch(url, { headers: { "Accept": "application/json" }, credentials: "same-origin" })
        .then(function (r) { return r.json(); })
        .then(function (datos) {
          alActualizar(datos);
          if (datos.terminado) { alTerminar(datos); } else { setTimeout(paso, intervalo); }
        })
        .catch(function () { setTimeout(paso, intervalo * 2); });
    }
    paso();
  }

  return { sondear: sondear };
})();
