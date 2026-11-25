"""
Mapa de posicionamiento INTERACTIVO (al pasar el ratón por un círculo
aparecen la marca, el precio y la especialización).

Uso:
    pip install pandas openpyxl plotly
    python main.py "/ruta/a/tu_archivo.xlsx"

Genera mapa_posicionamiento.html, que se abre con doble clic en el navegador.
El Excel debe tener tres columnas: Marca | Precio | Especialización
Si no pasas archivo, usa los datos de ejemplo.
"""
import sys
import pandas as pd
import plotly.graph_objects as go

# ---------- Ajustes ----------
MARCA_DESTACADA = "Babaria"
CORTE_X = 20
CORTE_Y = 2.5
X_MAX = 40
Y_MAX = 5
FECHA_PRECIOS = "24/11/2026"   # revisa la fecha
TITULO_RESTO = " es la opción más barata entre los sérums de alta especialización"
SUBTITULO = "Mapa de posicionamiento de seis sérums faciales"
COLOR_ACENTO = "#B8860B"
COLOR_PUNTOS = "#9A9A9A"
COLOR_TEXTO = "#555555"
COLOR_EJES = "#6B6B6B"
SALIDA = "mapa_posicionamiento.html"
SALIDA_PNG = "mapa_posicionamiento.png"
NIVELES = {1: "baja", 2: "media", 3: "alta"}

# ---------- Datos ----------
if len(sys.argv) > 1:
    df = pd.read_excel(sys.argv[1]).iloc[:, :3]
    df.columns = ["Marca", "Precio", "Especializacion"]
    df = df.dropna(subset=["Marca", "Precio", "Especializacion"])
    df["Precio"] = (df["Precio"].astype(str)
                    .str.replace("€", "", regex=False)
                    .str.replace(",", ".", regex=False)
                    .str.strip().astype(float))
else:
    df = pd.DataFrame({
        "Marca": ["Babaria", "L'Oréal", "Biovène", "La Roche-Posay", "Garnier", "The Ordinary"],
        "Precio": [5.74, 23.90, 6.95, 36.46, 13.35, 14.63],
        "Especializacion": [3, 3, 1, 2, 2, 3],
    })

df["Marca"] = df["Marca"].astype(str).str.strip()
df["Especializacion"] = df["Especializacion"].astype(float)
dest = df["Marca"].str.lower() == MARCA_DESTACADA.strip().lower()

def eur(x):
    return f"{x:.2f}".replace(".", ",") + " €"

df["hover"] = df.apply(
    lambda r: f"<b>{r['Marca']}</b><br>Precio por 30 ml: {eur(r['Precio'])}"
              f"<br>Especialización: {NIVELES.get(int(r['Especializacion']), '')} "
              f"({int(r['Especializacion'])}/3)", axis=1)

fig = go.Figure()

# Zona de interés (precio bajo + especialización alta)
fig.add_shape(type="rect", x0=0, x1=CORTE_X, y0=CORTE_Y, y1=Y_MAX,
              fillcolor=COLOR_ACENTO, opacity=0.07, line_width=0, layer="below")
# Ejes cruzados
fig.add_shape(type="line", x0=CORTE_X, x1=CORTE_X, y0=0, y1=Y_MAX,
              line=dict(color=COLOR_EJES, width=1.5))
fig.add_shape(type="line", x0=0, x1=X_MAX, y0=CORTE_Y, y1=CORTE_Y,
              line=dict(color=COLOR_EJES, width=1.5))

# Puntos: grises primero, destacada después (para que quede encima)
for mask, color, size, bold in [(~dest, COLOR_PUNTOS, 16, False), (dest, COLOR_ACENTO, 26, True)]:
    sub = df[mask]
    if sub.empty:
        continue
    fig.add_trace(go.Scatter(
        x=sub["Precio"], y=sub["Especializacion"], mode="markers+text",
        text=[f"<b>{m}</b>" if bold else m for m in sub["Marca"]],
        # La destacada lleva la etiqueta a la derecha para que la línea de la
        # anotación (que llega desde arriba a la izquierda) no la atraviese
        textposition="middle right" if bold else "top center",
        textfont=dict(color=color if bold else COLOR_TEXTO, size=16 if bold else 13),
        marker=dict(color=color, size=size),
        # El recuadro nativo de Plotly sale al lado del círculo y tapa los nombres;
        # se desactiva y se dibuja uno propio debajo del círculo (ver HOVER_JS)
        hoverinfo="none",
        customdata=[[h, color, size] for h in sub["hover"]],
        showlegend=False))

# Textos fijos: extremos, cuadrantes, anotación, título y pie
def txt(x, y, t, size=11, color=COLOR_TEXTO, xanchor="center", yanchor="middle",
        xref="x", yref="y", **kw):
    fig.add_annotation(x=x, y=y, text=t, showarrow=False, xref=xref, yref=yref,
                       xanchor=xanchor, yanchor=yanchor,
                       font=dict(size=size, color=color), **kw)

