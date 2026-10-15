"""Datos 100 % sintéticos para demo y pruebas. Ninguna persona ni empresa es real."""

EMAIL_DEMO = "demo@copiloto.test"
NOMBRE_DEMO = "Ana Demo Restrepo"
MAGNETO_ID_DEMO = "MAG-DEMO-0001"

TEXTO_HV_DEMO = """ANA DEMO RESTREPO
Tecnóloga en Sistemas | Medellín, Antioquia | ana.demo@ejemplo.test | +57 300 000 0000

PERFIL
Tecnóloga en sistemas con 3 años de experiencia en soporte técnico y mesa de ayuda.
Busco un rol de soporte de aplicaciones o analista de datos junior.

EXPERIENCIA
Analista de soporte - Empresa Ficticia XYZ (2022 - 2025)
Atención de incidentes de usuarios finales, escalamiento a nivel 2 y documentación en Zendesk.
Auxiliar de sistemas - Comercializadora Ficticia ABC (2021 - 2022)
Mantenimiento de equipos y administración de inventario de TI.

EDUCACIÓN
Tecnología en Sistemas de Información - Institución Universitaria Ficticia (2021)
Bachiller académico - Colegio Ficticio (2017)

HABILIDADES
SQL, Windows Server, Zendesk, Excel, Soporte técnico, Atención al cliente

IDIOMAS
Inglés B1
"""

PERFIL_DEMO = {
    "contacto": {
        "nombre": "Ana Demo Restrepo",
        "email": "ana.demo@ejemplo.test",
        "telefono": "+57 300 000 0000",
        "ciudad": "Medellín",
    },
    "resumen": "Tecnóloga en sistemas con 3 años de experiencia en soporte técnico y mesa de ayuda.",
    "experiencia": [
        {
            "cargo": "Analista de soporte",
            "empresa": "Empresa Ficticia XYZ",
            "periodo": "2022 - 2025",
            "descripcion": "Atención de incidentes de usuarios finales, escalamiento a nivel 2 y documentación en Zendesk.",
        },
        {
            "cargo": "Auxiliar de sistemas",
            "empresa": "Comercializadora Ficticia ABC",
            "periodo": "2021 - 2022",
            "descripcion": "Mantenimiento de equipos y administración de inventario de TI.",
        },
    ],
    "educacion": [
        {"titulo": "Tecnología en Sistemas de Información", "institucion": "Institución Universitaria Ficticia", "anio": "2021"},
        {"titulo": "Bachiller académico", "institucion": "Colegio Ficticio", "anio": "2017"},
    ],
    "habilidades": ["SQL", "Windows Server", "Zendesk", "Excel", "Soporte técnico", "Atención al cliente"],
    "idiomas": ["Inglés B1"],
}


def _req(tipo, valor, obligatorio=False, anios=None):
    requisito = {"tipo": tipo, "valor": valor, "obligatorio": obligatorio}
    if anios is not None:
        requisito["anios"] = anios
    return requisito


