# Criterios de aceptación: Feature 5 `adaptacion_hv`

Rama `feature-5-adaptacion-de-hv-agente-redactor` · Capacidad: Adaptación de HV (agente Redactor) · Sprint 3.

| Ítem | SP propuestos | Fuente de criterios |
|---|---|---|
| HU12 Adaptar la HV a una vacante | 13 | derivado del enunciado de la issue; por validar con el PO |
| HU13 Ver original y adaptada lado a lado | 5 | derivado del enunciado de la issue; por validar con el PO |
| HU14 Aprobar o rechazar los cambios | 5 | derivado del enunciado de la issue; por validar con el PO |

Los SP son una propuesta del equipo: en el Sprint 3 no hubo ceremonia de planning poker.

Grafo, intención `adaptar_hv`: `control_cuota → supervisor → redactor → validador_redactor → END`.
El Redactor no reescribe la HV: propone cambios puntuales (orden de habilidades, orden de experiencia, frase en el
resumen y palabras clave) usando solo lo que ya está en la HV. El `ValidadorRedactor` (NF03) descarta elementos de
lista que no estén soportados por la HV y cualquier texto que agregue términos de la vacante o cifras ausentes de la HV.
La propuesta queda en `HVAdaptada` (campos cifrados, NF02); el `PerfilExtraido` original nunca se modifica.

## HU12: Como candidato quiero que el sistema adapte mi hoja de vida a una vacante específica para aumentar mis opciones

| # | Criterio | Prueba (`tests/test_hu12_adaptar.py`) |
|---|---|---|
| CA1 | «Adaptar HV» lista las vacantes de la BD con la acción «Adaptar mi HV» por registro. | `test_ca1_lista_de_vacantes_con_accion_adaptar` |
| CA2 | El Redactor propone cambios orientados a la vacante, cada uno con su motivo, sin agregar datos. | `test_ca2_el_redactor_propone_cambios_orientados_a_la_vacante` |
| CA3 | La propuesta queda pendiente y la HV original no cambia. | `test_ca3_la_propuesta_queda_pendiente_y_no_toca_la_hv_original` |
| CA4 | Queda trazado qué agentes generaron la propuesta (NF05). | `test_ca4_queda_trazado_que_agente_genero_la_propuesta` |
| CA5 | Sin HV analizada no se puede adaptar. | `test_ca5_sin_hv_analizada_no_se_puede_adaptar` |

## HU13: Como candidato quiero ver lado a lado la versión original y la adaptada para entender los cambios

| # | Criterio | Prueba (`tests/test_hu13_comparar.py`) |
|---|---|---|
| CA1 | Cada cambio se muestra en dos columnas (original y adaptada) que se apilan en el celular. | `test_ca1_cada_cambio_muestra_original_y_adaptada_en_dos_columnas` |
| CA2 | Lo nuevo se resalta y lo que cambió de posición se marca como «movido». | `test_ca2_lo_que_cambia_se_resalta` |
| CA3 | Cada cambio explica su motivo. | `test_ca3_cada_cambio_explica_el_motivo` |
| CA4 | Solo el dueño de la HV ve la comparación (404 para otros). | `test_ca4_solo_el_dueno_ve_la_comparacion` |

## HU14: Como candidato quiero aprobar o rechazar los cambios antes de que se apliquen para mantener el control

| # | Criterio | Prueba (`tests/test_hu14_aprobar.py`) |
|---|---|---|
| CA1 | Cada cambio tiene «Aprobar» y «Rechazar». | `test_ca1_cada_cambio_tiene_aprobar_y_rechazar` |
| CA2 | Solo se aplican los cambios aprobados. | `test_ca2_solo_se_aplican_los_cambios_aprobados` |
| CA3 | La HV original nunca se modifica. | `test_ca3_la_hv_original_nunca_se_modifica` |
| CA4 | Si falta decidir algún cambio, no se aplica nada. | `test_ca4_sin_decidir_todos_no_se_aplica_nada` |
| CA5 | Rechazar todo descarta la adaptación. | `test_ca5_rechazar_todo_descarta_la_adaptacion` |
| CA6 | Una adaptación decidida no se vuelve a decidir. | `test_ca6_una_vez_decidida_no_se_vuelve_a_decidir` |

Extra: la versión aplicada se descarga en Word y se puede enviar en la postulación (HU15).
NF03 para el Redactor: `tests/test_nf03_redactor.py`.
