# Diagrama entidad-relación (modelos reales del núcleo)

> Pendiente: exportar imagen desde draw.io.

Generado 1 a 1 desde `backend/core/models.py` (migración única `core/migrations/0001_initial.py`).
`PK` llave primaria, `FK` llave foránea, `UK` única. Los campos marcados "cifrado" se guardan con Fernet (NF02).
`USUARIO` hereda de `AbstractUser` de Django (sus relaciones con grupos y permisos no se dibujan).

```mermaid
erDiagram
    USUARIO ||--o{ HOJA_VIDA : carga
    USUARIO |o--o{ EJECUCION_AGENTE : genera
    HOJA_VIDA ||--o| PERFIL_EXTRAIDO : produce
    HOJA_VIDA ||--o{ DIAGNOSTICO : recibe
    DIAGNOSTICO ||--o{ HALLAZGO : contiene
    HOJA_VIDA ||--o{ PLAN_MEJORA : tiene
    DIAGNOSTICO |o--o{ PLAN_MEJORA : origina
    VACANTE |o--o{ PLAN_MEJORA : objetivo
    PERFIL_EXTRAIDO ||--o{ AJUSTE_VACANTE : evalua
    VACANTE ||--o{ AJUSTE_VACANTE : recibe
    HOJA_VIDA ||--o{ PREGUNTA_ENTREVISTA : prepara
    VACANTE ||--o{ PREGUNTA_ENTREVISTA : sobre
    HOJA_VIDA |o--o{ EJECUCION_AGENTE : traza

    USUARIO {
        bigint id PK
        string username UK
        string email UK
        string password "hash"
        string nombre
        string rol "candidato | reclutador | admin"
        string magneto_id UK "nullable"
        int cuota_tokens_mes "NF04"
        string first_name
        string last_name
        bool is_active
        bool is_staff
        bool is_superuser
        datetime last_login "nullable"
        datetime date_joined
    }
    HOJA_VIDA {
        bigint id PK
        bigint usuario_id FK
        string archivo "ruta del archivo cifrado"
        text nombre_archivo "cifrado"
        string formato "pdf | docx"
        int tamano_bytes
        text texto_extraido "cifrado"
        string estado "cargada | procesando | analizada | error"
        datetime fecha_carga
    }
    PERFIL_EXTRAIDO {
        bigint id PK
        bigint hoja_vida_id FK,UK
        text datos "JSON cifrado: contacto, experiencia, educacion, habilidades, idiomas"
        bool confirmado
        datetime fecha_actualizacion
    }
    DIAGNOSTICO {
        bigint id PK
        bigint hoja_vida_id FK
        smallint puntaje "0-100, nullable"
        string nivel "bajo | por_mejorar | competitivo"
        text explicacion
        json criterios "peso, obtenido y evidencia por criterio"
        int duracion_ms
        string estado "procesando | completado | error"
        string mensaje_error
        string ejecucion_id
        datetime fecha
    }
    HALLAZGO {
        bigint id PK
        bigint diagnostico_id FK
        string categoria
        text descripcion
        string prioridad "alta | media | baja"
        smallint rango
        text accion_sugerida
    }
    VACANTE {
        bigint id PK
        string magneto_id UK
        string titulo
        string empresa
        string ciudad
        string modalidad "presencial | remoto | hibrido"
        int salario_min
        int salario_max
        text descripcion
        json requisitos
        bool activa
        date fecha_publicacion
    }
    AJUSTE_VACANTE {
        bigint id PK
        bigint perfil_id FK
        bigint vacante_id FK
        float score
        json cumple
        json no_cumple
        datetime fecha
    }
    PLAN_MEJORA {
        bigint id PK
        bigint hoja_vida_id FK
        bigint diagnostico_id FK "nullable"
        bigint vacante_id FK "nullable"
        json acciones
        datetime fecha
    }
    PREGUNTA_ENTREVISTA {
        bigint id PK
        bigint hoja_vida_id FK
        bigint vacante_id FK
        text pregunta
        string tipo "tecnica | conductual | brecha"
        string brecha
        text sugerencia
        smallint orden
        datetime fecha
    }
    EJECUCION_AGENTE {
        bigint id PK
        bigint usuario_id FK "nullable"
        bigint hoja_vida_id FK "nullable, SET NULL al borrar la HV"
        string ejecucion_id
        string agente
        string entrada_hash "sha256"
        text salida_resumen "sin datos personales"
        int tokens
        int duracion_ms
        string estado "ok | error"
        datetime fecha
    }
```

Restricción adicional: `AJUSTE_VACANTE (perfil_id, vacante_id)` es única.

## Diferencias con el ER del informe (Entrega 2)

| Informe | Implementado | Motivo |
|---|---|---|
| `HV_ADAPTADA`, `POSTULACION` | No se crean | Pertenecen al Sprint 3 (HU12-HU15) |
| `PLAN_MEJORA.diagnostico_id` obligatorio | `diagnostico_id` opcional + `hoja_vida_id` + `vacante_id` | HU17 genera el plan desde una vacante |
| No existe | `PREGUNTA_ENTREVISTA` | HU16 guarda las preguntas generadas |
| `DIAGNOSTICO` (puntaje, explicacion, duracion_ms, fecha) | + `nivel`, `criterios`, `estado`, `mensaje_error`, `ejecucion_id` | HU05 nivel, HU07 explicabilidad, NF01 progreso |
| `HALLAZGO` | + `accion_sugerida`, `rango` | HU06 acción sugerida y orden por prioridad |
| `HOJA_VIDA` | + `nombre_archivo`, `tamano_bytes`, `estado`; texto y nombre cifrados | HU02, NF02 |
| `PERFIL_EXTRAIDO.datos` JSON | Texto con JSON cifrado | NF02 |
| `EJECUCION_AGENTE` | + `hoja_vida_id`, `ejecucion_id` | NF01 progreso por ejecución, NF05 |
| `USUARIO` | Hereda de `AbstractUser` (login por correo) | Autenticación de Django |
| `VACANTE` | + `descripcion`, `activa`, `fecha_publicacion` | Lista y detalle de vacantes |