VACANTES_DEMO = [
    {
        "magneto_id": "MAG-V-001", "titulo": "Analista de soporte de aplicaciones", "empresa": "TecnoAndes (ficticia)",
        "ciudad": "Medellín", "modalidad": "hibrido", "salario_min": 2800000, "salario_max": 3500000,
        "descripcion": "Soporte de segundo nivel a aplicaciones internas, gestión de incidentes y consultas SQL.",
        "requisitos": [_req("habilidad", "SQL", True), _req("experiencia", "soporte", True, 2),
                       _req("habilidad", "Zendesk"), _req("educacion", "tecnólogo", True), _req("idioma", "Inglés B1")],
    },
    {
        "magneto_id": "MAG-V-002", "titulo": "Técnico de mesa de ayuda", "empresa": "Servicios Ficticios del Valle",
        "ciudad": "Cali", "modalidad": "presencial", "salario_min": 1800000, "salario_max": 2300000,
        "descripcion": "Atención de usuarios en mesa de ayuda y soporte a estaciones Windows.",
        "requisitos": [_req("experiencia", "mesa de ayuda", True, 1), _req("habilidad", "Windows Server"),
                       _req("habilidad", "Atención al cliente"), _req("educacion", "técnico")],
    },
    {
        "magneto_id": "MAG-V-003", "titulo": "Analista de datos junior", "empresa": "DatosNorte (ficticia)",
        "ciudad": "Bogotá", "modalidad": "remoto", "salario_min": 3200000, "salario_max": 4200000,
        "descripcion": "Construcción de reportes y tableros a partir de bases de datos relacionales.",
        "requisitos": [_req("habilidad", "SQL", True), _req("habilidad", "Python", True), _req("habilidad", "Power BI"),
                       _req("educacion", "profesional", True), _req("idioma", "Inglés B2")],
    },
    {
        "magneto_id": "MAG-V-004", "titulo": "Desarrollador backend Python", "empresa": "CódigoSur (ficticia)",
        "ciudad": "Medellín", "modalidad": "remoto", "salario_min": 5000000, "salario_max": 7000000,
        "descripcion": "Desarrollo de servicios web con Django y PostgreSQL.",
        "requisitos": [_req("habilidad", "Python", True), _req("habilidad", "Django", True),
                       _req("experiencia", "desarrollo", True, 3), _req("habilidad", "Git"), _req("educacion", "profesional")],
    },
    {
        "magneto_id": "MAG-V-005", "titulo": "Auxiliar de sistemas", "empresa": "Logística Ficticia S.A.S.",
        "ciudad": "Barranquilla", "modalidad": "presencial", "salario_min": 1500000, "salario_max": 1900000,
        "descripcion": "Mantenimiento preventivo de equipos y apoyo a usuarios.",
        "requisitos": [_req("experiencia", "sistemas", False, 1), _req("habilidad", "Excel"),
                       _req("habilidad", "Mantenimiento de equipos"), _req("educacion", "técnico")],
    },
    {
        "magneto_id": "MAG-V-006", "titulo": "Coordinador de soporte TI", "empresa": "Grupo Ficticio Andino",
        "ciudad": "Bogotá", "modalidad": "hibrido", "salario_min": 4500000, "salario_max": 5500000,
        "descripcion": "Liderar el equipo de soporte y los procesos ITIL.",
        "requisitos": [_req("experiencia", "soporte", True, 4), _req("habilidad", "ITIL", True),
                       _req("habilidad", "Liderazgo"), _req("educacion", "profesional"), _req("idioma", "Inglés B2")],
    },
    {
        "magneto_id": "MAG-V-007", "titulo": "Agente de servicio al cliente bilingüe", "empresa": "ContactoFicticio",
        "ciudad": "Medellín", "modalidad": "presencial", "salario_min": 2000000, "salario_max": 2600000,
        "descripcion": "Atención telefónica y por chat a clientes internacionales.",
        "requisitos": [_req("habilidad", "Atención al cliente", True), _req("idioma", "Inglés B2", True),
                       _req("experiencia", "servicio", False, 1), _req("educacion", "bachiller")],
    },
    {
        "magneto_id": "MAG-V-008", "titulo": "Administrador de bases de datos junior", "empresa": "InfoDatos (ficticia)",
        "ciudad": "Cali", "modalidad": "hibrido", "salario_min": 3500000, "salario_max": 4500000,
        "descripcion": "Administración y respaldo de bases de datos.",
        "requisitos": [_req("habilidad", "SQL", True), _req("habilidad", "PostgreSQL"), _req("habilidad", "Windows Server"),
                       _req("educacion", "tecnólogo", True), _req("experiencia", "bases de datos", False, 1)],
    },
    {
        "magneto_id": "MAG-V-009", "titulo": "Analista de calidad de software (QA)", "empresa": "PruebasYa (ficticia)",
        "ciudad": "Bogotá", "modalidad": "remoto", "salario_min": 3000000, "salario_max": 4000000,
        "descripcion": "Diseño y ejecución de pruebas funcionales.",
        "requisitos": [_req("habilidad", "Pruebas de software", True), _req("habilidad", "SQL"), _req("habilidad", "Jira"),
                       _req("educacion", "tecnólogo"), _req("experiencia", "pruebas", False, 1)],
    },
    {
        "magneto_id": "MAG-V-010", "titulo": "Soporte técnico en sitio", "empresa": "RedesFicticias",
        "ciudad": "Medellín", "modalidad": "presencial", "salario_min": 1900000, "salario_max": 2400000,
        "descripcion": "Visitas a clientes para soporte de equipos y redes.",
        "requisitos": [_req("habilidad", "Soporte técnico", True), _req("habilidad", "Windows Server"),
                       _req("experiencia", "soporte", True, 1), _req("educacion", "técnico")],
    },
    {
        "magneto_id": "MAG-V-011", "titulo": "Analista de inventarios TI", "empresa": "Comercial Ficticia del Caribe",
        "ciudad": "Barranquilla", "modalidad": "hibrido", "salario_min": 2200000, "salario_max": 2900000,
        "descripcion": "Control del inventario de equipos de tecnología.",
        "requisitos": [_req("habilidad", "Excel", True), _req("experiencia", "inventario", False, 1),
                       _req("habilidad", "SQL"), _req("educacion", "tecnólogo")],
    },
    {
        "magneto_id": "MAG-V-012", "titulo": "Practicante de analítica", "empresa": "Universidad Ficticia",
        "ciudad": "Bogotá", "modalidad": "hibrido", "salario_min": 1300000, "salario_max": 1300000,
        "descripcion": "Apoyo en limpieza de datos y reportes.",
        "requisitos": [_req("habilidad", "Excel"), _req("habilidad", "Python"), _req("educacion", "bachiller", True)],
    },
]
