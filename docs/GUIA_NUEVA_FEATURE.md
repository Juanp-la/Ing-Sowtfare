# Guía: agregar una Feature sin editar archivos compartidos

El proyecto tiene un **núcleo** idéntico en todas las ramas y una carpeta por **feature**.
Agregar una feature = agregar carpetas. No se edita ningún archivo del núcleo.

## Qué es núcleo (no tocar desde una feature)

| Ruta | Contenido |
|---|---|
| `backend/config/` | settings (descubre features), urls (monta features), wsgi/asgi |
| `backend/core/` | modelos y migración `0001_initial`, motor de agentes, LLM, servicios, seed, factories de prueba |
| `backend/conftest.py`, `pytest.ini`, `.coveragerc`, `requirements.txt`, `Dockerfile`, `manage.py` | ejecución y pruebas |
| `backend/apps/__init__.py` | paquete contenedor de features |
| `frontend/templates/base.html`, `partials/`, `core/` | plantilla base Bootstrap 5, menú, mensajes, estados vacío/error |
| `frontend/static/css/app.css`, `frontend/static/js/app.js` | estilos y utilidades JS comunes |
| `docker-compose.yml`, `.gitignore`, `.env.example`, `docs/GUIA_NUEVA_FEATURE.md` | entorno |

Si una feature necesita un cambio en el núcleo, se acuerda en equipo y se aplica **igual** en todas
las ramas (los archivos del núcleo deben quedar byte a byte idénticos).

## Estructura de una feature

```
backend/apps/<app>/
  __init__.py
  apps.py        AppConfig con prefijo_url, menu (y opcionalmente url_login, fragmentos_navbar)
  urls.py        app_name = "<app>"
  views.py  forms.py  servicios.py
  agentes.py     registra los nodos de LangGraph de la feature
  tests/         una prueba por criterio de aceptación
frontend/templates/<app>/   plantillas que extienden base.html
frontend/static/<app>/      css/js propios (opcional)
docs/CRITERIOS_<app>.md     criterios de aceptación de sus UH/NFR
```

## 1. AppConfig (plug-in)

```python
# backend/apps/mi_feature/apps.py
from django.apps import AppConfig

class MiFeatureConfig(AppConfig):
    name = "apps.mi_feature"
    label = "mi_feature"
    verbose_name = "Mi feature"
    prefijo_url = "mi-feature/"                       # se monta en /mi-feature/
    menu = [{"titulo": "Mi feature", "url": "mi_feature:inicio", "orden": 50}]
    # url_login = "mi_feature:ingresar"                # solo si reemplaza el login del núcleo
    # fragmentos_navbar = ["mi_feature/partials/x.html"]  # se incluyen en la barra superior
```

`config/settings.py` agrega a `INSTALLED_APPS` toda carpeta `backend/apps/*/apps.py`;
`config/urls.py` la monta con `prefijo_url`; el menú de `base.html` se arma con `menu`.

## 2. Nodos del grafo (LangGraph)

```python
# backend/apps/mi_feature/agentes.py
from core.agentes.base import AgenteBase
from core.agentes.registro import registrar_nodo

class AgenteMio(AgenteBase):
    nombre = "mio"

    def ejecutar(self, estado):
        borrador = {...}                                   # reglas deterministas
        datos = self.consultar_llm("prompt", MiEsquema, borrador=borrador)  # LLM falso por defecto
        return {"datos": {**estado.get("datos", {}), "mio": datos.model_dump()}}

registrar_nodo("mio", AgenteMio, intenciones=["mi_intencion"], orden=10)
```

- `AgenteBase.__call__` mide la duración, registra la traza en `EjecucionAgente` (NF05) y suma tokens (NF04).
- `GrafoCopiloto.construir()` arma: `START -> control_cuota -> supervisor -> nodos de la intención (por orden) -> END`.
- Para no editar `EstadoCopiloto`, use la llave genérica `datos` para lo propio de la feature.
- Para aplicar el validador de veracidad (NF03) a su salida, registre una subclase de `core.agentes.validador.NodoValidador`
  con `campo` apuntando a la llave que quiere validar y un `orden` mayor que el de su agente.

## 3. Invocar el grafo desde una vista

```python
from core.servicios.copiloto import CopilotoService
resultado = CopilotoService().ejecutar(request.user, "mi_intencion", hoja_vida_id=hv.pk, texto_hv=hv.texto_extraido)
```

Si el usuario no tiene cuota, se lanza `CuotaAgotada` y el middleware del núcleo muestra el aviso (HTTP 429).

## 4. Modelos

Las features **no** definen modelos que otra feature necesite. Todo modelo compartido vive en
`core/models.py` con la migración única `0001_initial`. Si una feature necesitara un modelo propio
y privado, debe acordarse antes con el equipo.

## 5. Pruebas

- Use las fixtures de `backend/conftest.py`: `usuario`, `cliente_autenticado`, `hv_demo`, `vacantes_demo`,
  `llm_falso`, `registro_aislado`; y las factories de `core/pruebas/fabricas.py` (`pdf_bytes`, `docx_bytes`, ...).
- El LLM es falso y determinista (`LLM_PROVIDER=mock`). Las pruebas bloquean la red.
- Una prueba por criterio de aceptación. Cobertura objetivo de la app: 80 % o más:
  `pytest --cov=apps/<app> --cov-report=term-missing`.
