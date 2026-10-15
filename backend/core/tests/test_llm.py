import time

import pytest
from django.core.exceptions import ImproperlyConfigured
from pydantic import BaseModel

from core.llm import fabrica
from core.llm.base import estimar_tokens
from core.llm.cache import LLMConCache
from core.llm.esquemas import PerfilHV, perfil_vacio
from core.llm.langchain_adapter import LangChainLLMClient, _fabrica_por_defecto
from core.llm.mock import MockLLMClient


class Saludo(BaseModel):
    texto: str = ""


def test_mock_es_determinista_y_devuelve_el_borrador():
    llm = MockLLMClient()
    a = llm.generar("prompt", Saludo, borrador={"texto": "hola"})
    b = llm.generar("prompt", Saludo, borrador={"texto": "hola"})
    assert a.datos == b.datos and a.datos.texto == "hola"
    assert a.tokens == b.tokens > 0
    assert len(llm.llamadas) == 2


def test_mock_respuestas_forzadas_y_latencia():
    llm = MockLLMClient(respuestas={"Saludo": {"texto": "forzado"}}, latencia_s=0.05)
    inicio = time.perf_counter()
    assert llm.generar("p", Saludo).datos.texto == "forzado"
    assert time.perf_counter() - inicio >= 0.05
    llm = MockLLMClient(respuestas={"Saludo": lambda prompt, borrador: {"texto": prompt.upper()}})
    assert llm.generar("abc", Saludo).datos.texto == "ABC"


def test_cache_no_repite_llamadas_ni_cobra_tokens():
    base = MockLLMClient(latencia_s=0.05)
    llm = LLMConCache(base, max_items=1)
    primera = llm.generar("p", Saludo, borrador={"texto": "x"})
    inicio = time.perf_counter()
    segunda = llm.generar("p", Saludo, borrador={"texto": "x"})
    assert time.perf_counter() - inicio < 0.05
    assert segunda.desde_cache and segunda.tokens == 0 and primera.tokens > 0
    llm.generar("otro", Saludo)  # expulsa la primera (max_items=1)
    assert len(base.llamadas) == 2
    llm.generar("p", Saludo, borrador={"texto": "x"})
    assert len(base.llamadas) == 3


def test_fabrica_por_defecto_es_mock_con_cache(settings):
    settings.LLM_PROVIDER = "mock"
    settings.LLM_CACHE = True
    fabrica.restablecer_llm()
    llm = fabrica.obtener_llm()
    assert isinstance(llm, LLMConCache) and isinstance(llm.cliente, MockLLMClient)
    assert fabrica.obtener_llm() is llm
    settings.LLM_CACHE = False
    assert isinstance(fabrica.crear_llm(), MockLLMClient)


def test_fabrica_permite_inyectar_un_cliente():
    falso = MockLLMClient()
    fabrica.establecer_llm(falso)
    assert fabrica.obtener_llm() is falso


def test_proveedor_real_exige_modelo(settings):
    settings.LLM_PROVIDER = "openai"
    settings.LLM_MODEL = ""
    with pytest.raises(ImproperlyConfigured):
        fabrica.crear_llm()


class _RespuestaCruda:
    usage_metadata = {"total_tokens": 42}


class _ModeloFalso:
    def __init__(self, parsed):
        self.parsed = parsed
        self.mensajes = []

    def with_structured_output(self, esquema, include_raw):
        assert include_raw is True
        return self

    def invoke(self, mensaje):
        self.mensajes.append(mensaje)
        return {"parsed": self.parsed, "raw": _RespuestaCruda()}


def test_adaptador_langchain_con_modelo_inyectado_sin_red():
    modelo = _ModeloFalso(Saludo(texto="ok"))
    cliente = LangChainLLMClient("proveedor", "modelo-x", fabrica=lambda p, m: modelo)
    respuesta = cliente.generar("Hola", Saludo, borrador={"texto": "b"})
    assert respuesta.datos.texto == "ok" and respuesta.tokens == 42 and respuesta.modelo == "modelo-x"
    assert "Borrador" in modelo.mensajes[0]


def test_adaptador_langchain_rechaza_salida_invalida():
    cliente = LangChainLLMClient("p", "m", fabrica=lambda p, m: _ModeloFalso(None))
    with pytest.raises(ValueError):
        cliente.generar("Hola", Saludo)


def test_adaptador_sin_paquete_langchain_da_error_claro(monkeypatch):
    import builtins

    original = builtins.__import__

    def importar(nombre, *args, **kwargs):
        if nombre.startswith("langchain.chat_models") or nombre == "langchain":
            raise ImportError(nombre)
        return original(nombre, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", importar)
    with pytest.raises(ImproperlyConfigured):
        _fabrica_por_defecto("openai", "gpt")


def test_esquema_de_perfil_vacio_y_tokens():
    assert perfil_vacio()["experiencia"] == []
    assert PerfilHV.model_validate({"habilidades": ["SQL"]}).habilidades == ["SQL"]
    assert estimar_tokens("") == 1 and estimar_tokens("a" * 8) == 2
