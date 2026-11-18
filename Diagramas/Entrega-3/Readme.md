# Diagramas de la Entrega 3 (Sprint 3)

En rojo: lo que se agregó en el Sprint 3.

| Diagrama | Archivo | Fuente |
|---|---|---|
| Clases de implementación: motor de agentes | `clases_agentes.png` | `fuentes/gen_clases.py` (Graphviz) |
| Clases de implementación: servicios, adaptadores y modelos | `clases_servicios.png` | `fuentes/gen_servicios.py` (Graphviz) |
| Despliegue | `despliegue.png` | `fuentes/despliegue.dot` |
| Entidad-relación implementado (migraciones 0001 y 0002) | `entidad_relacion.png` | `fuentes/er.mmd` (Mermaid) |
| Arquitectura por capas | `capas.png` | `fuentes/capas.dot` |
| Grafo de agentes (intenciones) | `grafo.png` | `fuentes/grafo.dot` |
| Árbol de directorios | `arbol.png` | `fuentes/arbol.html` |

Regenerar: `cd fuentes && python gen_clases.py && python gen_servicios.py && dot -Tpng -Gdpi=170 despliegue.dot -o ../despliegue.png`
(lo mismo para `capas.dot` y `grafo.dot`); el ER con `mmdc -i er.mmd -o ../entidad_relacion.png`.
