"""HU18 - Consultar el estado de mis postulaciones (criterios derivados, por validar con el PO)."""
import pytest

from apps.postulaciones import servicios
from core.models import Postulacion
from core.pruebas.fabricas import crear_usuario

pytestmark = pytest.mark.django_db


@pytest.fixture
def postulaciones(candidato_magneto, hv_demo, vacantes_demo, magneto):
    return [servicios.postular(candidato_magneto, v, perfil=hv_demo.perfil, cliente=magneto) for v in vacantes_demo[:3]]


def test_ca1_veo_la_lista_de_mis_postulaciones_con_su_estado(cliente_autenticado, postulaciones):
    postulaciones[1].estado = Postulacion.Estado.EN_REVISION
    postulaciones[1].save()
    html = cliente_autenticado.get("/postulaciones/").content.decode()
    assert html.count('class="fila-postulacion"') == 3 and "En revisión" in html and "Enviada" in html
    assert "Enviada: 2" in html and "En revisión: 1" in html


def test_ca2_puedo_filtrar_por_estado(cliente_autenticado, postulaciones):
    postulaciones[0].estado = Postulacion.Estado.NO_APTO
    postulaciones[0].save()
    html = cliente_autenticado.get("/postulaciones/?estado=no_apto").content.decode()
    assert html.count('class="fila-postulacion"') == 1 and postulaciones[0].vacante.titulo in html


def test_ca3_el_detalle_muestra_el_seguimiento_y_la_retroalimentacion(cliente_autenticado, postulaciones):
    p = postulaciones[0]
    p.estado, p.comentario_reclutador = Postulacion.Estado.NO_APTO, "Buscamos más experiencia."
    p.retroalimentacion = [{"requisito": "ITIL", "sugerencia": "Haz un curso de ITIL."}]
    p.save()
    html = cliente_autenticado.get(f"/postulaciones/{p.pk}/").content.decode()
    assert 'id="seguimiento"' in html and "Buscamos más experiencia." in html and "Haz un curso de ITIL." in html
    assert "Ver mi plan de mejora" in html


def test_ca4_puedo_retirar_una_postulacion_abierta(cliente_autenticado, postulaciones):
    p = postulaciones[0]
    assert "Sí, retirar" in cliente_autenticado.get(f"/postulaciones/{p.pk}/retirar/").content.decode()
    cliente_autenticado.post(f"/postulaciones/{p.pk}/retirar/")
    assert not Postulacion.objects.filter(pk=p.pk).exists()


def test_ca5_no_se_retira_una_postulacion_ya_decidida(cliente_autenticado, postulaciones):
    p = postulaciones[0]
    p.estado = Postulacion.Estado.APTO
    p.save()
    html = cliente_autenticado.post(f"/postulaciones/{p.pk}/retirar/", follow=True).content.decode()
    assert Postulacion.objects.filter(pk=p.pk).exists() and "no se puede retirar" in html


def test_ca6_solo_veo_mis_postulaciones(client, postulaciones):
    client.force_login(crear_usuario())
    assert client.get(f"/postulaciones/{postulaciones[0].pk}/").status_code == 404
    assert 'class="fila-postulacion"' not in client.get("/postulaciones/").content.decode()


def test_sin_postulaciones_ofrece_buscar_vacantes(cliente_autenticado):
    html = cliente_autenticado.get("/postulaciones/").content.decode()
    assert "No tienes postulaciones" in html and "/vacantes/" in html
