import pytest
from langgraph.graph import END
from pydantic import BaseModel

from core.agentes.base import AgenteBase
from core.agentes.grafo import GrafoCopiloto
from core.agentes.supervisor import Supervisor
from core.agentes.trazador import Trazador, hash_entrada, resumir
from core.agentes.validador import NodoValidador, ValidadorVeracidad
from core.datos_demo import PERFIL_DEMO, TEXTO_HV_DEMO
from core.llm.mock import MockLLMClient
from core.models import EjecucionAgente


class Eco(BaseModel):
    texto: str = ""


class AgenteEco(AgenteBase):
    nombre = "eco"

    def ejecutar(self, estado):
        datos = self.consultar_llm("eco", Eco, borrador={"texto": estado.get("texto_hv", "")})
        return {"explicacion": datos.texto}


class AgenteMayus(AgenteBase):
    nombre = "mayus"

    def ejecutar(self, estado):
        return {"explicacion": estado.get("explicacion", "").upper()}


class AgenteRoto(AgenteBase):
    nombre = "roto"

    def ejecutar(self, estado):
        raise RuntimeError("dato personal ana.demo@ejemplo.test")


@pytest.fixture
def solo_prueba(registro_aislado):
    registro_aislado.restaurar({})
    registro_aislado.registrar_nodo("mayus", AgenteMayus, intenciones=["eco"], orden=20)
    registro_aislado.registrar_nodo("eco", AgenteEco, intenciones=["eco", "solo_eco"], orden=10)
    registro_aislado.registrar_nodo("roto", AgenteRoto, intenciones=["romper"], orden=5)
    return registro_aislado


def test_agente_base_mide_y_traza_sin_persistir():
    agente = AgenteEco(llm=MockLLMClient(), trazador=Trazador(persistir=False))
    salida = agente({"texto_hv": "hola"})
    assert salida["explicacion"] == "hola"
    assert salida["tokens_usados"] > 0
    (registro,) = salida["traza"]
    assert registro["agente"] == "eco" and registro["estado"] == "ok" and registro["duracion_ms"] >= 0


@pytest.mark.django_db
def test_agente_que_falla_queda_trazado_sin_pii(usuario):
    salida = AgenteRoto(llm=MockLLMClient())({"usuario_id": usuario.pk})
    assert salida["error"] == "roto: RuntimeError"
    fila = EjecucionAgente.objects.get(agente="roto")
    assert fila.estado == "error" and "ana.demo" not in fila.salida_resumen and fila.usuario == usuario


def test_resumen_de_traza_no_incluye_valores_personales():
    texto = resumir({"perfil": {"email": "x@y.z"}, "habilidades": ["SQL"], "explicacion": "Ana Demo",
                     "ruta": "extractor", "puntaje": 80, "ok": True, "traza": [1], "otro": 1.5})
    assert "x@y.z" not in texto and "Ana Demo" not in texto
    assert "ruta=extractor" in texto and "puntaje=80" in texto and "perfil{1}" in texto
    assert "habilidades[1]" in texto and "explicacion(8 car.)" in texto and "ok=True" in texto
    assert len(hash_entrada({"a": 1})) == 64


def test_registro_valida_nombres_e_intenciones(registro_aislado):
    with pytest.raises(ValueError):
        registro_aislado.registrar_nodo("supervisor", AgenteEco, intenciones=["x"])
    with pytest.raises(ValueError):
        registro_aislado.registrar_nodo("nuevo", AgenteEco, intenciones=[])
    registro_aislado.registrar_nodo("nuevo", AgenteEco, intenciones=["prueba_registro"])
    assert "prueba_registro" in registro_aislado.intenciones()
    registro_aislado.eliminar_nodo("nuevo")
    assert registro_aislado.nodos_para("prueba_registro") == []


def test_supervisor_rutea_por_intencion(solo_prueba):
    supervisor = Supervisor(llm=MockLLMClient(), trazador=Trazador(persistir=False))
    assert supervisor.decidir_ruta({"intencion": "eco"}) == "eco"
    salida = supervisor({"intencion": "desconocida"})
    assert salida["ruta"] == END and salida["error"] == "intencion_no_disponible"


