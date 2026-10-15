/* NF01: indicador de progreso sin bloquear la interfaz; consulta el estado y recarga al terminar. */
(function () {
  var tarjeta = document.getElementById("progreso");
  if (!tarjeta || !window.Copiloto) { return; }
  var nodos = document.getElementById("progreso-nodos");
  var lento = document.getElementById("progreso-lento");
  window.Copiloto.sondear(tarjeta.getAttribute("data-url-estado"), {
    intervalo: 1500,
    alActualizar: function (datos) {
      if (nodos) { nodos.textContent = "Nodos completados: " + (datos.nodos.length ? datos.nodos.join(", ") : "ninguno aún"); }
      if (lento && datos.lento) { lento.classList.remove("d-none"); }
    }
  });
})();
