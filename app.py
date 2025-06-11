import streamlit as st
from supabase import create_client
import pandas as pd

# Configuración de conexión a Supabase
url = "https://emgqseferyrvnqekdbcm.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVtZ3FzZWZlcnlydm5xZWtkYmNtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk1NTU4MjEsImV4cCI6MjA2NTEzMTgyMX0.58IeQ-nZKn8UWEnV2Fdo0asB1eOGOFNkmxVd6ln0158"
supabase = create_client(url, key)

# Título de la app
st.title("Catálogo de Productos")

# Leer productos desde Supabase
data = supabase.table("productos").select("*").execute()
productos = pd.DataFrame(data.data)

# Filtros
filtro_nombre = st.text_input("Buscar por nombre")
filtro_categoria = st.selectbox("Filtrar por subcategoría", [""] + sorted(productos["Subcategoría"].dropna().unique()))

# Aplicar filtros
if filtro_nombre:
    productos = productos[productos["Nombre"].str.contains(filtro_nombre, case=False, na=False)]
if filtro_categoria:
    productos = productos[productos["Subcategoría"] == filtro_categoria]

# Mostrar productos
for _, row in productos.iterrows():
    st.markdown("---")
    col1, col2 = st.columns([1, 3])
    with col1:
        if row["URL Foto"]:
            st.image(row["URL Foto"], width=150)
        else:
            st.text("Sin imagen")
    with col2:
        st.subheader(row["Nombre"])
        st.write(f"**Referencia:** {row['Referencia']}")
        st.write(f"**Precio:** {row['PVP1']} €")
        st.write(f"**Subcategoría:** {row.get('Subcategoría', 'N/A')}")