@pytest.mark.django_db
def test_grafo_ejecuta_los_nodos_de_la_intencion_en_orden(solo_prueba, usuario):
    final = GrafoCopiloto(llm=MockLLMClient()).invocar(
        {"intencion": "eco", "usuario_id": usuario.pk, "texto_hv": "hola"}
    )
    assert final["explicacion"] == "HOLA"
    assert [t["agente"] for t in final["traza"]] == ["supervisor", "eco", "mayus"]
    assert EjecucionAgente.objects.filter(ejecucion_id=final["ejecucion_id"]).count() == 3
    solo = GrafoCopiloto(llm=MockLLMClient(), trazador=Trazador(persistir=False)).invocar(
        {"intencion": "solo_eco", "texto_hv": "hola"}
    )
    assert solo["explicacion"] == "hola"


def test_grafo_corta_cuando_un_nodo_falla_o_no_hay_ruta(solo_prueba):
    grafo = GrafoCopiloto(llm=MockLLMClient(), trazador=Trazador(persistir=False))
    assert grafo.invocar({"intencion": "romper"})["error"] == "roto: RuntimeError"
    assert grafo.invocar({"intencion": "nada"})["error"] == "intencion_no_disponible"


@pytest.mark.django_db
def test_grafo_bloquea_sin_cuota_antes_del_supervisor(solo_prueba, usuario):
    usuario.cuota_tokens_mes = 0
    usuario.save()
    final = GrafoCopiloto(llm=MockLLMClient()).invocar({"intencion": "eco", "usuario_id": usuario.pk})
    assert final["error"] == "cuota_agotada" and final["traza"] == []
    assert GrafoCopiloto(llm=MockLLMClient()).invocar({"intencion": "eco", "usuario_id": 999999})["cuota_ok"] is False


def test_validador_detecta_experiencia_inventada():
    generado = {**PERFIL_DEMO, "experiencia": PERFIL_DEMO["experiencia"] + [
        {"cargo": "Gerente general", "empresa": "Multinacional Inventada", "periodo": "2015 - 2020", "descripcion": ""}
    ], "habilidades": PERFIL_DEMO["habilidades"] + ["Kubernetes"]}
    validador = ValidadorVeracidad()
    inventados = validador.verificar(TEXTO_HV_DEMO, generado)
    assert "Gerente general" in inventados and "Kubernetes" in inventados
    assert validador.verificar(TEXTO_HV_DEMO, PERFIL_DEMO) == []
    limpio = validador.depurar(TEXTO_HV_DEMO, generado)
    assert len(limpio["experiencia"]) == 2 and "Kubernetes" not in limpio["habilidades"]


def test_validador_acepta_parafrasis_y_rechaza_numeros_nuevos():
    validador = ValidadorVeracidad()
    assert validador.verificar(TEXTO_HV_DEMO, {"resumen": "Experiencia en soporte técnico y mesa de ayuda"}) == []
    assert validador.verificar(TEXTO_HV_DEMO, {"resumen": "10 años de experiencia en soporte"}) != []
    assert validador.verificar(TEXTO_HV_DEMO, {"x": "TI"}) == []  # palabra corta presente
    assert validador.depurar(TEXTO_HV_DEMO, {"a": "Astronauta", "b": 3, "c": [3, [1]]}) == {"a": "", "b": 3, "c": [3, [1]]}


def test_nodo_validador_deja_constancia_de_lo_rechazado():
    nodo = NodoValidador(llm=MockLLMClient(), trazador=Trazador(persistir=False))
    salida = nodo({"texto_hv": TEXTO_HV_DEMO, "perfil": {"habilidades": ["SQL", "Astronomía cuántica"]}})
    assert salida["perfil"]["habilidades"] == ["SQL"]
    assert salida["validacion"] == {"ok": False, "rechazados": ["Astronomía cuántica"], "campo": "perfil"}
    assert nodo({"texto_hv": TEXTO_HV_DEMO, "perfil": PERFIL_DEMO})["validacion"]["ok"] is True
