# Criterios de aceptación: Feature 6 `postulaciones`

Rama `feature-6-postulacion-y-seguimiento` · Capacidad: Postulación y seguimiento · Sprint 3.

| Ítem | SP propuestos | Fuente de criterios |
|---|---|---|
| HU15 Postularme desde el copiloto | 8 | derivado del enunciado de la issue; por validar con el PO |
| HU18 Consultar el estado de mis postulaciones | 5 | derivado del enunciado de la issue; por validar con el PO |

La postulación se envía con `MagnetoClient.postular(...)` (simulado). El ajuste que queda guardado lo calcula el
agente Matcher (intención `buscar_vacantes`) sobre la HV que se envía, original o adaptada.

## HU15: Como candidato quiero postularme a la vacante desde el copiloto para no repetir el proceso en la plataforma

| # | Criterio | Prueba (`tests/test_hu15_postular.py`) |
|---|---|---|
| CA1 | El detalle de la vacante tiene el botón «Postularme». | `test_ca1_desde_el_detalle_de_la_vacante_puedo_postularme` |
| CA2 | Confirmo la HV y la postulación llega a Magneto; queda «Enviada» con su código, ajuste y requisitos. | `test_ca2_confirmo_y_la_postulacion_llega_a_magneto` |
| CA3 | No puedo postularme dos veces a la misma vacante. | `test_ca3_no_me_puedo_postular_dos_veces` |
| CA4 | Puedo enviar la versión adaptada (HU14), que aparece como recomendada. | `test_ca4_puedo_enviar_la_version_adaptada` |
| CA5 | Si Magneto falla, se informa y no queda registrada. | `test_ca5_si_magneto_falla_no_queda_registrada` |
| CA6 | Sin HV analizada no puedo postularme. | `test_ca6_sin_hv_analizada_no_puedo_postularme` |

## HU18: Como candidato quiero consultar el estado de mis postulaciones para hacer seguimiento

| # | Criterio | Prueba (`tests/test_hu18_seguimiento.py`) |
|---|---|---|
| CA1 | Veo mis postulaciones con su estado y un resumen por estado. | `test_ca1_veo_la_lista_de_mis_postulaciones_con_su_estado` |
| CA2 | Puedo filtrar por estado. | `test_ca2_puedo_filtrar_por_estado` |
| CA3 | El detalle muestra el seguimiento y la retroalimentación del reclutador (HU20). | `test_ca3_el_detalle_muestra_el_seguimiento_y_la_retroalimentacion` |
| CA4 | Puedo retirar una postulación abierta. | `test_ca4_puedo_retirar_una_postulacion_abierta` |
| CA5 | No puedo retirar una postulación ya decidida. | `test_ca5_no_se_retira_una_postulacion_ya_decidida` |
| CA6 | Solo veo mis postulaciones. | `test_ca6_solo_veo_mis_postulaciones` |
