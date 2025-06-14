import streamlit as st
from supabase import create_client
import pandas as pd
from fpdf import FPDF
import requests
from PIL import Image
from io import BytesIO
import tempfile
import os
from datetime import datetime

# Configuración Supabase
url = "https://emgqseferyrvnqekdbcm.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVtZ3FzZWZlcnlydm5xZWtkYmNtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk1NTU4MjEsImV4cCI6MjA2NTEzMTgyMX0.58IeQ-nZKn8UWEnV2Fdo0asB1eOGOFNkmxVd6ln0158"
supabase = create_client(url, key)

st.set_page_config(layout="wide")
st.title("Catálogo de productos")

# Inicializar carrito
if "carrito" not in st.session_state:
    st.session_state.carrito = {}

# Cargar productos y clientes
productos_df = pd.DataFrame(supabase.table("productos").select("*").execute().data)
clientes_df = pd.DataFrame(supabase.table("clientes").select("*").execute().data)

# Filtros
familia_sel = st.selectbox("Selecciona una familia", [""] + sorted(productos_df["Familia"].dropna().unique()))
if familia_sel:
    productos_df = productos_df[productos_df["Familia"] == familia_sel]

subfamilia_sel = st.selectbox("Selecciona una subfamilia", [""] + sorted(productos_df["Subfamilia"].dropna().unique()))
if subfamilia_sel:
    productos_df = productos_df[productos_df["Subfamilia"] == subfamilia_sel]

# Mostrar productos
st.markdown(f"### Resultados: {len(productos_df)} producto(s) encontrado(s)")
for _, row in productos_df.iterrows():
    with st.container():
        cols = st.columns([1, 3, 1])
        with cols[0]:
            st.image(row["URL Foto"], width=150) if row.get("URL Foto") else st.text("Sin imagen")
        with cols[1]:
            st.subheader(row.get("Nombre", ""))
            st.write(f"**Referencia:** {row.get('Referencia', '')}")
            st.write(f"**Precio:** {row.get('PVP1', '')} EUR")
            st.write(f"**Descripción:** {row.get('Descripcion Web', '')}")
        with cols[2]:
            if st.button("🛒 Añadir al carrito", key=row["Referencia"]):
                ref = row["Referencia"]
                if ref in st.session_state.carrito:
                    st.session_state.carrito[ref]["cantidad"] += 1
                else:
                    st.session_state.carrito[ref] = {
                        "nombre": row["Nombre"],
                        "precio": row["PVP1"],
                        "cantidad": 1
                    }
                st.success(f"{row['Nombre']} añadido al carrito.")

# Mostrar carrito
st.markdown("## 🛍️ Carrito de compra")
total = 0
if st.session_state.carrito:
    to_remove = []
    for ref, item in st.session_state.carrito.items():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        with col1:
            st.write(f"🔹 **{item['nombre']}**")
        with col2:
            item["cantidad"] = st.number_input("Cantidad", min_value=1, value=item["cantidad"], key=f"qty_{ref}")
        with col3:
            subtotal = item["precio"] * item["cantidad"]
            total += subtotal
            st.write(f"{subtotal:.2f} EUR")
        with col4:
            if st.button("❌", key=f"del_{ref}"):
                to_remove.append(ref)
    for ref in to_remove:
        st.session_state.carrito.pop(ref)
    st.markdown(f"### 💰 Total del pedido: {total:.2f} EUR")
else:
    st.info("Tu carrito está vacío.")

# Selección de cliente
st.markdown("## 👤 Selecciona un cliente")
clientes_nombres = [f"{c['nombre']} - {c['identificador_fiscal']}" for _, c in clientes_df.iterrows()]
cliente_sel = st.selectbox("Cliente", clientes_nombres)
cliente_id = clientes_df.iloc[clientes_nombres.index(cliente_sel)]["id"]

# Confirmar pedido
if st.session_state.carrito and cliente_id:
    if st.button("✅ Confirmar pedido"):
        # Insertar en tabla pedidos
        pedido_res = supabase.table("pedidos").insert({
            "cliente_id": cliente_id,
            "total": total
        }).execute()

        if pedido_res.data:
            pedido_id = pedido_res.data[0]["id"]
            # Insertar líneas de pedido
            for ref, item in st.session_state.carrito.items():
                supabase.table("lineas_pedido").insert({
                    "pedido_id": pedido_id,
                    "producto_id": ref,
                    "cantidad": item["cantidad"],
                    "precio_unitario": item["precio"]
                }).execute()

            st.success("✅ Pedido guardado correctamente.")
            st.session_state.carrito = {}  # Vaciar carrito

            # Generar PDF del pedido
            class PDF(FPDF):
                def header(self):
                    try:
                        logo_path = os.path.join(os.path.dirname(__file__), "Logo_Cabecera.png")
                        self.image(logo_path, x=10, y=8, w=40)
                    except:
                        pass
                    self.set_font("Arial", "B", 12)
                    self.cell(0, 10, "Andorralife - Pedido confirmado", ln=True, align="R")
                    self.ln(10)

                def footer(self):
                    self.set_y(-15)
                    self.set_font("Arial", "I", 8)
                    self.cell(0, 10, f'Página {self.page_no()}', align='C')

            pdf = PDF()
            pdf.add_page()
            pdf.set_font("Arial", "", 12)
            cliente = clientes_df[clientes_df["id"] == cliente_id].iloc[0]
            pdf.cell(0, 10, f"Cliente: {cliente['nombre']}", ln=True)
            pdf.cell(0, 10, f"NIF: {cliente['identificador_fiscal']}", ln=True)
            pdf.cell(0, 10, f"Dirección: {cliente['direccion']}", ln=True)
            pdf.cell(0, 10, f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
            pdf.ln(10)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(80, 10, "Producto", 1)
            pdf.cell(30, 10, "Cantidad", 1)
            pdf.cell(40, 10, "Precio U.", 1)
            pdf.cell(40, 10, "Subtotal", 1)
            pdf.ln()

            pdf.set_font("Arial", "", 11)
            for ref, item in st.session_state.carrito.items():
                subtotal = item["cantidad"] * item["precio"]
                pdf.cell(80, 10, item["nombre"][:30], 1)
                pdf.cell(30, 10, str(item["cantidad"]), 1)
                pdf.cell(40, 10, f"{item['precio']:.2f} EUR", 1)
                pdf.cell(40, 10, f"{subtotal:.2f} EUR", 1)
                pdf.ln()

            pdf.set_font("Arial", "B", 12)
            pdf.cell(150, 10, "Total", 1)
            pdf.cell(40, 10, f"{total:.2f} EUR", 1)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
                pdf.output(f.name)
                with open(f.name, "rb") as file:
                    st.download_button("⬇️ Descargar PDF del pedido", file.read(), file_name="pedido.pdf", mime="application/pdf")
        else:
            st.error("Error al guardar el pedido.")
