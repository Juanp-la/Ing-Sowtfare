# Criterios de aceptación: Feature 3 `diagnostico_hv`

Rama `feature-3-diagnostico-de-hv-agente-evaluador` · Capacidad: Diagnóstico de HV (agente Evaluador) · Sube: Juan Pablo.

| Ítem | SP | Responsable (Project) | Fuente de criterios |
|---|---|---|---|
| HU05 Puntaje de la HV | 8 | Juan Pablo | Oficial (Entrega 1 §3.4) |
| HU06 Hallazgos priorizados | 5 | Juan Pablo | Oficial (Entrega 1 §3.4) |
| HU07 Explicación del puntaje | 5 | David | derivado del enunciado y del Excel de UH; por validar con el PO, ver FUENTES_CRITERIOS.md del Excel: "cada criterio de la rúbrica con su peso y evidencia" |
| NF01 Diagnóstico en menos de 30 s | 8 | Juan Pablo | Oficial (Entrega 1 §3.4) |
| NF05 Trazabilidad por agente | 5 | Miguel | derivado del enunciado y del Excel de UH; por validar con el PO, ver FUENTES_CRITERIOS.md del Excel: "registro de cada ejecución de agente (tabla EjecucionAgente)" |

Grafo, intención `diagnosticar`: `control_cuota → supervisor → evaluador → END`. El puntaje sale de una rúbrica
determinista y configurable (`RUBRICA_PESOS` en settings, deben sumar 100); el LLM solo redacta el resumen.

Rúbrica por defecto: contacto 15 · perfil profesional 10 · experiencia completa 25 · logros medibles 10 ·
educación 15 · habilidades 15 · idiomas 10. Niveles: < 50 bajo, 50-74 por mejorar, ≥ 75 competitivo.

## HU05: Como candidato quiero recibir un puntaje de mi hoja de vida para saber qué tan competitiva es

| # | Criterio | Prueba (`tests/test_hu05_puntaje.py`) |
|---|---|---|
| CA1 | El sistema entrega un puntaje entre 0 y 100 acompañado de un nivel (bajo, por mejorar, competitivo). | `test_ca1_puntaje_entre_0_y_100_con_nivel`, `test_ca1_niveles_bajo_y_por_mejorar` |
| CA2 | Si la hoja de vida no pudo procesarse, muestra «No fue posible leer el archivo, intente con otro formato» en lugar de un puntaje. | `test_ca2_hv_que_no_pudo_procesarse_...`, `test_ca2_perfil_ilegible_...` |

## HU06: Como candidato quiero ver los hallazgos priorizados de mi hoja de vida para saber qué corregir primero

| # | Criterio | Prueba (`tests/test_hu06_hallazgos.py`) |
|---|---|---|
| CA1 | Los hallazgos se presentan ordenados por prioridad (alta, media, baja), con máximo cinco por pantalla y con una acción sugerida por hallazgo. | `test_ca1_hallazgos_ordenados_por_prioridad_maximo_cinco_con_accion` |
| CA2 | Si no hay hallazgos, se muestra «Tu hoja de vida cumple los criterios básicos». | `test_ca2_sin_hallazgos_muestra_que_cumple_los_criterios_basicos` |

## HU07: Como candidato quiero ver por qué el sistema me da ese puntaje para confiar en el diagnóstico

| # | Criterio derivado del enunciado y del Excel de UH; por validar con el PO, ver FUENTES_CRITERIOS.md | Prueba (`tests/test_hu07_explicacion.py`) |
|---|---|---|
| CA1 | Dado un diagnóstico, entonces cada criterio de la rúbrica muestra su peso, los puntos obtenidos y la evidencia tomada de la HV. | `test_ca1_cada_criterio_muestra_peso_puntos_y_evidencia` |
| CA2 | La suma de los puntos por criterio explica el puntaje total. | `test_ca2_la_suma_de_lo_obtenido_explica_el_puntaje` |
| CA3 | Se muestra un resumen en lenguaje natural redactado por el agente. | `test_ca3_resumen_en_lenguaje_natural_generado_por_el_agente` |
| CA4 | El LLM no puede alterar el puntaje calculado por la rúbrica. | `test_ca4_el_llm_no_puede_cambiar_el_puntaje` |

## NF01: Como usuario quiero que el diagnóstico se entregue en menos de 30 segundos para no abandonar el proceso

| # | Criterio | Prueba (`tests/test_nf01_rendimiento.py`) |
|---|---|---|
| CA1 | El tiempo entre la solicitud y el diagnóstico no supera 30 s en el 90 % de los casos (se mide por nodo en `EjecucionAgente` y en total en `Diagnostico.duracion_ms`). | `test_ca1_se_mide_el_tiempo_por_nodo_con_latencia_simulada`, `test_ca1_diez_diagnosticos_en_menos_de_30_s_el_90_por_ciento` |
| CA2 | Si se supera, el sistema muestra un indicador de progreso y no bloquea la interfaz. | `test_ca2_indicador_de_progreso_sin_bloquear_la_interfaz`, `test_ca2_si_supera_30_s_avisa_que_sigue_trabajando` |

Medios implementados: ejecución en segundo plano (`core.servicios.tareas`), sondeo JSON cada 1,5 s, medición por
nodo y caché de respuestas del LLM (`LLM_CACHE=1`, `test_cache_del_llm_acelera_diagnosticos_repetidos`).
Pendiente: nodos en paralelo (el grafo actual es secuencial) y la medición con un LLM real (las pruebas usan el LLM
falso con latencia simulada; la prueba de "diez archivos" corre con el LLM falso).

## NF05: Como administrador quiero registro y trazabilidad de qué agente generó cada resultado para auditar errores

| # | Criterio derivado del enunciado y del Excel de UH; por validar con el PO, ver FUENTES_CRITERIOS.md | Prueba (`tests/test_nf05_trazabilidad.py`) |
|---|---|---|
| CA1 | Cada nodo ejecutado queda en `EjecucionAgente` con agente, tokens, duración, estado, hash de entrada y resumen sin datos personales. | `test_ca1_cada_ejecucion_registra_agente_tokens_y_duracion` |
| CA2 | La vista "Trazabilidad" lista las ejecuciones y permite filtrar por agente. | `test_ca2_la_vista_muestra_la_trazabilidad_y_filtra_por_agente` |
| CA3 | Cada candidato ve solo sus ejecuciones; un administrador (staff) ve todas. | `test_ca3_cada_usuario_solo_ve_sus_trazas_y_el_admin_ve_todas` |
