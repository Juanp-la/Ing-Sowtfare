# Criterios de aceptación: Feature 7 `preparacion`

Rama `feature-7-preparacion-agente-coach` · Capacidad: Preparación (agente Coach) · Sube: David.

| Ítem | SP | Responsable (Project) | Fuente de criterios |
|---|---|---|---|
| HU16 Preguntas probables de entrevista | 5 | David | derivado del enunciado y del Excel de UH; por validar con el PO, ver FUENTES_CRITERIOS.md del Excel: "generadas a partir de la vacante y las brechas" |
| HU17 Plan de mejora con acciones | 5 | David | derivado del enunciado y del Excel de UH; por validar con el PO, ver FUENTES_CRITERIOS.md del Excel: "acciones concretas por cada brecha detectada" |

Grafo, intención `preparar`: `control_cuota → supervisor → coach → END`. Las brechas salen de la comparación
requisito por requisito del núcleo (`core.dominio.requisitos`), así la feature funciona sola, sin depender del Matcher.
Las reglas generan el borrador de preguntas y plan; el LLM puede redactarlo mejor, pero el Coach garantiza que toda
brecha tenga una acción. Se guarda en `PreguntaEntrevista` y `PlanMejora` (asociado a HV, vacante y último diagnóstico).

Flujo: `Preparación` (lista de vacantes de la BD con acción **Preparar**) → página de la vacante con brechas →
**Generar preguntas y plan**. Si la rama de matching está integrada, el detalle de la vacante enlaza aquí.

## HU16: Como candidato quiero recibir preguntas probables de entrevista para prepararme

| # | Criterio derivado del enunciado y del Excel de UH; por validar con el PO, ver FUENTES_CRITERIOS.md | Prueba (`tests/test_hu16_preguntas.py`) |
|---|---|---|
| CA1 | Dada una vacante, cuando genero la preparación, entonces recibo preguntas técnicas sobre requisitos que cumplo, preguntas sobre cada brecha (máx. 3) y preguntas conductuales sobre la empresa y el cargo. | `test_ca1_preguntas_generadas_desde_la_vacante_y_las_brechas` |
| CA2 | Cada pregunta trae una sugerencia de cómo responderla basada en mi experiencia real. | `test_ca2_cada_pregunta_trae_una_sugerencia_para_responder` |
| CA3 | Las preguntas se guardan y puedo volver a verlas; al regenerar se reemplazan. | `test_ca3_se_guardan_y_al_regenerar_se_reemplazan` |
| CA4 | Sin HV analizada se muestra un estado vacío y no se genera nada. | `test_ca4_sin_hv_analizada_muestra_estado_vacio` |

## HU17: Como candidato quiero un plan de mejora con acciones concretas para cerrar mis brechas

| # | Criterio derivado del enunciado y del Excel de UH; por validar con el PO, ver FUENTES_CRITERIOS.md | Prueba (`tests/test_hu17_plan.py`) |
|---|---|---|
| CA1 | Por cada brecha detectada hay una acción concreta con recurso y plazo. | `test_ca1_una_accion_concreta_por_cada_brecha_con_recurso_y_plazo` |
| CA2 | Las brechas de requisitos obligatorios aparecen primero (prioridad alta). | `test_ca2_las_brechas_obligatorias_van_primero` |
| CA3 | Si no hay brechas, el plan lo indica. | `test_ca3_sin_brechas_el_plan_lo_indica` |
| CA4 | El plan queda guardado asociado a la HV, la vacante y el último diagnóstico. | `test_ca4_el_plan_se_guarda_asociado_a_la_hv_la_vacante_y_el_diagnostico` |
| CA5 | Si el LLM omite una brecha, el Coach agrega la acción faltante. | `test_ca5_si_el_llm_omite_una_brecha_el_coach_la_completa` |

## Fuera de alcance
Simulacro de entrevista interactivo y seguimiento de postulaciones (HU15, HU18: Sprint 3 o posterior).
