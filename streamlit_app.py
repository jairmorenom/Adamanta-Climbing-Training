import streamlit as st


# ======================================
# CONFIGURACIÓN DE LA APP
# ======================================

st.set_page_config(
    page_title="Adamanta Training",
    page_icon="🧗",
    layout="wide"
)


# ======================================
# ENCABEZADO
# ======================================

st.title("ADAMANTA")
st.subheader("Sistema de planificación y seguimiento de entrenamiento")

st.divider()


# ======================================
# SELECTORES
# ======================================

col1, col2 = st.columns(2)

with col1:

    semana = st.selectbox(
        "Selecciona la semana",
        list(range(1, 53)),
        index=46
    )

with col2:

    sesion = st.selectbox(
        "Selecciona la sesión",
        [1, 2, 3, 4]
    )


# ======================================
# IDENTIFICAR BLOQUE
# ======================================

if semana <= 13:
    bloque = 1

elif semana <= 26:
    bloque = 2

elif semana <= 39:
    bloque = 3

else:
    bloque = 4


# ======================================
# RESUMEN
# ======================================

st.divider()

st.subheader("Sesión seleccionada")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Semana",
        semana
    )

with col2:
    st.metric(
        "Bloque",
        bloque
    )

with col3:
    st.metric(
        "Sesión",
        sesion
    )


st.success(
    "La aplicación está funcionando correctamente."
)
