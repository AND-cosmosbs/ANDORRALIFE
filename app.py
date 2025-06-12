import streamlit as st
from supabase import create_client
import pandas as pd
from fpdf import FPDF
import requests
from PIL import Image
from io import BytesIO
import tempfile
import os

# Configuración Supabase
url = "https://emgqseferyrvnqekdbcm.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVtZ3FzZWZlcnlydm5xZWtkYmNtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk1NTU4MjEsImV4cCI6MjA2NTEzMTgyMX0.58IeQ-nZKn8UWEnV2Fdo0asB1eOGOFNkmxVd6ln0158"
supabase = create_client(url, key)

st.set_page_config(layout="wide")
st.title("Catálogo de productos")

# Cargar datos desde Supabase
data = supabase.table("productos").select("*").execute()
productos = pd.DataFrame(data.data)

# Obtener valores únicos de 'Familia' (el filtro)
familias = productos["Familia"].dropna().unique().tolist()
familia_sel = st.selectbox("Selecciona una familia", [""] + sorted(familias))

# Filtrar si hay selección
if familia_sel:
    productos = productos[productos["Familia"] == familia_sel]

# Mostrar resultados
st.markdown(f"### Resultados: {len(productos)} producto(s) encontrado(s)")

for _, row in productos.iterrows():
    with st.container():
        cols = st.columns([1, 3])
        with cols[0]:
            if row.get("URL Foto"):
                st.image(row["URL Foto"], width=150)
            else:
                st.text("Sin imagen")
        with cols[1]:
            st.subheader(row.get("Nombre", ""))
            st.write(f"**Referencia:** {row.get('Referencia', '')}")
            st.write(f"**Precio:** {row.get('PVP1', '')} €")
            st.write(f"**Descripción:** {row.get('Descripcion Web', '')}")

# Función para generar PDF
def generar_pdf(df, familia):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Catálogo de productos - {familia}", ln=True)

    for _, row in df.iterrows():
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, row.get("Nombre", ""), ln=True)

        # Insertar imagen
        if row.get("URL Foto"):
            try:
                response = requests.get(row["URL Foto"])
                img = Image.open(BytesIO(response.content))
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    img.save(tmp.name)
                    pdf.image(tmp.name, w=50)
                    os.unlink(tmp.name)
            except Exception:
                pass

        # Info del producto
        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(0, 8, f"Referencia: {row.get('Referencia', '')}")
        pdf.multi_cell(0, 8, f"Precio: {row.get('PVP1', '')} €")
        descripcion = row.get("Descripcion Web", "")
        if descripcion:
            pdf.multi_cell(0, 8, f"Descripción: {descripcion}")
        pdf.ln(5)

    return pdf

# Botón para generar PDF
if not productos.empty:
    if st.button("📄 Generar PDF del catálogo"):
        titulo = familia_sel if familia_sel else "completo"
        pdf = generar_pdf(productos, titulo)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            pdf.output(f.name)
            with open(f.name, "rb") as file:
                st.download_button(
                    "⬇️ Descargar catálogo PDF",
                    file.read(),
                    file_name=f"catalogo_{titulo}.pdf",
                    mime="application/pdf"
                )
