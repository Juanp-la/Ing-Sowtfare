"""Esquemas Pydantic compartidos (contrato del perfil que producen y consumen los agentes)."""
from pydantic import BaseModel, Field


class Contacto(BaseModel):
    nombre: str = ""
    email: str = ""
    telefono: str = ""
    ciudad: str = ""


class Experiencia(BaseModel):
    cargo: str = ""
    empresa: str = ""
    periodo: str = ""
    descripcion: str = ""


class Educacion(BaseModel):
    titulo: str = ""
    institucion: str = ""
    anio: str = ""


class PerfilHV(BaseModel):
    contacto: Contacto = Field(default_factory=Contacto)
    resumen: str = ""
    experiencia: list[Experiencia] = Field(default_factory=list)
    educacion: list[Educacion] = Field(default_factory=list)
    habilidades: list[str] = Field(default_factory=list)
    idiomas: list[str] = Field(default_factory=list)


def perfil_vacio():
    return PerfilHV().model_dump()