txt(0.5, 1.02, "ESPECIALIZACIÓN (+)", xref="paper", yref="paper", yanchor="bottom")
txt(0.5, -0.02, "ESPECIALIZACIÓN (−)", xref="paper", yref="paper", yanchor="top")
txt(-0.01, CORTE_Y / Y_MAX, "PRECIO (−)", xref="paper", yref="paper", xanchor="right")
txt(1.01, CORTE_Y / Y_MAX, "PRECIO (+)", xref="paper", yref="paper", xanchor="left")

q = dict(size=10, color="#A6A6A6")
txt(0.4, Y_MAX - 0.15, "Precio bajo · especialización alta", xanchor="left", yanchor="top", **q)
txt(X_MAX - 0.4, Y_MAX - 0.15, "Precio alto · especialización alta", xanchor="right", yanchor="top", **q)
txt(0.4, 0.15, "Precio bajo · especialización baja", xanchor="left", yanchor="bottom", **q)
txt(X_MAX - 0.4, 0.15, "Precio alto · especialización baja", xanchor="right", yanchor="bottom", **q)

if dest.any():
    b = df[dest].iloc[0]
    mismos = df[(df["Especializacion"] == b["Especializacion"]) & (df["Precio"] > b["Precio"])]
    if not mismos.empty:
        rival = mismos.sort_values("Precio", ascending=False).iloc[0]
        veces = f'{rival["Precio"] / b["Precio"]:.1f}'.replace(".", ",")
        fig.add_annotation(
            x=b["Precio"], y=b["Especializacion"], ax=0.8, ay=Y_MAX - 0.55,
            axref="x", ayref="y", xref="x", yref="y",
            text=(f"<b>{eur(b['Precio'])}</b><br>{veces} veces más barata que {rival['Marca']},"
                  f"<br>con la misma especialización"),
            showarrow=True, arrowhead=0, arrowwidth=0.8, arrowcolor=COLOR_ACENTO,
            standoff=14, align="left", xanchor="left", yanchor="top",
            font=dict(size=13, color=COLOR_ACENTO))

fig.update_layout(
    font=dict(family="Arial, Helvetica, sans-serif"),   # una sola fuente para todo el gráfico
    hoverlabel=dict(font_family="Arial, Helvetica, sans-serif"),
    title=dict(
        text=(f"<b><span style='color:{COLOR_ACENTO}'>{MARCA_DESTACADA}</span>{TITULO_RESTO}</b>"
              f"<br><span style='font-size:14px;color:#666666;font-weight:normal'>{SUBTITULO}</span>"),
        x=0.03, xanchor="left", font=dict(size=22, color="#222222")),
    xaxis=dict(range=[0, X_MAX], visible=False, fixedrange=True),
    yaxis=dict(range=[0, Y_MAX], visible=False, fixedrange=True),
    plot_bgcolor="white", paper_bgcolor="white",
    margin=dict(l=90, r=90, t=135, b=100), width=1000, height=765,
    annotations=list(fig.layout.annotations) + [dict(
        text=(f"Precio equivalente a 30 ml, consultado el {FECHA_PRECIOS} a precio habitual (sin promociones). "
              "Especialización (1-3) según los beneficios declarados por cada marca."
              "<br>Pasa el ratón por un círculo para ver el precio de cada marca."),
        align="left", yanchor="top",
        # Misma posición izquierda que el título (30 px del borde), pasada a
        # coordenadas del área del gráfico: (30 - margen izq.) / ancho del área
        x=(0.03 * 1000 - 90) / (1000 - 90 - 90), y=-0.1, xref="paper", yref="paper", showarrow=False,
        xanchor="left", font=dict(size=11, color="#777777"))])

# Recuadro al pasar el ratón: aparece DEBAJO del círculo, así no tapa el nombre
# de la marca (que está encima, o a la derecha en la destacada)
HOVER_JS = """
var gd = document.getElementById('{plot_id}');
var base = gd.layout.annotations.length;
gd.on('plotly_hover', function (ev) {
  var p = ev.points[0], d = p.customdata;
  var upd = {};
  upd['annotations[' + base + ']'] = {
    x: p.x, y: p.y, xref: 'x', yref: 'y', showarrow: false,
    xanchor: 'center', yanchor: 'top', yshift: -(d[2] / 2 + 8),
    text: d[0], align: 'left', bgcolor: 'white', bordercolor: d[1],
    borderwidth: 1, borderpad: 6,
    font: {family: 'Arial, Helvetica, sans-serif', size: 13, color: '#222222'}
  };
  Plotly.relayout(gd, upd);
});
gd.on('plotly_unhover', function () {
  var upd = {};
  upd['annotations[' + base + ']'] = null;
  Plotly.relayout(gd, upd);
});
"""

fig.write_html(SALIDA, include_plotlyjs="cdn", config={"displayModeBar": False},
               post_script=HOVER_JS)
print("Guardado:", SALIDA)
# Versión en imagen (para presentaciones o PDF). En una imagen no hay ratón,
# así que se quita esa línea de la nota del pie.
nota = fig.layout.annotations[-1]
nota.text = nota.text.split("<br>Pasa el ratón")[0]
fig.write_image(SALIDA_PNG, scale=2)
print("Guardado:", SALIDA_PNG)
