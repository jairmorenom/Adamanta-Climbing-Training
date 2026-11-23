import streamlit as st
import pandas as pd


# ======================================
# CONFIGURACIÓN
# ======================================

st.set_page_config(
    page_title="Adamanta Training",
    page_icon="🧗",
    layout="wide"
)


# ======================================
# DATOS DE PRUEBA
# ======================================

datos = pd.DataFrame({
    "Alumno": ["Emi", "Juan Cruz", "Marina"],
    "Volumen %": [83.3, 83.3, 83.3],
    "RPE planificado": [6.3, 6.3, 6.3],
    "RPE real": [7.0, 7.0, 6.0],
    "Carga %": [92.1, 92.1, 78.9],
    "Nivel": [
        "MONITOREAR",
        "MONITOREAR",
        "MONITOREAR"
    ],
    "Estado": [
        "Volumen ligeramente bajo",
        "Volumen ligeramente bajo",
        "Volumen ligeramente bajo | Carga ligeramente baja"
    ],
    "Recomendación": [
        "Subir ligeramente el volumen en la próxima sesión",
        "Subir ligeramente el volumen en la próxima sesión",
        "Subir ligeramente el volumen en la próxima sesión"
    ]
})


# ======================================
# SIDEBAR
# ======================================

st.sidebar.title("ADAMANTA")

pagina = st.sidebar.radio(
    "Navegación",
    [
        "Inicio",
        "Planear sesión",
        "Registrar sesión",
        "Seguimiento",
        "Alertas"
    ]
)


# ======================================
# INICIO
# ======================================

if pagina == "Inicio":

    st.title("ADAMANTA")
    st.subheader(
        "Sistema de planificación y seguimiento de entrenamiento"
    )

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Bloque actual", "4")
    col2.metric("Semana", "47")
    col3.metric("Sesiones / semana", "4")
    col4.metric("Alumnos activos", len(datos))

    st.divider()

    st.subheader("Resumen del grupo")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Volumen medio",
        f"{datos['Volumen %'].mean():.1f}%"
    )

    col2.metric(
        "RPE medio",
        f"{datos['RPE real'].mean():.1f}"
    )

    col3.metric(
        "Carga media",
        f"{datos['Carga %'].mean():.1f}%"
    )

    st.subheader("Estado actual")

    st.dataframe(
        datos[
            [
                "Alumno",
                "Volumen %",
                "RPE real",
                "Carga %",
                "Nivel"
            ]
        ],
        use_container_width=True
    )


# ======================================
# PLANEAR SESIÓN
# ======================================

elif pagina == "Planear sesión":

    st.title("Planear sesión")

    col1, col2 = st.columns(2)

    with col1:

        semana = st.selectbox(
            "Semana",
            list(range(1, 53)),
            index=46
        )

    with col2:

        sesion = st.selectbox(
            "Sesión",
            [1, 2, 3, 4]
        )


    if semana <= 13:
        bloque = 1

    elif semana <= 26:
        bloque = 2

    elif semana <= 39:
        bloque = 3

    else:
        bloque = 4


    st.info(
        f"Bloque {bloque} · Semana {semana} · Sesión {sesion}"
    )


    tipos = [
        "Corrección de técnica",
        "Habilidades técnicas",
        "Coordinación",
        "Proyección",
        "Flash or Trash",
        "Movilidad aplicada",
        "Dinámicos",
        "Endurance técnico"
    ]

    tipo = st.selectbox(
        "Tipo de sesión",
        tipos
    )


    ejercicios = [
        "Pies silenciosos",
        "Talones + empeines",
        "Cambios de pies",
        "Centro de masas",
        "Movimiento aislado → secuencia"
    ]


    seleccion = st.multiselect(
        "Selecciona ejercicios",
        ejercicios
    )


    if seleccion:

        st.subheader("Ejercicios seleccionados")

        for ejercicio in seleccion:

            st.write(
                f"• {ejercicio}"
            )


# ======================================
# REGISTRAR SESIÓN
# ======================================

elif pagina == "Registrar sesión":

    st.title("Registrar sesión")

    alumnos = datos["Alumno"].tolist()

    presentes = st.multiselect(
        "Alumnos presentes",
        alumnos,
        default=alumnos
    )

    st.divider()

    resultados = []

    for alumno in presentes:

        st.subheader(alumno)

        col1, col2 = st.columns(2)

        with col1:

            volumen = st.number_input(
                "Volumen real",
                min_value=0,
                max_value=2000,
                value=80,
                key=f"vol_{alumno}"
            )

        with col2:

            rpe = st.slider(
                "RPE real",
                1,
                10,
                6,
                key=f"rpe_{alumno}"
            )


        resultados.append({
            "Alumno": alumno,
            "Volumen": volumen,
            "RPE": rpe,
            "Carga": volumen * rpe
        })


    if st.button("Guardar sesión"):

        st.success(
            "Sesión registrada correctamente."
        )

        st.dataframe(
            pd.DataFrame(resultados),
            use_container_width=True
        )


# ======================================
# SEGUIMIENTO
# ======================================

elif pagina == "Seguimiento":

    st.title("Seguimiento por bloque")

    alumno = st.selectbox(
        "Selecciona alumno",
        datos["Alumno"]
    )

    datos_alumno = datos[
        datos["Alumno"] == alumno
    ].iloc[0]


    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Volumen",
        f"{datos_alumno['Volumen %']}%"
    )

    col2.metric(
        "RPE real",
        datos_alumno["RPE real"]
    )

    col3.metric(
        "Carga",
        f"{datos_alumno['Carga %']}%"
    )


    # Datos simulados de tendencia
    tendencia = pd.DataFrame({
        "Semana": [44, 45, 46, 47],
        "Volumen": [88, 91, 86, datos_alumno["Volumen %"]],
        "Carga": [95, 97, 90, datos_alumno["Carga %"]]
    })


    st.subheader("Volumen semanal")

    st.line_chart(
        tendencia.set_index("Semana")["Volumen"]
    )


    st.subheader("Carga semanal")

    st.line_chart(
        tendencia.set_index("Semana")["Carga"]
    )


# ======================================
# ALERTAS
# ======================================

elif pagina == "Alertas":

    st.title("Alertas y recomendaciones")

    for _, fila in datos.iterrows():

        with st.expander(
            f"{fila['Alumno']} · {fila['Nivel']}"
        ):

            st.write(
                f"**Volumen:** {fila['Volumen %']}%"
            )

            st.write(
                f"**RPE planificado:** {fila['RPE planificado']}"
            )

            st.write(
                f"**RPE real:** {fila['RPE real']}"
            )

            st.write(
                f"**Carga:** {fila['Carga %']}%"
            )

            st.write(
                f"**Estado:** {fila['Estado']}"
            )

            st.info(
                f"Recomendación: {fila['Recomendación']}"
            )
