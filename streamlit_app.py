import streamlit as st
import pandas as pd
import random


# ======================================
# CONFIGURACIÓN GENERAL
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
# BASE DE EJERCICIOS
# ======================================

ejercicios_por_bloque = {

    # ==================================
    # BLOQUE 1
    # ==================================

    1: {

        "Corrección de técnica": [
            "Pies silenciosos",
            "Talones + empeines",
            "Cambios de pies",
            "Centro de masas / dirección corporal",
            "Movimiento dinámico aislado → secuencia"
        ],

        "Habilidades técnicas": [
            "Puntas + precisión",
            "Talón / empeine aplicado",
            "Cruces + rotación de cadera",
            "Pies altos + movilidad aplicada",
            "Combinación de habilidades"
        ],

        "Coordinación": [
            "Cambio de pies + ritmo",
            "Coordinación mano-pie",
            "Deadpoint controlado",
            "Secuencia dinámica de pies",
            "Coordinación combinada"
        ],

        "Proyección": [
            "Proyecto corto técnico",
            "Trabajo por secciones",
            "Proyecto en desplome",
            "Beta limitada",
            "Proyecto completo"
        ],

        "Flash or Trash": [
            "Flash or Trash clásico",
            "Visualización + ejecución",
            "Flash por estilos",
            "Intentos limitados",
            "Flash bajo presión"
        ],

        "Movilidad aplicada": [
            "Pies altos",
            "Apertura de cadera",
            "Cruces amplios",
            "Movilidad en slab",
            "Secuencia de movilidad combinada"
        ],

        "Dinámicos": [
            "Deadpoint a una mano",
            "Salto controlado",
            "Coordinación de pies dinámica",
            "Doble movimiento",
            "Secuencia dinámica combinada"
        ],

        "Volumen / Endurance técnico": [
            "Circuito de volumen técnico",
            "Travesía continua",
            "Boulders encadenados",
            "Endurance por estilos",
            "Secuencia larga en spray wall"
        ]
    },


    # ==================================
    # BLOQUE 2
    # ==================================

    2: {

        "Volumen técnico": [
            "Circuito de boulders por estilos",
            "Volumen progresivo",
            "Travesía técnica larga",
            "Boulders encadenados",
            "Volumen en spray wall"
        ],

        "Fuerza general aplicada": [
            "Tracción + core en muro",
            "Boulders de tensión corporal",
            "Fuerza de piernas aplicada",
            "Movimientos largos controlados",
            "Circuito de fuerza general"
        ],

        "Coordinación": [
            "Coordinación mano-pie",
            "Cambios de pies con ritmo",
            "Secuencias cruzadas",
            "Coordinación en desplome",
            "Coordinación combinada en spray wall"
        ],

        "Dinámicos / potencia": [
            "Deadpoint potente",
            "Salto a dos manos",
            "Dyno con coordinación de pies",
            "Movimientos largos explosivos",
            "Secuencia dinámica combinada"
        ],

        "Habilidades técnicas": [
            "Puntas + precisión",
            "Talón + empeine aplicados",
            "Cruces + rotación de cadera",
            "Pies altos + cambios de dirección",
            "Combinación técnica en spray wall"
        ],

        "Endurance / Power endurance técnico": [
            "4×4 técnico",
            "Travesía por tiempo",
            "Boulders encadenados",
            "Secuencia larga en spray wall",
            "Endurance por estilos"
        ],

        "Corrección de técnica": [
            "Pies silenciosos",
            "Corrección de talón / empeine",
            "Centro de masas",
            "Corrección de secuencia",
            "Mismo boulder, nueva beta"
        ],

        "Movilidad aplicada": [
            "Pies altos + apertura de cadera",
            "Movilidad en slab",
            "Cruces amplios",
            "Rotaciones + cambio de dirección",
            "Secuencia de movilidad combinada"
        ]
    },


    # ==================================
    # BLOQUE 3
    # ==================================

    3: {

        "Flash or Trash": [
            "Flash or Trash clásico",
            "Flash por estilos",
            "Visualización completa",
            "Beta después del fallo",
            "Flash bajo presión"
        ],

        "Simulación de competencia": [
            "Mini ronda 4 boulders",
            "Ronda por estilos",
            "Simulación con aislamiento",
            "Intentos con tiempo",
            "Final 4×4 adaptada"
        ],

        "Coordinación": [
            "Coordinación de pies",
            "Mano-pie avanzada",
            "Cambios de ritmo",
            "Coordinación en desplome",
            "Secuencia combinada"
        ],

        "Habilidades técnicas": [
            "Talón + empeine avanzado",
            "Cruces y rotaciones",
            "Pies altos complejos",
            "Cambio de dirección",
            "Combinación técnica avanzada"
        ],

        "Corrección de técnica": [
            "Video + corrección",
            "Movimiento aislado",
            "Dos betas diferentes",
            "Corrección bajo fatiga",
            "Coach observa, atleta analiza"
        ],

        "Dinámicos": [
            "Deadpoint avanzado",
            "Dyno con pies",
            "Doble coordinación",
            "Dinámico con cambio de dirección",
            "Secuencia dinámica competitiva"
        ],

        "Proyección": [
            "Proyecto competitivo",
            "Crux primero",
            "Proyecto con intentos limitados",
            "Proyecto por secciones",
            "Proyecto completo con análisis"
        ],

        "Endurance técnico": [
            "Boulders consecutivos",
            "Travesía técnica",
            "Circuito competitivo",
            "Secuencia larga",
            "Calidad bajo fatiga"
        ],

        "Movilidad aplicada": [
            "Pies altos competitivos",
            "Apertura de cadera en posiciones complejas",
            "Cruces amplios + rotación",
            "Movilidad en slab técnico",
            "Secuencia combinada de movilidad"
        ]
    },


    # ==================================
    # BLOQUE 4
    # ==================================

    4: {

        "Simulación de competencia": [
            "Ronda 4 boulders",
            "Final 4×4 adaptada",
            "Simulación con aislamiento",
            "Competencia por estilos",
            "Ronda con estrategia"
        ],

        "Corrección de técnica": [
            "Video + corrección",
            "Error aislado",
            "Comparación de betas",
            "Corrección en roca simulada",
            "Autocorrección"
        ],

        "Proyección": [
            "Proyecto estilo roca",
            "Crux primero",
            "Proyecto por secciones",
            "Intentos limitados",
            "Proyecto completo"
        ],

        "Flash or Trash": [
            "Flash competitivo",
            "Flash estilo roca",
            "Flash por estilos",
            "Beta después del fallo",
            "Un intento"
        ],

        "Habilidades técnicas": [
            "Talones y empeines complejos",
            "Pies pequeños",
            "Rotaciones y banderas",
            "Compresión",
            "Combinación estilo roca"
        ],

        "Coordinación": [
            "Mano-pie",
            "Cambios rápidos de pies",
            "Cambio de ritmo",
            "Coordinación en desplome",
            "Secuencia combinada"
        ],

        "Dinámicos": [
            "Deadpoint",
            "Dyno controlado",
            "Doble movimiento",
            "Dinámico lateral",
            "Secuencia dinámica"
        ],

        "Endurance técnico": [
            "Boulders consecutivos",
            "Travesía estilo roca",
            "Secuencia larga",
            "Endurance por estilos",
            "Calidad bajo fatiga"
        ],

        "Movilidad aplicada": [
            "Pies altos",
            "Apertura de cadera",
            "Cruces amplios",
            "Slab de movilidad",
            "Movilidad estilo roca"
        ]
    }
}


