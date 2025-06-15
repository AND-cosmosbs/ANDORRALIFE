import streamlit as st
import pandas as pd
import requests
from fpdf import FPDF
from io import BytesIO
from PIL import Image
from datetime import datetime

# Configuración de conexión
SUPABASE_URL = "https://emgqseferyrvnqekdbcm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVtZ3FzZWZlcnlydm5xZWtkYmNtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk1NTU4MjEsImV4cCI6MjA2NTEzMTgyMX0.58IeQ-nZKn8UWEnV2Fdo0asB1eOGOFNkmxVd6ln0158"
HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}

# Cargar datos de productos y clientes
@st.cache_data(ttl=600)
def cargar_tabla(nombre_tabla):
    url = f"{SUPABASE_URL}/rest/v1/{nombre_tabla}?select=*"
    r = requests.get(url, headers=HEADERS)
    return pd.DataFrame(r.json())

df_productos = cargar_tabla("productos")
df_clientes = cargar_tabla("clientes")

# Carrito en estado de sesión
if "carrito" not in st.session_state:
    st.session_state.carrito = []

# Filtro por familia
familia_sel = st.selectbox("Filtrar por familia:", sorted(df_productos["Familia"].dropna().unique()))
productos_filtrados = df_productos[df_productos["Familia"] == familia_sel]

st.title(f"Catálogo de productos: {familia_sel}")

# Mostrar productos con botón de añadir al carrito
for _, row in productos_filtrados.iterrows():
    with st.container():
        cols = st.columns([1, 3, 1])
        with cols[0]:
            if row["URL Foto"]:
                st.image(row["URL Foto"], width=100)
        with cols[1]:
            st.markdown(f"**{row['Nombre']}**")
            st.markdown(f"Ref: `{row['Referencia']}`")
            st.markdown(f"{row.get('Descripcion Web', '')}")
            st.markdown(f"**Precio:** {row.get('PVP1', '')} €")
        with cols[2]:
            if st.button(f"➕ Añadir {row['Referencia']}", key=row['Referencia']):
                st.session_state.carrito.append({"ref": row["Referencia"], "nombre": row["Nombre"], "precio": row["PVP1"], "url": row["URL Foto"]})

# Mostrar carrito actual
st.subheader("🛒 Carrito")
if st.session_state.carrito:
    carrito_df = pd.DataFrame(st.session_state.carrito)
    st.dataframe(carrito_df)

    # Selección de cliente
    cliente_sel = st.selectbox("Seleccionar cliente:", df_clientes["nombre"].dropna().unique())
    datos_cliente = df_clientes[df_clientes["nombre"] == cliente_sel].iloc[0]

    # Botón para generar factura
    if st.button("📄 Generar albarán/factura simple"):
        pdf = FPDF()
        pdf.add_page()

        try:
            pdf.image("Logo_Cabecera.png", x=10, y=8, w=40)
        except:
            pass

        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Factura Simplificada", ln=True, align="C")
        pdf.ln(10)

        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Cliente: {datos_cliente['nombre']} - CIF: {datos_cliente['identificador_fiscal']}", ln=True)
        pdf.cell(0, 10, f"Fecha: {datetime.now().strftime('%Y-%m-%d')}", ln=True)
        pdf.ln(5)

        total = 0
        for item in st.session_state.carrito:
            pdf.cell(0, 8, f"{item['ref']} - {item['nombre']} - {item['precio']} €", ln=True)
            total += float(item["precio"]) if item["precio"] else 0

        pdf.ln(5)
        pdf.cell(0, 10, f"TOTAL: {round(total, 2)} €", ln=True)

        buffer = BytesIO()
        pdf.output(buffer)
        st.download_button("⬇️ Descargar PDF de la factura", data=buffer.getvalue(), file_name="factura.pdf", mime="application/pdf")
else:
    st.info("Añade productos al carrito para continuar.")
