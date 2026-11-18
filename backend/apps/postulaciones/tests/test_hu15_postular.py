"""HU15 - Postularme a la vacante desde el copiloto (criterios derivados, por validar con el PO)."""
import pytest

from apps.postulaciones import servicios
from core.models import HVAdaptada, Postulacion

pytestmark = pytest.mark.django_db


def test_ca1_desde_el_detalle_de_la_vacante_puedo_postularme(cliente_autenticado, hv_demo, vacante_soporte):
    html = cliente_autenticado.get(f"/vacantes/{vacante_soporte.pk}/?hv={hv_demo.pk}").content.decode()
    assert 'id="btn-postular"' in html and f"/postulaciones/vacante/{vacante_soporte.pk}/" in html


def test_ca2_confirmo_y_la_postulacion_llega_a_magneto(cliente_autenticado, candidato_magneto, hv_demo,
                                                       vacante_soporte, magneto):
    html = cliente_autenticado.get(f"/postulaciones/vacante/{vacante_soporte.pk}/").content.decode()
    assert f'value="perfil-{hv_demo.perfil.pk}" checked' in html
    respuesta = cliente_autenticado.post(f"/postulaciones/vacante/{vacante_soporte.pk}/",
                                         {"hv_enviar": f"perfil-{hv_demo.perfil.pk}"}, follow=True)
    postulacion = Postulacion.objects.get(usuario=candidato_magneto, vacante=vacante_soporte)
    assert magneto.postulaciones == [{"id": postulacion.magneto_id, "candidato": "MAG-T-CAND-1", "vacante": "MAG-V-001"}]
    assert postulacion.estado == Postulacion.Estado.ENVIADA and postulacion.hoja_vida == hv_demo
    assert postulacion.score > 0 and postulacion.cumple and postulacion.perfil_enviado == hv_demo.perfil.datos
    assert postulacion.magneto_id in respuesta.content.decode()


def test_ca3_no_me_puedo_postular_dos_veces(cliente_autenticado, candidato_magneto, hv_demo, vacante_soporte, magneto):
    url = f"/postulaciones/vacante/{vacante_soporte.pk}/"
    cliente_autenticado.post(url, {"hv_enviar": f"perfil-{hv_demo.perfil.pk}"})
    respuesta = cliente_autenticado.get(url, follow=True)
    assert "Ya te postulaste a esta vacante" in respuesta.content.decode()
    with pytest.raises(servicios.YaPostulado):
        servicios.postular(candidato_magneto, vacante_soporte, perfil=hv_demo.perfil, cliente=magneto)
    assert Postulacion.objects.count() == 1 and len(magneto.postulaciones) == 1


def test_ca4_puedo_enviar_la_version_adaptada(cliente_autenticado, candidato_magneto, hv_demo, vacante_soporte, magneto):
    cliente_autenticado.post(f"/adaptacion/vacante/{vacante_soporte.pk}/generar/", {"hv": hv_demo.pk})
    adaptacion = HVAdaptada.objects.get()
    cliente_autenticado.post(f"/adaptacion/{adaptacion.pk}/", {f"decision_{c['id']}": "aprobar" for c in adaptacion.cambios})
    html = cliente_autenticado.get(f"/postulaciones/vacante/{vacante_soporte.pk}/?adaptacion={adaptacion.pk}").content.decode()
    assert f'value="adaptacion-{adaptacion.pk}" checked' in html and "Recomendada" in html
    cliente_autenticado.post(f"/postulaciones/vacante/{vacante_soporte.pk}/", {"hv_enviar": f"adaptacion-{adaptacion.pk}"})
    postulacion = Postulacion.objects.get()
    adaptacion.refresh_from_db()
    assert postulacion.hv_adaptada == adaptacion and postulacion.perfil_enviado == adaptacion.perfil_adaptado


def test_ca5_si_magneto_falla_no_queda_registrada(cliente_autenticado, candidato_magneto, hv_demo, vacante_soporte,
                                                  magneto):
    magneto.fallar_postulacion = True
    html = cliente_autenticado.post(f"/postulaciones/vacante/{vacante_soporte.pk}/",
                                    {"hv_enviar": f"perfil-{hv_demo.perfil.pk}"}).content.decode()
    assert "Magneto no recibió tu postulación" in html and not Postulacion.objects.exists()


def test_ca6_sin_hv_analizada_no_puedo_postularme(cliente_autenticado, vacante_soporte):
    html = cliente_autenticado.get(f"/postulaciones/vacante/{vacante_soporte.pk}/").content.decode()
    assert "Necesitas una hoja de vida analizada para postularte" in html


def test_sin_elegir_hv_se_pide_elegirla(cliente_autenticado, candidato_magneto, hv_demo, vacante_soporte, magneto):
    html = cliente_autenticado.post(f"/postulaciones/vacante/{vacante_soporte.pk}/",
                                    {"hv_enviar": "perfil-999999"}).content.decode()
    assert "Elige la hoja de vida que quieres enviar" in html


def test_vacante_inactiva_no_admite_postulaciones(cliente_autenticado, vacante_soporte):
    vacante_soporte.activa = False
    vacante_soporte.save()
    assert cliente_autenticado.get(f"/postulaciones/vacante/{vacante_soporte.pk}/").status_code == 404


def test_error_del_matcher_impide_postular(candidato_magneto, hv_demo, vacante_soporte, magneto):
    class Falla:
        def ejecutar(self, *a, **k):
            return {"error": "matcher: ValueError"}

    with pytest.raises(servicios.ErrorPostulacion):
        servicios.postular(candidato_magneto, vacante_soporte, perfil=hv_demo.perfil, cliente=magneto, servicio=Falla())
