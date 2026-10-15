# Criterios de aceptación: Feature 2 `analisis_hv`

Rama `feature-2-analisis-de-hv-agente-extractor` · Capacidad: Análisis de HV (agente Extractor) · Sube: Juan Pablo.

| Ítem | SP | Responsable (Project) | Fuente de criterios |
|---|---|---|---|
| HU02 Cargar HV en PDF o Word | 5 | David | Oficial (Entrega 1 §3.4) |
| HU03 Ver y corregir datos extraídos | 5 | Juan Pablo | Oficial (Entrega 1 §3.4) |
| NF02 Datos cifrados y borrables | 5 | Miguel | derivado del enunciado y del Excel de UH; por validar con el PO, ver FUENTES_CRITERIOS.md del Excel: "cifrado de campos sensibles y borrado a solicitud" |
| NF03 No inventar experiencia | 8 | Juan Pablo | derivado del enunciado y del Excel de UH; por validar con el PO, ver FUENTES_CRITERIOS.md del Excel: "nodo validador compara salida vs HV original" |

Flujo: `Mis hojas de vida` (lista) → `Cargar nueva HV` (HU02) → detalle con nombre y botón **Analizar** →
grafo `extraer_perfil`: `control_cuota → supervisor → extractor → validador_extractor` → perfil editable (HU03).

## HU02: Como candidato quiero cargar mi hoja de vida en PDF o Word para que el sistema la analice

| # | Criterio | Prueba (`tests/test_hu02_carga.py`) |
|---|---|---|
| CA1 | El sistema acepta archivos .pdf y .docx de máximo 5 MB. | `test_ca1_acepta_pdf_y_docx_de_maximo_5_mb` |
| CA2 | Si el archivo excede el tamaño o tiene otra extensión, muestra «Formato no admitido: cargue un PDF o Word de máximo 5 MB» y conserva la pantalla de carga. | `test_ca2_otra_extension_...`, `test_ca2_archivo_de_mas_de_5_mb_...`, `test_ca2_envio_sin_archivo_...` |
| CA3 | Al cargar correctamente, muestra el nombre del archivo y habilita el botón Analizar. | `test_ca3_al_cargar_muestra_el_nombre_y_habilita_analizar` |

Además de la extensión y el tamaño se valida la firma real del archivo (`%PDF-`, ZIP con `word/document.xml`).
PDF con PyMuPDF y Word con python-docx (`ExtractorTexto`, patrón Strategy). HV escaneadas: fuera de alcance (sin OCR);
se informa «No fue posible leer el archivo, intente con otro formato».

## HU03: Como candidato quiero ver los datos que el sistema extrajo de mi hoja de vida para confirmarlos o corregirlos

| # | Criterio | Prueba (`tests/test_hu03_perfil.py`) |
|---|---|---|
| CA1 | Tras el análisis, el sistema muestra los campos extraídos (contacto, experiencia, educación, habilidades). | `test_ca1_tras_el_analisis_muestra_los_campos_extraidos` |
| CA2 | Todo campo vacío se resalta y el usuario puede editarlo. | `test_ca2_todo_campo_vacio_se_resalta_y_es_editable` |
| CA3 | Los cambios se guardan solo cuando el usuario confirma. | `test_ca3_los_cambios_se_guardan_solo_al_confirmar`, `test_formulario_invalido_no_guarda` |

## NF02: Como usuario quiero que mis datos personales se almacenen cifrados y se puedan eliminar a solicitud

| # | Criterio derivado del enunciado y del Excel de UH; por validar con el PO, ver FUENTES_CRITERIOS.md | Prueba (`tests/test_nf02_privacidad.py`) |
|---|---|---|
| CA1 | Dado que cargo y analizo mi HV, entonces el texto, el nombre del archivo y el perfil quedan cifrados en BD (Fernet) y el archivo cifrado en disco con nombre aleatorio. | `test_ca1_datos_personales_cifrados_en_bd_y_en_disco` |
| CA2 | Dado que elimino una HV desde la lista y confirmo, entonces se borran el archivo, el texto, el perfil y todo lo derivado; la traza de agentes queda sin vínculo ni datos personales (para no perder el consumo de cuota). | `test_ca2_eliminar_hv_borra_todos_sus_datos_desde_la_lista` |
| CA3 | Ningún usuario puede ver ni borrar la HV de otro (HTTP 404). | `test_ca3_nadie_puede_ver_ni_borrar_la_hv_de_otro` |

Clave por variable de entorno `CAMPOS_CIFRADO_KEY` (en desarrollo, clave efímera con aviso `core.W001`).

## NF03: Como usuario quiero que el sistema nunca agregue experiencia que yo no declaré en mi hoja de vida

| # | Criterio derivado del enunciado y del Excel de UH; por validar con el PO, ver FUENTES_CRITERIOS.md | Prueba (`tests/test_nf03_veracidad.py`) |
|---|---|---|
| CA1 | Dado que el LLM devuelve un cargo, empresa o habilidad que no está en la HV, cuando el validador compara contra el texto original, entonces el dato se descarta, el candidato es avisado y queda traza del nodo validador. | `test_ca1_dato_inventado_por_el_llm_es_rechazado` |
| CA2 | Dado un perfil fiel a la HV, entonces pasa completo y la traza muestra `supervisor → extractor → validador_extractor`. | `test_ca2_sin_datos_inventados_el_perfil_pasa_completo` |

Regla del `ValidadorVeracidad` (núcleo): un valor se acepta si aparece literal (normalizado) en la HV o si al menos el
80 % de sus palabras significativas están en ella y todos sus números también; si una entrada de experiencia o
educación tiene algún dato no soportado, se descarta completa.

## Fuera de alcance
OCR de HV escaneadas; HU04 (HV del perfil Magneto) y Redactor/HU12-HU14 (Sprint 3).