# ======================================
# FUNCIÓN PARA OBTENER BLOQUE
# ======================================

def obtener_bloque(semana):

    if 1 <= semana <= 13:
        return 1, "Proyección en piedra"

    elif 14 <= semana <= 26:
        return 2, "Volumen, fuerza e hipertrofia"

    elif 27 <= semana <= 39:
        return 3, "Técnica avanzada + transición a competencia"

    else:
        return 4, "Competencia + transición a roca"


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

    col1.metric(
        "Bloque actual",
        "4"
    )

    col2.metric(
        "Semana",
        "47"
    )

    col3.metric(
        "Sesiones / semana",
        "4"
    )

    col4.metric(
        "Alumnos activos",
        len(datos)
    )

    st.divider()

    st.subheader(
        "Resumen del grupo"
    )

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

    st.divider()

    st.subheader(
        "Estado actual"
    )

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

    st.title(
        "Planear sesión"
    )

    st.caption(
        "Selecciona la semana y la sesión para construir "
        "el entrenamiento del día."
    )

    # --------------------------------------
    # SEMANA Y SESIÓN
    # --------------------------------------

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


    # --------------------------------------
    # BLOQUE
    # --------------------------------------

    bloque, nombre_bloque = obtener_bloque(
        semana
    )

    st.info(
        f"Bloque {bloque} · "
        f"{nombre_bloque} · "
        f"Semana {semana} · "
        f"Sesión {sesion}"
    )


    # --------------------------------------
    # TIPO DE SESIÓN
    # --------------------------------------

    tipos_disponibles = list(
        ejercicios_por_bloque[
            bloque
        ].keys()
    )

    tipo_sesion = st.selectbox(
        "Tipo de sesión",
        tipos_disponibles
    )


    # --------------------------------------
    # EJERCICIOS
    # --------------------------------------

    ejercicios_disponibles = (
        ejercicios_por_bloque[
            bloque
        ][tipo_sesion]
    )

    st.divider()

    st.subheader(
        "Selección de ejercicios"
    )


    # --------------------------------------
    # CANTIDAD
    # --------------------------------------

    cantidad = st.slider(
        "¿Cuántos ejercicios quieres realizar?",
        min_value=1,
        max_value=5,
        value=3
    )


    # --------------------------------------
    # MODO
    # --------------------------------------

    modo = st.radio(
        "Modo de selección",
        [
            "Manual",
            "Aleatorio"
        ],
        horizontal=True
    )


    # --------------------------------------
    # MANUAL
    # --------------------------------------

    if modo == "Manual":

        seleccion = st.multiselect(
            "Selecciona los ejercicios",
            ejercicios_disponibles,
            max_selections=cantidad
        )


    # --------------------------------------
    # ALEATORIO
    # --------------------------------------

    else:

        if st.button(
            "Generar ejercicios aleatorios",
            use_container_width=True
        ):

            st.session_state[
                "ejercicios_aleatorios"
            ] = random.sample(
                ejercicios_disponibles,
                k=cantidad
            )

        seleccion = st.session_state.get(
            "ejercicios_aleatorios",
            []
        )


    # --------------------------------------
    # MOSTRAR PLAN
    # --------------------------------------

    if seleccion:

        st.divider()

        st.subheader(
            "Plan de la sesión"
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Bloque",
            bloque
        )

        col2.metric(
            "Semana",
            semana
        )

        col3.metric(
            "Sesión",
            sesion
        )

        st.write(
            f"**Tipo:** {tipo_sesion}"
        )

        st.write(
            "**Ejercicios seleccionados:**"
        )

        for i, ejercicio in enumerate(
            seleccion,
            1
        ):

            st.success(
                f"{i}. {ejercicio}"
            )

        if len(seleccion) < cantidad:

            st.warning(
                f"Seleccionaste "
                f"{len(seleccion)} "
                f"de {cantidad} ejercicios."
            )

        else:

            st.success(
                "Sesión lista para utilizar."
            )


