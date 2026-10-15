"""NÚCLEO compartido de Magneto Copiloto: modelos, motor de agentes, LLM y servicios.

Este paquete es idéntico en todas las ramas de feature. No lo edite desde una feature:
las features se conectan por AppConfig (prefijo_url, menu, url_login, fragmentos_navbar)
y registran sus nodos con core.agentes.registro.registrar_nodo().
"""
