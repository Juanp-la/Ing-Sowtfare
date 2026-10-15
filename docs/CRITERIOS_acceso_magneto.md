# Criterios de aceptación: Feature 1 `acceso_magneto`

Rama `feature-1-acceso-e-integracion-magneto` · Capacidad: Acceso e integración Magneto · Sube: Miguel.

| Ítem | SP | Responsable (Project) | Fuente de criterios |
|---|---|---|---|
| HU01 Iniciar sesión con cuenta Magneto | 8 | Miguel | Oficial (Entrega 1 §3.4) |
| NF04 Límite de consumo LLM por usuario | 3 | Miguel | derivado del enunciado y del Excel de UH; por validar con el PO, ver FUENTES_CRITERIOS.md del Excel: "Cuota de tokens por usuario antes de invocar el grafo" |

## HU01: Como candidato quiero iniciar sesión con mi cuenta de Magneto para acceder al copiloto sin crear otro usuario

| # | Criterio (Dado / Cuando / Entonces) | Prueba |
|---|---|---|
| CA1 | Dado un visitante sin sesión activa, cuando entra a cualquier página del copiloto, entonces es redirigido al inicio de sesión de Magneto. | `test_ca1_sin_sesion_redirige_al_inicio_de_sesion_de_magneto` |
| CA2 | Dado un candidato en el inicio de sesión, cuando envía credenciales inválidas, entonces ve «Usuario o contraseña incorrectos» y el correo digitado se conserva. | `test_ca2_credenciales_invalidas_muestran_mensaje_y_conservan_el_correo`, `test_ca2_correo_inexistente_o_vacio_da_el_mismo_mensaje` |
| CA3 | Dado un candidato con credenciales válidas de Magneto, cuando inicia sesión, entonces el copiloto muestra su nombre. | `test_ca3_con_sesion_valida_el_copiloto_muestra_el_nombre_del_candidato` |
| CA4 (derivado) | Dado un candidato de Magneto que nunca entró, cuando inicia sesión, entonces se vincula por `magneto_id` sin crear un segundo usuario ni pedir otra clave. | `test_ingreso_no_crea_otro_usuario_y_vincula_por_magneto_id` |

Implementación: `MagnetoClient` (interfaz, patrón Adapter) y `MagnetoMockClient` (simulado, sin red). El directorio
simulado son las cuentas sintéticas con `magneto_id` que crea `manage.py seed_demo` (clave aleatoria impresa en
consola). La feature declara `url_login`, así el login mínimo del núcleo delega en ella.

## NF04: Como administrador quiero un límite de consumo por usuario para controlar el costo de las llamadas al LLM

| # | Criterio derivado del enunciado y del Excel de UH; por validar con el PO, ver FUENTES_CRITERIOS.md | Prueba |
|---|---|---|
| CA1 | Dado un candidato con sesión, cuando abre "Mi consumo" o mira la barra superior, entonces ve los tokens usados en el mes frente a su cuota (y un estado vacío si no ha usado agentes). | `test_ca1_el_panel_muestra_el_consumo_del_mes`, `test_ca1_indicador_de_cuota_visible_en_la_barra`, `test_ca1_estado_vacio_sin_consumo` |
| CA2 | Dado un candidato con cuota disponible, cuando una vista invoca el grafo, entonces la cuota se verifica antes y el consumo queda registrado. | `test_ca2_la_cuota_se_verifica_antes_de_invocar_el_grafo` |
| CA3 | Dado un candidato con la cuota agotada, cuando intenta usar un agente, entonces el grafo no se invoca y ve el aviso de cuota agotada (HTTP 429). | `test_ca3_al_agotarse_la_cuota_se_bloquean_los_agentes` |

La verificación vive en el núcleo (`ControlCuota`, nodo `control_cuota` del grafo y `CopilotoService`); esta
feature aporta el panel, el indicador y las pruebas extremo a extremo. La cuota por usuario se edita en el admin.

## Fuera de alcance (Sprint 3 o posterior)
HU04 (usar la HV del perfil Magneto) y cliente real de Magneto: no se construyen.
