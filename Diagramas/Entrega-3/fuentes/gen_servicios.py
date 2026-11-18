import sys
sys.path.insert(0, ".")
from uml import clase, render

C = [
 clase("CopilotoService", ["-control_cuota: ControlCuota"], ["+ejecutar(usuario, intencion, **entrada): dict"], "Facade"),
 clase("GrafoCopiloto", ["-llm", "-trazador", "-control_cuota"], ["+construir(): StateGraph", "+invocar(estado): dict"]),
 clase("ControlCuota", [], ["+verificar(usuario): bool", "+resumen(usuario): dict"]),
 clase("registro", ["_REGISTRO: dict"], ["+registrar_nodo(nombre, fabrica, intenciones, orden)", "+nodos_para(intencion): list"], "module"),
 clase("MagnetoClient", [], ["+autenticar(email, clave)", "+obtener_perfil(magneto_id)", "+obtener_hv(magneto_id): ArchivoHVMagneto", "+postular(magneto_id, vacante_id, perfil): str"], "interface"),
 clase("MagnetoMockClient", ["-hojas_vida", "+postulaciones: list"], ["+obtener_hv(...)", "+postular(...)"]),
 clase("ArchivoHVMagneto", ["+nombre", "+formato", "+contenido: bytes"], ["+huella: str"], "dataclass", sprint3=True),
 clase("acceso_magneto.servicios", [], ["+importar_hv_magneto(usuario, cliente)"], "module", sprint3=True),
 clase("matching_vacantes.servicios", [], ["+calcular_ajustes(usuario, perfil)", "+generar_alertas(usuario, umbral)", "+generar_alertas_todos(umbral)"], "module", sprint3=True),
 clase("adaptacion_hv.servicios", [], ["+adaptar(usuario, perfil, vacante)", "+decidir(adaptacion, decisiones): int", "+comparacion(adaptacion): list", "+documento_word(adaptacion): bytes"], "module", sprint3=True),
 clase("postulaciones.servicios", [], ["+postular(usuario, vacante, perfil|adaptacion)", "+calcular_ajuste(...)", "+retirar(postulacion)"], "module", sprint3=True),
 clase("reclutador.servicios", ["SUGERENCIAS: dict"], ["+vacantes_del_reclutador(usuario)", "+candidatos_por_ajuste(vacante, estado)", "+decidir(reclutador, postulacion, decision, comentario)", "+retroalimentacion_para(...)"], "module", sprint3=True),
 clase("Usuario", ["+email", "+rol", "+magneto_id"], [], "model"),
 clase("HojaVida", ["+origen", "+huella", "+estado"], [], "model"),
 clase("PerfilExtraido", ["+datos (cifrado)"], [], "model"),
 clase("Vacante", ["+requisitos", "+reclutador"], [], "model"),
 clase("AlertaVacante", ["+score", "+leida"], [], "model", sprint3=True),
 clase("HVAdaptada", ["+cambios (cifrado)", "+perfil_adaptado (cifrado)", "+estado"], [], "model", sprint3=True),
 clase("Postulacion", ["+perfil_enviado (cifrado)", "+score", "+estado", "+retroalimentacion"], ["+abierta(): bool", "+decidida(): bool"], "model", sprint3=True),
]
E = """
  edge [arrowhead=vee];
  "CopilotoService" -> "GrafoCopiloto"; "CopilotoService" -> "ControlCuota"; "GrafoCopiloto" -> "registro";
  "matching_vacantes.servicios" -> "CopilotoService" [xlabel="buscar_vacantes"];
  "adaptacion_hv.servicios" -> "CopilotoService" [xlabel="adaptar_hv"];
  "postulaciones.servicios" -> "CopilotoService" [xlabel="buscar_vacantes"];
  "postulaciones.servicios" -> "MagnetoClient";
  "acceso_magneto.servicios" -> "MagnetoClient";
  "MagnetoClient" -> "ArchivoHVMagneto" [style=dashed, xlabel="crea"];
  edge [arrowhead=empty, style=dashed]; "MagnetoMockClient" -> "MagnetoClient";
  edge [arrowhead=vee, style=dotted, color="#777777"];
  "acceso_magneto.servicios" -> "HojaVida"; "matching_vacantes.servicios" -> "AlertaVacante";
  "adaptacion_hv.servicios" -> "HVAdaptada"; "postulaciones.servicios" -> "Postulacion"; "reclutador.servicios" -> "Postulacion";
  edge [arrowhead=none, style=solid, color="#333333"];
  "Usuario" -> "HojaVida" [headlabel="*", taillabel="1"]; "HojaVida" -> "PerfilExtraido" [headlabel="0..1", taillabel="1"];
  "HojaVida" -> "HVAdaptada" [headlabel="*", taillabel="1"]; "Vacante" -> "Postulacion" [headlabel="*", taillabel="1"];
  "Usuario" -> "Postulacion" [headlabel="*", taillabel="1"]; "HVAdaptada" -> "Postulacion" [headlabel="*", taillabel="0..1"];
  "Usuario" -> "AlertaVacante" [headlabel="*", taillabel="1"]; "Vacante" -> "AlertaVacante" [headlabel="*", taillabel="1"];
  "Usuario" -> "Vacante" [headlabel="*", taillabel="0..1 reclutador"];
"""
render("clases_servicios", "\n".join(C) + E, rankdir="TB")
