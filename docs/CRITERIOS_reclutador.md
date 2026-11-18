# Criterios de aceptación: Feature 8 `reclutador`

Rama `feature-8-modulo-reclutador` · Capacidad: Módulo reclutador · Sprint 3.

| Ítem | SP propuestos | Fuente de criterios |
|---|---|---|
| HU19 Candidatos ordenados por ajuste | 8 | derivado del enunciado de la issue; por validar con el PO |
| HU20 Marcar apto / no apto con retroalimentación | 8 | derivado del enunciado de la issue; por validar con el PO |

Acceso solo para usuarios con rol `reclutador` (o `admin`): un candidato recibe 403 y no ve el menú.
Cada reclutador ve las vacantes que tiene asignadas (`Vacante.reclutador`).

## HU19: Como reclutador quiero ver los candidatos postulados ordenados por ajuste para priorizar mi revisión

| # | Criterio | Prueba (`tests/test_hu19_candidatos.py`) |
|---|---|---|
| CA1 | Veo mis vacantes con el número de postulados y cuántos faltan por revisar. | `test_ca1_veo_mis_vacantes_con_el_numero_de_postulados` |
| CA2 | Los candidatos aparecen del mayor al menor ajuste. | `test_ca2_los_candidatos_aparecen_del_mayor_al_menor_ajuste` |
| CA3 | Cada candidato muestra ajuste, requisitos cumplidos y la acción «Evaluar». | `test_ca3_cada_candidato_muestra_ajuste_requisitos_y_accion_evaluar` |
| CA4 | Puedo filtrar candidatos por estado. | `test_ca4_puedo_filtrar_candidatos_por_estado` |
| CA5 | Un candidato no entra al módulo. | `test_ca5_un_candidato_no_entra_al_modulo_reclutador` |
| CA6 | No veo vacantes de otro reclutador. | `test_ca6_no_veo_vacantes_de_otro_reclutador` |

## HU20: Como reclutador quiero marcar a un candidato como apto o no apto y que esa decisión alimente su retroalimentación

| # | Criterio | Prueba (`tests/test_hu20_decision.py`) |
|---|---|---|
| CA1 | Al abrir la postulación, el candidato la ve «En revisión». | `test_ca1_al_abrir_la_postulacion_el_candidato_la_ve_en_revision` |
| CA2 | «No apto» exige un comentario. | `test_ca2_marcar_no_apto_exige_comentario` |
| CA3 | «No apto» genera una sugerencia por cada requisito no cumplido (obligatorios primero). | `test_ca3_no_apto_genera_retroalimentacion_por_cada_requisito_no_cumplido` |
| CA4 | El candidato ve la decisión, el comentario y las sugerencias en su seguimiento (HU18). | `test_ca4_el_candidato_ve_la_decision_en_su_seguimiento` |
| CA5 | «Apto» resalta los requisitos obligatorios que cumplió. | `test_ca5_apto_resalta_los_puntos_fuertes` |
| CA6 | La decisión se puede corregir. | `test_ca6_la_decision_se_puede_corregir` |
| CA7 | Un candidato no puede decidir. | `test_ca7_un_candidato_no_puede_decidir` |
