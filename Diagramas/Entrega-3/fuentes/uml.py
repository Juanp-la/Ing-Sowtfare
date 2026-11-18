"""Genera diagramas UML de clases con Graphviz (cajas de 3 compartimentos)."""
import html
import subprocess
import sys


def clase(nombre, atributos=(), metodos=(), estereotipo="", color="#EEF3FB", sprint3=False):
    borde = "#C0392B" if sprint3 else "#2F5597"
    fondo = "#FDEDEC" if sprint3 else color
    filas = []
    cab = (f'<FONT POINT-SIZE="9"><I>«{html.escape(estereotipo)}»</I></FONT><BR/>' if estereotipo else "")
    nombre_fmt = f"<I>{html.escape(nombre)}</I>" if estereotipo in ("abstract", "interface") else html.escape(nombre)
    filas.append(f'<TR><TD BGCOLOR="{fondo}">{cab}<B>{nombre_fmt}</B></TD></TR>')
    def bloque(items):
        if not items:
            return '<TR><TD> </TD></TR>'
        return '<TR><TD ALIGN="LEFT" BALIGN="LEFT">' + "<BR/>".join(html.escape(i) for i in items) + "</TD></TR>"
    filas.append(bloque(atributos))
    filas.append(bloque(metodos))
    return (f'"{nombre}" [shape=plain, label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" '
            f'COLOR="{borde}"><TR><TD><TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="3" COLOR="{borde}">'
            + "".join(filas) + "</TABLE></TD></TR></TABLE>>];")


def render(nombre, cuerpo, rankdir="BT", extra=""):
    dot = f'''digraph G {{
  rankdir={rankdir}; splines=ortho; nodesep=0.35; ranksep=0.55; fontname="Helvetica"; {extra}
  node [fontname="Helvetica", fontsize=10]; edge [fontname="Helvetica", fontsize=9, color="#333333"];
{cuerpo}
}}'''
    open(f"{nombre}.dot", "w").write(dot)
    subprocess.run(["dot", "-Tpng", "-Gdpi=170", f"{nombre}.dot", "-o", f"{nombre}.png"], check=True)
