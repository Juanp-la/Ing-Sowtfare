# Magneto Copiloto

Copiloto de empleabilidad con agentes especializados (LangGraph) para la plataforma de empleo Magneto.
Proyecto del equipo **Los Troyanos** para el curso de Ingeniería de Software de la Universidad EAFIT.

## Tabla de contenido

1. [Descripción](#1-descripción)
2. [Estructura del repositorio y ramas](#2-estructura-del-repositorio-y-ramas)
3. [Entornos de ejecución recomendables](#3-entornos-de-ejecución-recomendables)
4. [Cómo ejecutar](#4-cómo-ejecutar)
5. [Pruebas](#5-pruebas)
6. [Gestión del proyecto](#6-gestión-del-proyecto)
7. [Autores](#7-autores)
8. [Contenido del curso](#8-contenido-del-curso)

## 1. Descripción

### 1.1 Contexto
Magneto es una plataforma colombiana de empleo que conecta a personas que buscan trabajo con las vacantes que publican
empresas de múltiples sectores. El reto **Profile Manager** (Retos 2026-2) propone, en su **Idea 2**, una arquitectura
agéntica con LangGraph: agentes especializados que estructuran el perfil, procesan vacantes y dejan trazabilidad de
lo que hizo cada agente.

### 1.2 Problema
- La hoja de vida (HV) suele estar desactualizada, mal estructurada o escrita como lista de funciones y no de logros.
- El candidato no sabe qué tan cerca está de una vacante ni qué le falta, así que se postula con la misma HV a ofertas distintas.
- Cuando lo descartan no recibe retroalimentación accionable, y el reclutador recibe muchos perfiles poco alineados.

### 1.3 Solución propuesta
Un asistente web que acompaña al candidato desde que carga su HV hasta que se prepara para una vacante. Un agente
**Supervisor** decide qué agentes intervienen según la acción pedida, sobre un grafo de LangGraph con estado compartido:

| Agente | Responsabilidad en el MVP |
|---|---|
| Supervisor | Enruta por intención (`extraer_perfil`, `diagnosticar`, `buscar_vacantes`, `preparar`) después del control de cuota |
| Extractor | Convierte la HV (PDF o Word) en un perfil estructurado; un validador de veracidad descarta datos que no estén en la HV |
| Evaluador | Puntaje 0-100 con rúbrica, hallazgos priorizados y explicación por criterio |
| Matcher | Ordena las vacantes por ajuste y explica requisito por requisito qué se cumple y qué no |
| Coach | Preguntas probables de entrevista y plan de mejora por brecha |

**Visión (Entrega 1):** para las personas que buscan empleo en Colombia y se postulan con una HV genérica sin saber qué
tan cerca están de la vacante, Magneto Copiloto diagnostica la HV, la compara con las vacantes reales de Magneto, en
español, y le devuelve al candidato retroalimentación sobre su proceso.

**Grupo objetivo:** jóvenes que buscan su primer empleo, perfiles técnicos y operativos en convocatorias masivas y
profesionales en transición de sector. Usuario secundario: el reclutador de la empresa cliente.

### 1.4 Alcance del MVP (Sprint 2)
17 ítems, 102 story points (61 % de los 167 SP del backlog):

| Feature | UH | NFR |
|---|---|---|
| F1 Acceso e integración Magneto | HU01 Iniciar sesión con cuenta Magneto | NF04 Límite de consumo LLM por usuario |
| F2 Análisis de HV (agente Extractor) | HU02 Cargar HV en PDF o Word, HU03 Ver y corregir datos extraídos | NF02 Datos cifrados y borrables, NF03 No inventar experiencia |
| F3 Diagnóstico de HV (agente Evaluador) | HU05 Puntaje, HU06 Hallazgos priorizados, HU07 Explicación del puntaje | NF01 Diagnóstico en menos de 30 s, NF05 Trazabilidad por agente |
| F4 Matching de vacantes (agente Matcher) | HU08 Vacantes por ajuste, HU09 Filtros, HU10 Requisitos que cumplo y no cumplo | NF06 Uso desde el celular |
| F7 Preparación (agente Coach) | HU16 Preguntas de entrevista, HU17 Plan de mejora | (ninguno) |

En el Sprint 2 Magneto se simula con un adaptador (mock) y el LLM es falso y determinista por defecto.

### 1.5 Fuera de alcance (Sprint 3)
Features 5 (Adaptación de HV, agente Redactor), 6 (Postulación y seguimiento) y 8 (Módulo reclutador):
HU04, HU11, HU12, HU13, HU14, HU15, HU18, HU19 y HU20 (65 SP). Tampoco hay OCR para HV escaneadas.

## 2. Estructura del repositorio y ramas

### 2.1 Modelo de ramas

```
main
 ├── Sprint-1
 ├── Sprint-2
 │    ├── feature-1-acceso-e-integracion-magneto
 │    ├── feature-2-analisis-de-hv-agente-extractor
 │    ├── feature-3-diagnostico-de-hv-agente-evaluador
 │    ├── feature-4-matching-de-vacantes-agente-matcher
 │    ├── feature-7-preparacion-agente-coach
 │    └── ajuste-ui-ux-sprint2
 └── Sprint-3
```

Regla de Pull Request: **Feature → Sprint-N → main**. Cada Feature se integra a su rama de sprint con un PR revisado;
al cerrar el sprint, `Sprint-N` entra a `main` con otro PR. En `origin` existen hoy `main`, `Sprint-2` y las 5 ramas
de feature (ya mergeadas en `Sprint-2` con los PR #42 a #46). `Sprint-1` y `Sprint-3` son parte del modelo: Pendiente
de crear en el remoto.

### 2.2 Qué vive en cada rama
- **`main`:** el producto entregable: `backend/`, `frontend/`, `docs/`, `docker-compose.yml`, `.env.example` y este `README.md`.
  El código llega a `main` con el PR `Sprint-2` → `main`; hoy `main` solo contiene `README.md` y `poc_magneto.py` (PoC de la Entrega 1).
- **`Sprint-N`:** el código integrado del sprint más sus entregables y recursos, por ejemplo `Diagramas/`
  (clases, componentes, despliegue y entidad-relación) en `Sprint-2`.
- **`feature-<n>-<descripcion>`:** una Feature con sus UH y NFR.

### 2.3 Árbol real (rama `Sprint-2` con el ajuste de UI)

```
backend/
  manage.py  requirements.txt  Dockerfile  pytest.ini  .coveragerc  conftest.py
  config/            settings (descubre las features), urls (las monta), wsgi, asgi
  core/              núcleo compartido
    models.py        modelos y migración única 0001_initial
    agentes/         AgenteBase, EstadoCopiloto, Supervisor, ValidadorVeracidad, Trazador, registro, GrafoCopiloto
    llm/             LLMClient, MockLLMClient, adaptador LangChain (apagado), caché, esquemas Pydantic
    servicios/       CopilotoService (fachada), ControlCuota, cifrado Fernet, archivos, tareas en segundo plano
    dominio/         comparación requisito por requisito y normalización de texto
    management/      comando seed_demo
    pruebas/         factories reutilizables
  apps/
    acceso_magneto/     F1: MagnetoClient + MagnetoMockClient, login, panel de cuota
    analisis_hv/        F2: ExtractorTexto (PDF/Word), agente Extractor, perfil editable, borrado
    diagnostico_hv/     F3: rúbrica, agente Evaluador, progreso, trazabilidad
    matching_vacantes/  F4: Embedder local, agente Matcher, filtros, detalle de ajuste
    preparacion/        F7: agente Coach, preguntas y plan de mejora
frontend/
  templates/  base.html, partials/, 403.html, 404.html, 500.html, core/ y una carpeta por feature
  static/     css/app.css, js/app.js, img/brand/ (logos), vendor/bootstrap@5.3.3/, y estáticos por feature
docs/
  GUIA_NUEVA_FEATURE.md, GUIA_UI.md, FUENTES_CRITERIOS.md, CRITERIOS_<app>.md (uno por feature)
```

### 2.4 Cómo se agrega una Feature
Resumen de `docs/GUIA_NUEVA_FEATURE.md`: una Feature nueva es una carpeta `backend/apps/<app>/` con su `apps.py`.
`config/settings.py` la instala sola, `config/urls.py` la monta con el `prefijo_url` de su AppConfig y el menú de
`base.html` se arma con su atributo `menu`. Sus nodos de LangGraph se registran en `apps/<app>/agentes.py` con
`registrar_nodo(...)`. Sus Django Templates van en `frontend/templates/<app>/` y sus criterios en `docs/CRITERIOS_<app>.md`.
No se editan archivos compartidos; los modelos compartidos viven en `core`.

### 2.5 Feature, rama, UH/NFR y responsables (GitHub Project, 14 de octubre de 2026)

| Feature | Rama | UH / NFR | Responsables |
|---|---|---|---|
| F1 | `feature-1-acceso-e-integracion-magneto` | HU01, NF04 | Miguel Angel Colorado Castaño |
| F2 | `feature-2-analisis-de-hv-agente-extractor` | HU02, HU03, NF02, NF03 | David Santiago Duarte Niño (HU02), Juan Pablo Lopera Arrazola (HU03, NF03), Miguel Angel Colorado Castaño (NF02) |
| F3 | `feature-3-diagnostico-de-hv-agente-evaluador` | HU05, HU06, HU07, NF01, NF05 | Juan Pablo Lopera Arrazola (HU05, HU06, NF01), David Santiago Duarte Niño (HU07), Miguel Angel Colorado Castaño (NF05) |
| F4 | `feature-4-matching-de-vacantes-agente-matcher` | HU08, HU09, HU10, NF06 | Miguel Angel Colorado Castaño (HU08, HU09), David Santiago Duarte Niño (HU10, NF06) |
| F7 | `feature-7-preparacion-agente-coach` | HU16, HU17 | David Santiago Duarte Niño |

## 3. Entornos de ejecución recomendables

| Elemento | Recomendación | Fuente verificable |
|---|---|---|
| Sistema operativo | Windows 10/11 con Git Bash o WSL2, macOS o Ubuntu | Desarrollo hecho en Windows 11 con Git Bash |
| Python | 3.11 o superior; desarrollo y pruebas con **3.12.4** (el informe declara 3.12) | `backend/Dockerfile` usa `python:3.12-slim` |
| Gestor de paquetes | `pip` con `venv` fuera del repositorio | `backend/requirements.txt` |
| Base de datos | SQLite en desarrollo (por defecto); PostgreSQL 16 en contenedor | `config/settings.py`, `docker-compose.yml` (`postgres:16-alpine`) |
| Contenedores (opcional) | Docker Desktop con Docker Compose | `docker-compose.yml`, `backend/Dockerfile` |
| Navegador | Cualquier navegador moderno, también desde el celular | Bootstrap 5.3.3 vendorizado |
| RAM y disco | No medidos | Pendiente |

Dependencias principales (`backend/requirements.txt`): Django 5.1, LangGraph 1.2 (trae langchain-core), Pydantic 2,
cryptography (Fernet), PyMuPDF, python-docx, dj-database-url, psycopg 3, gunicorn, pytest, pytest-django y pytest-cov.

## 4. Cómo ejecutar

### 4.1 Requisitos y clonado

```bash
git clone https://github.com/Juanp-la/Ing-Sowtfare.git
cd Ing-Sowtfare
```

### 4.2 Entorno virtual
Git Bash, macOS o Linux:

```bash
python -m venv ../.venv-copiloto
source ../.venv-copiloto/Scripts/activate   # en macOS/Linux: source ../.venv-copiloto/bin/activate
pip install -r backend/requirements.txt
```

PowerShell:

```powershell
py -3 -m venv ..\.venv-copiloto   # probado con Python 3.12 y 3.13
..\.venv-copiloto\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

### 4.3 Variables de entorno
Para la ejecución local con SQLite (secciones 4.2 y 4.4) **no hace falta `.env`**: todo tiene valores por defecto.
El `.env` solo es obligatorio para Docker Compose (sección 4.5). Para crearlo, copie `.env.example` a `.env` en la
raíz; el archivo está en `.gitignore` y no se sube al repositorio. Variables (solo por nombre): `DJANGO_DEBUG`,
`DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DATABASE_URL`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`,
`CAMPOS_CIFRADO_KEY`, `LLM_PROVIDER` (por defecto `mock`), `LLM_MODEL`, `LLM_CACHE`, `CUOTA_TOKENS_DEFECTO`,
`COPILOTO_TAREAS_ASINCRONAS`, `MAGNETO_CLIENT` (`mock`), `DEV_AUTO_LOGIN`, `ANTHROPIC_API_KEY` y `LLM_TEMPERATURE`
(estas dos últimas solo para la prueba con un LLM real, sección 4.10). Los comandos para generar
`DJANGO_SECRET_KEY` y `CAMPOS_CIFRADO_KEY` están comentados en el mismo `.env.example`.

No se necesita ninguna llave externa (ni de un LLM ni de Magneto): ambos están simulados con `mock`.

### 4.4 Base de datos, datos de demostración y servidor

```bash
cd backend
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

`seed_demo` crea un usuario demo, una HV sintética y 12 vacantes sintéticas, e imprime en consola el correo y una
clave nueva en cada ejecución (no se guarda en ningún archivo). Use esas credenciales: ver salida de `seed_demo`.

### 4.5 Modo Docker Compose
No hay que crear ninguna base de datos: el compose levanta PostgreSQL 16 y crea la base `copiloto`. La única
variable obligatoria es `POSTGRES_PASSWORD`, una clave interna de esa base local que usted inventa (no es una llave
de ningún servicio externo). El resto de variables puede quedar como viene en `.env.example`.

1. Cree el `.env` con una clave aleatoria. PowerShell, desde la raíz del repo:

```powershell
Copy-Item .env.example .env
$pw = -join ((48..57)+(65..90)+(97..122) | Get-Random -Count 24 | ForEach-Object {[char]$_})
(Get-Content .env) -replace '^POSTGRES_PASSWORD=.*', "POSTGRES_PASSWORD=$pw" | Set-Content .env
$b = New-Object byte[] 32; [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b)
$k = [Convert]::ToBase64String($b).Replace('+','-').Replace('/','_')
(Get-Content .env) -replace '^CAMPOS_CIFRADO_KEY=.*', "CAMPOS_CIFRADO_KEY=$k" | Set-Content .env
$s = -join ((48..57)+(65..90)+(97..122) | Get-Random -Count 50 | ForEach-Object {[char]$_})
(Get-Content .env) -replace '^DJANGO_SECRET_KEY=.*', "DJANGO_SECRET_KEY=$s" | Set-Content .env
```

   Git Bash, macOS o Linux:

```bash
cp .env.example .env
sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$(python -c 'import secrets; print(secrets.token_hex(12))')/" .env
sed -i "s/^CAMPOS_CIFRADO_KEY=.*/CAMPOS_CIFRADO_KEY=$(python -c 'import os,base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode())')/" .env
sed -i "s/^DJANGO_SECRET_KEY=.*/DJANGO_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(50))')/" .env
```

   `CAMPOS_CIFRADO_KEY` es obligatoria en Docker: sin ella cada proceso del servidor usa una clave temporal distinta
   y no puede leer los datos cifrados que creó otro (por ejemplo, la HV demo cargada con `seed_demo`). Lo mismo pasa con
   `DJANGO_SECRET_KEY`: sin ella cada proceso firma las sesiones con una clave distinta y la aplicación pide iniciar
   sesión de nuevo en cada acción. Genere las tres variables antes del primer `docker compose up` y no las cambie
   después (si cambia `POSTGRES_PASSWORD` con la base ya creada, ejecute `docker compose down -v`).

2. Levante los servicios (la primera vez construye la imagen y aplica las migraciones):

```bash
docker compose up --build
```

3. En otra terminal, en la misma carpeta, cree el usuario y los datos de demostración. Imprime el correo y la
   clave del usuario demo:

```bash
docker compose exec web python manage.py seed_demo
```

4. Abra http://localhost:8000 e ingrese con esas credenciales. Para detener: `docker compose down`
   (agregue `-v` para borrar también los datos de la base).

Este modo no se ejecutó en la sesión de construcción: Pendiente de probar.

### 4.6 URLs de la aplicación

| URL | Pantalla |
|---|---|
| http://127.0.0.1:8000/magneto/ingresar/ | Ingreso con la cuenta de Magneto (simulada) |
| http://127.0.0.1:8000/hv/ | Mis hojas de vida (cargar, analizar, corregir perfil, eliminar) |
| http://127.0.0.1:8000/diagnostico/ | Diagnóstico y trazabilidad por agente |
| http://127.0.0.1:8000/vacantes/ | Vacantes ordenadas por ajuste, filtros y detalle |
| http://127.0.0.1:8000/preparacion/ | Preguntas de entrevista y plan de mejora |
| http://127.0.0.1:8000/magneto/consumo/ | Consumo de la cuota de tokens |
| http://127.0.0.1:8000/admin/ | Administración de Django (requiere `createsuperuser`) |

### 4.7 Troubleshooting

| Síntoma | Solución |
|---|---|
| `ModuleNotFoundError: django` | El venv no está activado: actívelo antes de `pip` y `manage.py` |
| `Error: That port is already in use` | `python manage.py runserver 8001` o cierre el proceso del puerto 8000 |
| `warning: LF will be replaced by CRLF` | Aviso de fin de línea en Windows; opcional `git config core.autocrlf true` |
| Aviso `core.W001` o error `core.E001` | Falta `CAMPOS_CIFRADO_KEY` en `.env` (con `DJANGO_DEBUG=0` es obligatoria) |
| `DJANGO_SECRET_KEY es obligatoria` | Ocurre con `DJANGO_DEBUG=0`: defínala en `.env` |
| `required variable POSTGRES_PASSWORD is missing a value` | Falta el `.env` o `POSTGRES_PASSWORD` está vacía: siga los pasos de la sección 4.5 |
| En Docker, la HV demo o el perfil no se pueden leer (error al descifrar) | `CAMPOS_CIFRADO_KEY` estaba vacía al cargar los datos: defínala en `.env`, ejecute `docker compose down -v`, `docker compose up --build` y repita `seed_demo` |
| La app pide iniciar sesión en cada acción (Docker) | `DJANGO_SECRET_KEY` vacía: defínala en `.env` y reinicie con `docker compose up -d` |
| `password authentication failed for user "copiloto"` | Se cambió `POSTGRES_PASSWORD` con la base ya creada: ejecute `docker compose down -v` y `docker compose up --build` |
| `temperature is deprecated for this model` | Quite `LLM_TEMPERATURE` del `.env`: por defecto no se envía ese parámetro |
| `No fue posible leer el archivo` con un LLM real | Ese mensaje aparece si falla cualquier agente. Revise en la terminal del servidor la línea `Falló el agente ...` y la pantalla Trazabilidad |
| `manage.py` no se encuentra | Ejecute los comandos de Django dentro de `backend` y con el venv activo (el prompt muestra `(.venv-copiloto)`) |
| La clave demo no funciona | `seed_demo` genera una clave nueva en cada ejecución: use la última impresa |

### 4.8 Decisiones y trade-offs

| Decisión | Por qué | Costo |
|---|---|---|
| Adaptador `MagnetoClient` con `MagnetoMockClient` | No hay API real de Magneto; el resto del sistema no depende de ella | El login y las vacantes son simulados con datos sintéticos |
| LLM inyectable (`LLMClient`) con `MockLLMClient` por defecto | Pruebas deterministas y sin red; costo cero en desarrollo | La calidad y la latencia con un LLM real no están medidas |
| Reglas deterministas más LLM para redactar | El puntaje, el ajuste y las brechas son reproducibles y explicables | El LLM solo redacta; no "decide" |
| Validador de veracidad en el grafo | El Extractor no puede devolver datos que no estén en la HV (NF03) | Puede descartar paráfrasis demasiado libres |
| SQLite en desarrollo, PostgreSQL 16 en contenedor | Arranque sin instalar nada extra | El modo contenedor no se probó en esta entrega |
| Cifrado Fernet de campos sensibles y del archivo | Datos personales protegidos en reposo (NF02) | No se puede filtrar por campos cifrados |
| Un solo núcleo compartido y features como plug-in | Cada Feature se agrega sin tocar archivos compartidos; PR sin conflictos | Cambiar el núcleo exige acuerdo del equipo |
| Tareas en segundo plano con hilos | Indicador de progreso sin bloquear la interfaz (NF01) | No hay cola de trabajos; suficiente para el MVP local |
| Embedder local por bolsa de palabras | Matching sin red y determinista | Menor calidad semántica que un modelo de embeddings |

### 4.9 Seguridad (OWASP básico)
- Secretos fuera del repositorio: `.env` está en `.gitignore`; `.env.example` solo lista nombres.
- `DEBUG` por variable; con `DJANGO_DEBUG=0` se exigen `DJANGO_SECRET_KEY` y `CAMPOS_CIFRADO_KEY` y se activan cookies seguras.
- Validación de entradas: extensión, tamaño (5 MB) y firma real del archivo; formularios de Django con CSRF activo.
- Autoescape de Django Templates sin `|safe`; contenido de la HV y del LLM escapado (probado con contenido hostil).
- Cada usuario solo ve sus HV y diagnósticos (404 en caso contrario).
- Logs con correos y teléfonos enmascarados; la traza de agentes guarda hash y resumen sin datos personales.
- Cuota mensual de tokens verificada antes de invocar el grafo (NF04).

### 4.10 Prueba con un LLM real (Claude)
Por defecto el proyecto usa un LLM simulado (`LLM_PROVIDER=mock`), sin llaves ni costo. Para probar con un modelo real:

1. Cree la llave en Claude Console (https://platform.claude.com):
   1. Inicie sesión y agregue crédito en Billing. La API se paga aparte de la suscripción a claude.ai.
   2. En Settings, Limits, fije un límite mensual de gasto bajo.
   3. En Settings, API Keys, pulse Create Key, póngale un nombre (por ejemplo `magneto-copiloto-prueba`) y cópiela: solo se muestra una vez.
2. Instale los paquetes opcionales en el venv (sección 4.2):

```powershell
pip install langchain langchain-anthropic
```

3. Abra el `.env` de la raíz (`notepad .env`; así la llave no queda en el historial del terminal) y defina:

```
LLM_PROVIDER=anthropic
LLM_MODEL=claude-haiku-5-5
LLM_CACHE=0
CUOTA_TOKENS_DEFECTO=100000
ANTHROPIC_API_KEY=su_llave_aqui
```

   `LLM_CACHE=0` evita que la caché falsee los tiempos. `CUOTA_TOKENS_DEFECTO` sube la cuota mensual por usuario, que se fija al ejecutar `seed_demo`. No defina `LLM_TEMPERATURE` salvo que su modelo la acepte.
4. Desde `backend` y con el venv activo, cree datos limpios y compruebe la llave antes de usar la aplicación:

```powershell
python manage.py migrate
python manage.py seed_demo
python manage.py shell -c "from core.llm.fabrica import crear_llm; from core.llm.esquemas import PerfilHV; r=crear_llm().generar('Ana Demo, Medellin, sabe SQL y Excel.', PerfilHV); print(r.modelo, r.tokens, r.datos.contacto.nombre, r.datos.habilidades)"
```

   Debe imprimir el modelo, un número real de tokens y los datos de Ana Demo. La consola de Windows puede mostrar mal los acentos; no afecta los datos.
5. Levante el servidor (`python manage.py runserver 8001`, ya que Docker puede ocupar el 8000) y recorra la aplicación con la HV sintética de demostración: subir y analizar, confirmar el perfil, diagnosticar (cronometrar para NF01), vacantes, coach y Trazabilidad. Use siempre datos sintéticos: el texto de la HV se envía al proveedor.
6. Al terminar, revoque la llave en Claude Console. El `.env` está en `.gitignore`; nunca suba la llave al repositorio.

El modo Docker no instala `langchain` ni pasa `ANTHROPIC_API_KEY`: esta prueba se hace con el venv local.

## 5. Pruebas

### 5.1 Casos de uso
Solo HU01, HU02, HU03, HU05, HU06 y NF01 tienen criterios oficiales (Entrega 1, sección 3.4). Los demás criterios
fueron redactados por el equipo a partir del enunciado y del Excel de UH y están **por validar con el PO**
(`docs/FUENTES_CRITERIOS.md`).

| CU | UH | Actor | Precondición | Flujo | Resultado esperado | Criterio |
|---|---|---|---|---|---|---|
| CU01 | HU01 | Candidato | Cuenta Magneto (simulada) | Abre el copiloto, ingresa correo y clave | Ve su nombre; con clave errada ve «Usuario o contraseña incorrectos» y conserva el correo | Oficial, `docs/CRITERIOS_acceso_magneto.md` |
| CU02 | HU02 | Candidato | Sesión iniciada | Carga un PDF o Word | Ve el nombre del archivo y el botón Analizar; otro formato o más de 5 MB muestra el mensaje de formato | Oficial, `docs/CRITERIOS_analisis_hv.md` |
| CU03 | HU03 | Candidato | HV cargada | Pulsa Analizar, revisa y corrige el perfil | Campos vacíos resaltados; cambios guardados solo al confirmar | Oficial, `docs/CRITERIOS_analisis_hv.md` |
| CU04 | HU05 | Candidato | HV analizada | Pide el diagnóstico | Puntaje 0-100 con nivel; si la HV no se pudo leer, mensaje en vez de puntaje | Oficial, `docs/CRITERIOS_diagnostico_hv.md` |
| CU05 | HU06 | Candidato | Diagnóstico listo | Revisa los hallazgos | Ordenados alta, media, baja; máximo 5 por pantalla con acción sugerida | Oficial, `docs/CRITERIOS_diagnostico_hv.md` |
| CU06 | HU07 | Candidato | Diagnóstico listo | Abre "¿Por qué este puntaje?" | Cada criterio con peso, puntos y evidencia | Derivado, `docs/CRITERIOS_diagnostico_hv.md` |
| CU07 | HU08 | Candidato | HV analizada, vacantes en BD | Abre Vacantes | Lista ordenada por ajuste con "Ver ajuste" por registro | Derivado, `docs/CRITERIOS_matching_vacantes.md` |
| CU08 | HU09 | Candidato | Lista de vacantes | Filtra por ciudad, modalidad y salario | Solo vacantes que cumplen los filtros, en orden de ajuste | Derivado, `docs/CRITERIOS_matching_vacantes.md` |
| CU09 | HU10 | Candidato | Lista de vacantes | Pulsa "Ver ajuste" | Requisitos que cumple y no cumple, con evidencia | Derivado, `docs/CRITERIOS_matching_vacantes.md` |
| CU10 | HU16 | Candidato | HV analizada | Elige una vacante en Preparación y genera | Preguntas probables con sugerencia de respuesta | Derivado, `docs/CRITERIOS_preparacion.md` |
| CU11 | HU17 | Candidato | HV analizada | Genera la preparación | Una acción con recurso y plazo por cada brecha | Derivado, `docs/CRITERIOS_preparacion.md` |

### 5.2 Resultados de pruebas automáticas
Ejecutadas el 14 de octubre de 2026 a las 23:10 (-0500) con `pytest -q --cov=apps --cov=core` y Python 3.12.4.
Todas las pruebas usan el LLM falso y bloquean la red.

| Rama (commit) | Tests | Pasados | Fallidos | Cobertura total (core + apps) | Cobertura `apps/` |
|---|---|---|---|---|---|
| `feature-1-acceso-e-integracion-magneto` (11e2ee3) | 88 | 88 | 0 | 99 % | 100 % |
| `feature-2-analisis-de-hv-agente-extractor` (e469ada) | 102 | 102 | 0 | 99 % | 99 % |
| `feature-3-diagnostico-de-hv-agente-evaluador` (afc3b0c) | 99 | 99 | 0 | 99 % | 100 % |
| `feature-4-matching-de-vacantes-agente-matcher` (0622997) | 98 | 98 | 0 | 99 % | 100 % |
| `feature-7-preparacion-agente-coach` (afc2b34) | 86 | 86 | 0 | 99 % | 100 % |
| `ajuste-ui-ux-sprint2` (0a502a7 más cambios sin commitear) | 230 | 230 | 0 | 99 % | 99 % |

Resumen crudo:

```
== feature-1-acceso-e-integracion-magneto 11e2ee3
TOTAL                            1240     13    99%
88 passed in 33.52s
TOTAL                                              116      0   100%
== feature-2-analisis-de-hv-agente-extractor e469ada
TOTAL                                  1432     13    99%
102 passed in 34.30s
TOTAL                                   308      1    99%
== feature-3-diagnostico-de-hv-agente-evaluador afc3b0c
TOTAL                            1374     12    99%
99 passed in 36.42s
TOTAL                                250      0   100%
== feature-4-matching-de-vacantes-agente-matcher 0622997
TOTAL                            1300     11    99%
98 passed in 28.39s
TOTAL                                   176      0   100%
== feature-7-preparacion-agente-coach afc2b34
TOTAL                            1269     11    99%
86 passed in 25.78s
TOTAL                             145      0   100%
== ajuste-ui-ux-sprint2 0a502a7
TOTAL                                  2119     16    99%
230 passed in 85.85s (0:01:25)
TOTAL                                              995      7    99%
```

En cada bloque, la primera línea `TOTAL` es la cobertura de `core` más `apps` y la última es solo `apps/`.

### 5.3 Ejecución del código

```bash
cd backend
pytest -q                                              # todas las pruebas
pytest -q apps/analisis_hv                             # una feature
pytest --cov=apps --cov-report=term-missing            # con cobertura
python -m coverage report --include="apps/*"           # cobertura solo de las features
```

Demo manual (Sección 6 del informe):
1. `python manage.py seed_demo` y `python manage.py runserver`; ingrese con las credenciales impresas.
2. **Lista desde la BD con acción por registro:** "Vacantes" lee la tabla `Vacante`, la ordena por ajuste y cada fila
   tiene "Ver ajuste", que abre los requisitos que cumple y no cumple.
3. **Formulario lanzado desde una lista que inserta, actualiza y borra:** en "Mis hojas de vida", "Cargar nueva HV"
   inserta, "Editar perfil" actualiza el perfil extraído (se guarda solo al confirmar) y "Eliminar" borra la HV con
   sus datos tras confirmar.

## 6. Gestión del proyecto
- **GitHub Projects (Kanban):** https://github.com/users/Juanp-la/projects/3 con columnas Backlog, For Start,
  In progress y Done, campos de sprint, estimación (SP), prioridad y módulo.
- **Jerarquía:** Feature → historia de usuario (HU) → requisitos funcionales (criterios de aceptación) y no funcionales (NF).
- **Priorización MoSCoW:** campo de prioridad del Project con valores Must have, Should have y Could have.
- **Scrum:** estimación con planning poker en escala Fibonacci (1, 2, 3, 5, 8, 13), velocidad supuesta de 50 SP por
  sprint, cono de incertidumbre de 128 a 206 SP y Definition of Done en el Excel de historias.
- **Wiki:** https://github.com/Juanp-la/Ing-Sowtfare/wiki

## 7. Autores

| Nombre | GitHub |
|---|---|
| Miguel Angel Colorado Castaño | [migueCOLORADO](https://github.com/migueCOLORADO) |
| Juan Pablo Lopera Arrazola | [Juanp-la](https://github.com/Juanp-la) |
| David Santiago Duarte Niño | [vantaf](https://github.com/vantaf) |

## 8. Contenido del curso

| Dato | Valor |
|---|---|
| Curso | Ingeniería de Software |
| Universidad | Universidad EAFIT |
| Profesora | Elizabeth Suescun Monsalve |
| Código del curso | C2666 |
| Programa | Ingenieria de Sistemas |
| Semestre | 2026-2 |

