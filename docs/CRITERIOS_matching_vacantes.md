# Criterios de aceptación: Feature 4 `matching_vacantes`

Rama `feature-4-matching-de-vacantes-agente-matcher` · Capacidad: Matching de vacantes (agente Matcher) · Sube: Miguel.

| Ítem | SP | Responsable (Project) | Fuente de criterios |
|---|---|---|---|
| HU08 Vacantes ordenadas por ajuste | 13 | Miguel | derivado del enunciado y del Excel de UH; por validar con el PO, ver FUENTES_CRITERIOS.md del Excel: "ranking perfil-vacante (embeddings + reglas). Vacantes de prueba en BD" |
| HU09 Filtrar vacantes (ciudad, modalidad, salario) | 3 | Miguel | derivado del enunciado y del Excel de UH; por validar con el PO, ver FUENTES_CRITERIOS.md del Excel: "filtro sobre la lista de vacantes (consulta a BD)" |
| HU10 Requisitos que cumplo y no cumplo | 8 | David | derivado del enunciado y del Excel de UH; por validar con el PO, ver FUENTES_CRITERIOS.md del Excel: "brechas requisito por requisito para una vacante" |
| NF06 Uso desde el celular | 3 | David | derivado del enunciado y del Excel de UH; por validar con el PO, ver FUENTES_CRITERIOS.md del Excel: "interfaz responsive (Bootstrap)" |

Grafo, intención `buscar_vacantes`: `control_cuota → supervisor → matcher → END`.
Ajuste = 70 % reglas (cada requisito evaluado con `core.dominio.requisitos`; los obligatorios pesan doble) + 30 %
similitud local de texto con un `Embedder` inyectable (`EmbedderBolsaPalabras` por defecto, sin red; se reemplaza con
`MATCHER_EMBEDDER = "ruta.a.MiEmbedder"` en settings). El ajuste se guarda en `AjusteVacante` y solo se recalcula si
cambia el perfil, si hay vacantes nuevas o si el candidato pulsa «Recalcular ajuste».

Demo con el PO (Sección 6 del informe): lista desde la tabla `Vacante` ordenada por ajuste con el botón
**Ver ajuste** en cada registro, que abre los requisitos que cumple y no cumple.

## HU08: Como candidato quiero ver vacantes de Magneto ordenadas por nivel de ajuste con mi perfil

| # | Criterio derivado del enunciado y del Excel de UH; por validar con el PO, ver FUENTES_CRITERIOS.md | Prueba (`tests/test_hu08_ranking.py`) |
|---|---|---|
| CA1 | Dado un perfil analizado, cuando abro "Vacantes", entonces veo las vacantes activas de la BD ordenadas de mayor a menor ajuste (%), y la primera es la que mejor cumple. | `test_ca1_lista_desde_bd_ordenada_por_ajuste`, `test_vacantes_inactivas_no_aparecen` |
| CA2 | Cada vacante de la lista tiene un botón «Ver ajuste». | `test_ca2_cada_vacante_tiene_el_boton_ver_ajuste` |
| CA3 | Sin HV analizada se muestra un estado vacío; si el perfil cambia, el ajuste se recalcula. | `test_ca3_sin_hv_analizada_muestra_estado_vacio`, `test_ca3_el_ajuste_se_recalcula_cuando_cambia_el_perfil` |
| CA4 | El Matcher combina reglas y similitud local con un Embedder inyectable. | `test_ca4_matcher_combina_reglas_y_similitud_con_embedder_inyectable` |

## HU09: Como candidato quiero filtrar las vacantes por ciudad, modalidad y salario para enfocar mi búsqueda

| # | Criterio derivado del enunciado y del Excel de UH; por validar con el PO, ver FUENTES_CRITERIOS.md | Prueba (`tests/test_hu09_filtros.py`) |
|---|---|---|
| CA1 | Al elegir una ciudad solo se muestran vacantes de esa ciudad. | `test_ca1_filtra_por_ciudad` |
| CA2 | Al elegir una modalidad (presencial, remoto, híbrido) solo se muestran esas. | `test_ca2_filtra_por_modalidad` |
| CA3 | Con un rango salarial se muestran las vacantes cuyo rango se cruza con el pedido. | `test_ca3_filtra_por_rango_salarial` |
| CA4 | Los filtros se combinan y la lista conserva el orden por ajuste. | `test_ca4_filtros_combinados_mantienen_el_orden_por_ajuste` |
| CA5 | Si no hay resultados se muestra «No hay vacantes con esos filtros.». | `test_ca5_sin_resultados_muestra_mensaje` |
| CA6 | Un rango salarial invertido muestra un error y no se aplica. | `test_ca6_rango_salarial_invertido_muestra_error_y_no_filtra` |

## HU10: Como candidato quiero ver qué requisitos cumplo y cuáles no en una vacante para decidir si me postulo

| # | Criterio derivado del enunciado y del Excel de UH; por validar con el PO, ver FUENTES_CRITERIOS.md | Prueba (`tests/test_hu10_requisitos.py`) |
|---|---|---|
| CA1 | El detalle muestra, requisito por requisito, si lo cumplo o no y la evidencia tomada de mi HV. | `test_ca1_detalle_requisito_por_requisito_con_evidencia` |
| CA2 | Se resume cuántos requisitos cumplo y se marcan los obligatorios. | `test_ca2_resumen_y_marcas_de_obligatorio` |
| CA3 | Si cumplo todo, se indica explícitamente. | `test_ca3_cumple_todo` |
| CA4 | Una vacante inexistente o cerrada responde 404. | `test_ca4_vacante_inexistente_o_cerrada_da_404` |
| CA5 | Sin HV analizada se invita a cargarla. | `test_ca5_sin_hv_invita_a_cargarla` |

## NF06: Como usuario quiero usar el copiloto desde el celular con la misma funcionalidad que en el computador

| # | Criterio derivado del enunciado y del Excel de UH; por validar con el PO, ver FUENTES_CRITERIOS.md | Prueba (`tests/test_nf06_responsive.py`) |
|---|---|---|
| CA1 | `base.html` declara viewport, carga Bootstrap 5 y tiene menú colapsable. | `test_ca1_base_tiene_viewport_bootstrap_y_menu_colapsable` |
| CA2 | Toda tabla de cualquier plantilla está en `table-responsive` y se apila como tarjetas en celular (`tabla-apilable` + `data-etiqueta`). | `test_ca2_toda_tabla_es_desplazable_o_apilable_en_celular` |
| CA3 | Toda plantilla de feature extiende `base.html` y no usa anchos fijos en píxeles. | `test_ca3_las_plantillas_de_feature_extienden_base_y_usan_rejilla_fluida` |
| CA4 | El CSS apila las tablas por debajo de 576 px. | `test_ca4_css_apila_tablas_en_pantallas_pequenas` |
| CA5 | Las vistas de vacantes usan la rejilla responsiva (filtros en columna en celular). | `test_ca5_vistas_de_vacantes_se_renderizan_con_clases_responsivas` |

Las pruebas de CA2 y CA3 recorren todas las plantillas presentes, así que al integrar en `Sprint-2` también verifican
las de las demás features. Pendiente: prueba visual en un navegador real de celular.
