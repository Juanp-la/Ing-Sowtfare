/* HU02: muestra el nombre del archivo elegido antes de cargarlo. */
(function () {
  var entrada = document.getElementById("id_archivo");
  var nombre = document.getElementById("nombre-seleccionado");
  if (!entrada || !nombre) { return; }
  entrada.addEventListener("change", function () {
    var archivo = entrada.files && entrada.files[0];
    nombre.textContent = archivo ? "Seleccionado: " + archivo.name : "";
  });
})();