# ======================================
# REGISTRAR SESIÓN
# ======================================

elif pagina == "Registrar sesión":

    st.title(
        "Registrar sesión"
    )

    semana = st.selectbox(
        "Semana",
        list(range(1, 53)),
        index=46,
        key="registro_semana"
    )

    sesion = st.selectbox(
        "Sesión",
        [1, 2, 3, 4],
        key="registro_sesion"
    )

    alumnos = datos[
        "Alumno"
    ].tolist()

    presentes = st.multiselect(
        "Alumnos presentes",
        alumnos,
        default=alumnos
    )

    st.divider()

    resultados = []

    for alumno in presentes:

        st.subheader(
            alumno
        )

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
            "Semana": semana,
            "Sesión": sesion,
            "Alumno": alumno,
            "Volumen": volumen,
            "RPE": rpe,
            "Carga": volumen * rpe
        })


    if st.button(
        "Guardar sesión",
        use_container_width=True
    ):

        st.success(
            "Sesión registrada correctamente."
        )

        st.dataframe(
            pd.DataFrame(
                resultados
            ),
            use_container_width=True
        )


# ======================================
# SEGUIMIENTO
# ======================================

elif pagina == "Seguimiento":

    st.title(
        "Seguimiento por bloque"
    )

    bloque_analisis = st.selectbox(
        "Bloque",
        [1, 2, 3, 4],
        index=3
    )

    alumno = st.selectbox(
        "Selecciona alumno",
        datos["Alumno"]
    )

    datos_alumno = datos[
        datos["Alumno"] == alumno
    ].iloc[0]


    # --------------------------------------
    # MÉTRICAS
    # --------------------------------------

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


    # --------------------------------------
    # TENDENCIA SIMULADA
    # --------------------------------------

    tendencia = pd.DataFrame({
        "Semana": [
            44,
            45,
            46,
            47
        ],

        "Volumen": [
            88,
            91,
            86,
            datos_alumno[
                "Volumen %"
            ]
        ],

        "Carga": [
            95,
            97,
            90,
            datos_alumno[
                "Carga %"
            ]
        ],

        "RPE": [
            6.0,
            6.5,
            6.4,
            datos_alumno[
                "RPE real"
            ]
        ]
    })


    st.divider()

    st.subheader(
        "Volumen semanal"
    )

    st.line_chart(
        tendencia.set_index(
            "Semana"
        )["Volumen"]
    )


    st.subheader(
        "Carga semanal"
    )

    st.line_chart(
        tendencia.set_index(
            "Semana"
        )["Carga"]
    )


    st.subheader(
        "RPE semanal"
    )

    st.line_chart(
        tendencia.set_index(
            "Semana"
        )["RPE"]
    )


# ======================================
# ALERTAS
# ======================================

elif pagina == "Alertas":

    st.title(
        "Alertas y recomendaciones"
    )

    st.caption(
        "Seguimiento automático del volumen, "
        "RPE y carga por alumno."
    )

    st.divider()

    for _, fila in datos.iterrows():

        with st.expander(
            f"{fila['Alumno']} · "
            f"{fila['Nivel']}"
        ):

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Volumen",
                f"{fila['Volumen %']}%"
            )

            col2.metric(
                "RPE",
                fila["RPE real"],
                delta=round(
                    fila["RPE real"]
                    - fila[
                        "RPE planificado"
                    ],
                    1
                )
            )

            col3.metric(
                "Carga",
                f"{fila['Carga %']}%"
            )

            st.write(
                f"**Estado:** "
                f"{fila['Estado']}"
            )

            st.info(
                f"Recomendación: "
                f"{fila['Recomendación']}"
            )
