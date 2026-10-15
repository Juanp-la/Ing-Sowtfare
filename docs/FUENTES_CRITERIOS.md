<!-- fuentes-criterios-v1 -->
# Fuentes de los criterios de aceptación

Este documento dice de dónde sale cada criterio de aceptación del Sprint 2 y cuáles son oficiales.

Fuentes consultadas:
1. Enunciado de la historia en la issue de GitHub (repositorio Juanp-la/Ing-Sowtfare). El cuerpo de las issues está vacío: solo existe el enunciado.
2. Comentario de la fila de cada ítem en el Excel `Los Troyanos - UHs - Entrega 2`.
3. Informe de la Entrega 1, sección 3.4 (Sprint Backlog), donde están las condiciones de aceptación oficiales.
4. Informe de la Entrega 2 (borrador): sección de arquitectura y tabla de supuestos del Excel.

## Criterios oficiales (Entrega 1, sección 3.4)

| ID | Issue | Fuente |
|---|---|---|
| HU01 | #1 | Entrega 1, sección 3.4 |
| HU02 | #2 | Entrega 1, sección 3.4 |
| HU03 | #3 | Entrega 1, sección 3.4 |
| HU05 | #5 | Entrega 1, sección 3.4 |
| HU06 | #6 | Entrega 1, sección 3.4 |
| NF01 | #21 | Entrega 1, sección 3.4 |

## Ítems sin criterios oficiales

Para estos 11 ítems no existen condiciones de aceptación en la Entrega 1 ni en las issues. Los criterios Dado/Cuando/Entonces de cada `docs/CRITERIOS_<app>.md` se redactaron a partir del enunciado y del comentario del Excel que aparecen abajo, y quedan pendientes de validación por el Product Owner.

| ID | Issue | Enunciado (issue) | Comentario (Excel) |
|---|---|---|---|
| HU07 | #7 | Como candidato quiero ver por qué el sistema me da ese puntaje para confiar en el diagnóstico. | Explicabilidad: cada criterio de la rúbrica con su peso y evidencia |
| HU08 | #8 | Como candidato quiero ver vacantes de Magneto ordenadas por nivel de ajuste con mi perfil. | Ranking perfil-vacante (embeddings + reglas). Vacantes de prueba en BD |
| HU09 | #9 | Como candidato quiero filtrar las vacantes por ciudad, modalidad y salario para enfocar mi búsqueda. | Filtro sobre la lista de vacantes (consulta a BD) |
| HU10 | #10 | Como candidato quiero ver qué requisitos cumplo y cuáles no en una vacante para decidir si me postulo. | Brechas requisito por requisito para una vacante |
| HU16 | #16 | Como candidato quiero recibir preguntas probables de entrevista para prepararme. | Generadas a partir de la vacante y las brechas |
| HU17 | #17 | Como candidato quiero un plan de mejora con acciones concretas para cerrar mis brechas. | Acciones concretas por cada brecha detectada |
| NF02 | #22 | Como usuario quiero que mis datos personales se almacenen cifrados y se puedan eliminar a solicitud. | Seguridad/privacidad: cifrado de campos sensibles y borrado a solicitud |
| NF03 | #23 | Como usuario quiero que el sistema nunca agregue experiencia que yo no declaré en mi hoja de vida. | Guardrail: nodo validador compara salida vs HV original |
| NF04 | #24 | Como administrador quiero un límite de consumo por usuario para controlar el costo de las llamadas al LLM. | Cuota de tokens por usuario antes de invocar el grafo |
| NF05 | #25 | Como administrador quiero registro y trazabilidad de qué agente generó cada resultado para auditar errores. | Registro de cada ejecución de agente (tabla EjecucionAgente) |
| NF06 | #26 | Como usuario quiero usar el copiloto desde el celular con la misma funcionalidad que en el computador. | Interfaz responsive (Bootstrap) |

## Contexto adicional del informe y del Excel

| Tema | Fuente | Qué dice |
|---|---|---|
| NF02 | Informe Entrega 2, arquitectura | Seguridad: llaves en variables de entorno, cifrado de datos personales y borrado a solicitud |
| NF04 y NF05 | Informe Entrega 2, arquitectura | Trazabilidad de cada ejecución de agente y cuota de tokens por usuario |
| NF06 | Informe Entrega 2, arquitectura | Aplicación web responsive, usable desde computador y celular |
| Magneto simulado | Excel, supuestos 3 y 4 | No hay API real de Magneto: adaptador simulado con la misma interfaz; vacantes como datos de prueba en la base de datos |
| LLM | Excel, supuesto 5 | Proveedor comercial vía LangChain con modelo rápido para NF01; costo controlado con NF04 |
| Alcance de HV | Excel, supuesto 6 | PDF con texto seleccionable o Word; HV escaneadas fuera de alcance (sin OCR) |
