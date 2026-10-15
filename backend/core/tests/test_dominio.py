from datetime import date

from core.datos_demo import PERFIL_DEMO
from core.dominio.requisitos import anios_periodo, evaluar_requisito, evaluar_requisitos, nivel_educativo
from core.dominio.texto import normalizar, palabras, texto_perfil


def _req(tipo, valor, **extra):
    return {"tipo": tipo, "valor": valor, **extra}


def test_normalizar_y_aplanar_perfil():
    assert normalizar("  Atención   AL Cliente ") == "atencion al cliente"
    assert palabras("C# y SQL!") == ["c#", "y", "sql"]
    assert "Zendesk" in texto_perfil(PERFIL_DEMO) and texto_perfil(None) == ""


def test_habilidad_declarada_y_mencionada_en_experiencia():
    assert evaluar_requisito(PERFIL_DEMO, _req("habilidad", "sql"))["evidencia"] == "Habilidad declarada: SQL"
    mencionada = evaluar_requisito(PERFIL_DEMO, _req("habilidad", "escalamiento"))
    assert mencionada["cumple"] and "experiencia" in mencionada["evidencia"]
    faltante = evaluar_requisito(PERFIL_DEMO, _req("habilidad", "Python", obligatorio=True))
    assert not faltante["cumple"] and faltante["obligatorio"] and faltante["evidencia"] == "No aparece en la hoja de vida"
    assert not evaluar_requisito(PERFIL_DEMO, _req("habilidad", "R"))["cumple"]  # no confunde letras sueltas


def test_experiencia_por_anios():
    assert evaluar_requisito(PERFIL_DEMO, _req("experiencia", "soporte", anios=2))["cumple"]
    corta = evaluar_requisito(PERFIL_DEMO, _req("experiencia", "soporte", anios=4))
    assert not corta["cumple"] and "3 año(s)" in corta["evidencia"]
    assert "Sin experiencia" in evaluar_requisito(PERFIL_DEMO, _req("experiencia", "desarrollo"))["evidencia"]


def test_educacion_por_nivel():
    assert evaluar_requisito(PERFIL_DEMO, _req("educacion", "técnico"))["cumple"]
    assert evaluar_requisito(PERFIL_DEMO, _req("educacion", "tecnólogo"))["cumple"]
    assert not evaluar_requisito(PERFIL_DEMO, _req("educacion", "profesional"))["cumple"]
    assert nivel_educativo("Maestría en datos") == 6 and nivel_educativo("Curso libre") == 0


def test_idioma_por_nivel():
    assert evaluar_requisito(PERFIL_DEMO, _req("idioma", "Inglés B1"))["cumple"]
    assert not evaluar_requisito(PERFIL_DEMO, _req("idioma", "Inglés B2"))["cumple"]
    assert "no aparece" in evaluar_requisito(PERFIL_DEMO, _req("idioma", "Francés A2"))["evidencia"]


def test_periodos_y_separacion_cumple_no_cumple():
    assert anios_periodo("2022 - 2025") == 3
    assert anios_periodo("2020 - actual", hoy=date(2026, 1, 1)) == 6
    assert anios_periodo("2024") == 0 and anios_periodo("sin fechas") == 0
    cumple, no_cumple = evaluar_requisitos(PERFIL_DEMO, [_req("habilidad", "Excel"), _req("habilidad", "Django")])
    assert [r["requisito"] for r in cumple] == ["Excel"] and [r["requisito"] for r in no_cumple] == ["Django"]
    assert evaluar_requisitos({}, None) == ([], [])
