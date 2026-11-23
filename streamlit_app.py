import streamlit as st
import pandas as pd
import random
import urllib.parse
import matplotlib.pyplot as plt


# =========================================================
# CONFIGURACIÓN
# =========================================================

st.set_page_config(
    page_title="Adamanta Training",
    page_icon="🧗",
    layout="wide"
)


# =========================================================
# GOOGLE SHEET
# =========================================================
# Pega aquí el ID de tu Google Sheet.
#
# Ejemplo:
# https://docs.google.com/spreadsheets/d/ABC123XYZ/edit
#
# SPREADSHEET_ID = "ABC123XYZ"

SPREADSHEET_ID = "1liLy4wqzh5-dx6TCAN7XF62Jx7TYfusbPwftT0B9kjA"


# =========================================================
# NOMBRES DE HOJAS
# =========================================================

HOJAS_EJERCICIOS = {
    1: "Lista de ejercicios Bloque 1",
    2: "Lista de ejercicios bloque 2",
    3: "Lista de ejercicios bloque 3",
    4: "Lista de ejercicios bloque 4",
}

HOJAS_CARGA = {
    1: "Carga de ejercicios Bloque 1",
    2: "Carga de ejercicios Bloque 2",
    3: "Carga de ejercicios Bloque 3",
    4: "Carga de ejercicios Bloque 4",
}


# =========================================================
# FUNCIONES GOOGLE SHEETS
# =========================================================

@st.cache_data(ttl=60)
def leer_hoja(nombre_hoja):

    nombre_codificado = urllib.parse.quote(
        nombre_hoja
    )

    url = (
        f"https://docs.google.com/spreadsheets/d/"
        f"{SPREADSHEET_ID}/gviz/tq?"
        f"tqx=out:csv&sheet={nombre_codificado}"
    )

    df = pd.read_csv(url)

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    return df


def obtener_bloque(semana):

    if 1 <= semana <= 13:
        return 1, "Proyección en piedra"

    elif 14 <= semana <= 26:
        return 2, "Volumen, fuerza e hipertrofia"

    elif 27 <= semana <= 39:
        return 3, "Técnica avanzada + transición a competencia"

    else:
        return 4, "Competencia + transición a roca"


def limpiar_texto(valor):

    if pd.isna(valor):
        return ""

    return str(valor).strip()


# =========================================================
# LEER DATOS PRINCIPALES
# =========================================================

try:

    df_distribucion = leer_hoja(
        "Distribucion semanal"
    )

    df_alumnos = leer_hoja(
        "Alumnos"
    )

    conexion_ok = True

except Exception as error:

    conexion_ok = False

    st.error(
        "No se pudo leer la base de datos."
    )

    st.code(str(error))

    st.info(
        "Revisa que el Google Sheet esté compartido como "
        "'Cualquier persona con el enlace → Lector' y que "
        "SPREADSHEET_ID sea correcto."
    )


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("ADAMANTA")

if conexion_ok:

    st.sidebar.success(
        "Base de datos conectada"
    )

else:

    st.sidebar.error(
        "Sin conexión"
    )


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


# =========================================================
# DETENER SI NO HAY CONEXIÓN
# =========================================================

if not conexion_ok:

    st.stop()


# =========================================================
# LIMPIAR DISTRIBUCIÓN SEMANAL
# =========================================================

df_distribucion["Semana"] = pd.to_numeric(
    df_distribucion["Semana"],
    errors="coerce"
)


# =========================================================
# LISTA DE ALUMNOS
# =========================================================

if "Nombre" in df_alumnos.columns:

    alumnos = (
        df_alumnos["Nombre"]
        .dropna()
        .astype(str)
        .str.strip()
        .tolist()
    )

else:

    alumnos = (
        df_alumnos.iloc[:, 0]
        .dropna()
        .astype(str)
        .str.strip()
        .tolist()
    )


# =========================================================
# INICIO
# =========================================================

if pagina == "Inicio":

    st.title("ADAMANTA")

    st.subheader(
        "Sistema de planificación y seguimiento"
    )

    st.caption(
        "Planificación · Carga · Seguimiento · Alertas"
    )

    st.divider()


    # -----------------------------------------------------
    # DATOS GENERALES
    # -----------------------------------------------------

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Semanas programadas",
        52
    )

    col2.metric(
        "Sesiones por semana",
        4
    )

    col3.metric(
        "Alumnos",
        len(alumnos)
    )


    st.divider()

    st.subheader(
        "Alumnos"
    )

    if alumnos:

        df_lista_alumnos = pd.DataFrame({
            "Alumno": alumnos
        })

        st.dataframe(
            df_lista_alumnos,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.warning(
            "No hay alumnos registrados."
        )


# =========================================================
# PLANEAR SESIÓN
# =========================================================

elif pagina == "Planear sesión":

    st.title(
        "Planear sesión"
    )

    st.caption(
        "La programación se obtiene directamente "
        "de la base de datos."
    )


    # -----------------------------------------------------
    # SEMANA Y SESIÓN
    # -----------------------------------------------------

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


    bloque, nombre_bloque = obtener_bloque(
        semana
    )


    # -----------------------------------------------------
    # TIPO DE SESIÓN AUTOMÁTICO
    # -----------------------------------------------------

    fila_semana = df_distribucion[
        df_distribucion["Semana"] == semana
    ]

    columna_sesion = (
        f"Sesión {sesion}"
    )


    if (
        fila_semana.empty
        or columna_sesion not in df_distribucion.columns
    ):

        st.error(
            "No se encontró la sesión programada."
        )

        st.stop()


    tipo_sesion = limpiar_texto(
        fila_semana.iloc[0][
            columna_sesion
        ]
    )


    st.info(
        f"Bloque {bloque} · "
        f"{nombre_bloque} · "
        f"Semana {semana} · "
        f"Sesión {sesion}"
    )


    st.metric(
        "Tipo de sesión",
        tipo_sesion
    )


    # =====================================================
    # LEER LISTA REAL DE EJERCICIOS
    # =====================================================

    df_lista = leer_hoja(
        HOJAS_EJERCICIOS[bloque]
    )


    # -----------------------------------------------------
    # BUSCAR FILA DEL TIPO DE SESIÓN
    # -----------------------------------------------------

    primera_columna = (
        df_lista.columns[0]
    )

    coincidencia = df_lista[
        df_lista[
            primera_columna
        ]
        .astype(str)
        .str.strip()
        .str.lower()
        ==
        tipo_sesion.lower()
    ]


    ejercicios = []


    # -----------------------------------------------------
    # FORMATO NORMAL
    # -----------------------------------------------------

    if not coincidencia.empty:

        indice = coincidencia.index[0]

        fila = df_lista.loc[indice]

        for columna in df_lista.columns[1:6]:

            nombre = limpiar_texto(
                fila[columna]
            )

            if (
                nombre
                and not nombre.lower().startswith(
                    "opción"
                )
            ):

                ejercicios.append(
                    nombre
                )


    # -----------------------------------------------------
    # FORMATO CON FILA "OPCIÓN 1..."
    # -----------------------------------------------------

    if not ejercicios:

        for i in range(
            len(df_lista)
        ):

            valor = limpiar_texto(
                df_lista.iloc[i, 0]
            )

            if (
                valor.lower()
                == tipo_sesion.lower()
            ):

                if i + 1 < len(
                    df_lista
                ):

                    fila_siguiente = (
                        df_lista.iloc[
                            i + 1
                        ]
                    )

                    for valor_ejercicio in (
                        fila_siguiente.iloc[
                            1:6
                        ]
                    ):

                        ejercicio = limpiar_texto(
                            valor_ejercicio
                        )

                        if ejercicio:

                            ejercicios.append(
                                ejercicio
                            )

                break


    if not ejercicios:

        st.error(
            f"No se encontraron ejercicios para "
            f"{tipo_sesion}."
        )

        st.stop()


    # =====================================================
    # SELECCIÓN DE EJERCICIOS
    # =====================================================

    st.divider()

    st.subheader(
        "Ejercicios"
    )


    cantidad = st.slider(
        "Cantidad de ejercicios",
        1,
        min(
            5,
            len(ejercicios)
        ),
        min(
            3,
            len(ejercicios)
        )
    )


    modo = st.radio(
        "Modo de selección",
        [
            "Manual",
            "Aleatorio"
        ],
        horizontal=True
    )


    # -----------------------------------------------------
    # MANUAL
    # -----------------------------------------------------

    if modo == "Manual":

        seleccion = st.multiselect(
            "Selecciona los ejercicios",
            ejercicios,
            max_selections=cantidad
        )


    # -----------------------------------------------------
    # ALEATORIO
    # -----------------------------------------------------

    else:

        clave = (
            f"aleatorio_"
            f"{bloque}_"
            f"{semana}_"
            f"{sesion}_"
            f"{tipo_sesion}_"
            f"{cantidad}"
        )

        if st.button(
            "Generar selección",
            use_container_width=True
        ):

            st.session_state[
                clave
            ] = random.sample(
                ejercicios,
                cantidad
            )

        seleccion = (
            st.session_state.get(
                clave,
                []
            )
        )


    # =====================================================
    # CARGA REAL DESDE GOOGLE SHEETS
    # =====================================================

    if seleccion:

        st.divider()

        df_carga = leer_hoja(
            HOJAS_CARGA[bloque]
        )


        columnas_numericas = [
            "Series/Boulders",
            "Movimientos",
            "Vueltas",
            "RPE objetivo",
            "Descanso min"
        ]


        for columna in columnas_numericas:

            if columna in df_carga.columns:

                df_carga[
                    columna
                ] = pd.to_numeric(
                    df_carga[
                        columna
                    ],
                    errors="coerce"
                )


        if all(
            columna in df_carga.columns
            for columna in [
                "Series/Boulders",
                "Movimientos",
                "Vueltas"
            ]
        ):

            df_carga[
                "Volumen"
            ] = (
                df_carga[
                    "Series/Boulders"
                ]
                *
                df_carga[
                    "Movimientos"
                ]
                *
                df_carga[
                    "Vueltas"
                ]
            )


        filas_plan = []


        for ejercicio in seleccion:

            coincidencia_carga = (
                df_carga[
                    df_carga[
                        "Ejercicio"
                    ]
                    .astype(str)
                    .str.strip()
                    .str.lower()
                    ==
                    ejercicio.lower()
                ]
            )


            if coincidencia_carga.empty:

                filas_plan.append({
                    "Ejercicio": ejercicio,
                    "Series/Boulders": None,
                    "Movimientos": None,
                    "Vueltas": None,
                    "RPE": None,
                    "Descanso": None,
                    "Volumen": None
                })

                continue


            fila = (
                coincidencia_carga.iloc[
                    0
                ]
            )


            filas_plan.append({
                "Ejercicio":
                    ejercicio,

                "Series/Boulders":
                    fila.get(
                        "Series/Boulders"
                    ),

                "Movimientos":
                    fila.get(
                        "Movimientos"
                    ),

                "Vueltas":
                    fila.get(
                        "Vueltas"
                    ),

                "RPE":
                    fila.get(
                        "RPE objetivo"
                    ),

                "Descanso":
                    fila.get(
                        "Descanso min"
                    ),

                "Volumen":
                    fila.get(
                        "Volumen"
                    )
            })


        df_plan = pd.DataFrame(
            filas_plan
        )


        # =================================================
        # MOSTRAR PLAN
        # =================================================

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
            f"**Tipo:** "
            f"{tipo_sesion}"
        )


        st.dataframe(
            df_plan,
            use_container_width=True,
            hide_index=True
        )


        # =================================================
        # RESUMEN DE CARGA
        # =================================================

        volumen_total = pd.to_numeric(
            df_plan[
                "Volumen"
            ],
            errors="coerce"
        ).sum()


        rpe_medio = pd.to_numeric(
            df_plan[
                "RPE"
            ],
            errors="coerce"
        ).mean()


        if pd.isna(
            rpe_medio
        ):

            rpe_medio = 0


        carga_planificada = (
            volumen_total
            *
            rpe_medio
        )


        st.divider()

        col1, col2, col3 = (
            st.columns(3)
        )


        col1.metric(
            "Volumen planificado",
            f"{volumen_total:.0f}"
        )


        col2.metric(
            "RPE objetivo",
            f"{rpe_medio:.1f}"
        )


        col3.metric(
            "Carga planificada",
            f"{carga_planificada:.0f}"
        )


        # -------------------------------------------------
        # GUARDAR TEMPORALMENTE LA SESIÓN
        # -------------------------------------------------

        if len(
            seleccion
        ) == cantidad:

            st.session_state[
                "sesion_planificada"
            ] = {
                "Semana":
                    semana,

                "Sesión":
                    sesion,

                "Bloque":
                    bloque,

                "Tipo":
                    tipo_sesion,

                "Ejercicios":
                    seleccion,

                "Volumen":
                    float(
                        volumen_total
                    ),

                "RPE":
                    float(
                        rpe_medio
                    ),

                "Carga":
                    float(
                        carga_planificada
                    )
            }


            st.success(
                "Sesión lista."
            )


# =========================================================
# REGISTRAR SESIÓN
# =========================================================

elif pagina == "Registrar sesión":

    st.title(
        "Registrar sesión"
    )


    plan = st.session_state.get(
        "sesion_planificada"
    )


    if not plan:

        st.warning(
            "Primero crea una sesión en "
            "'Planear sesión'."
        )

        st.stop()


    st.info(
        f"Semana {plan['Semana']} · "
        f"Sesión {plan['Sesión']} · "
        f"{plan['Tipo']}"
    )


    col1, col2, col3 = (
        st.columns(3)
    )


    col1.metric(
        "Volumen planificado",
        f"{plan['Volumen']:.0f}"
    )


    col2.metric(
        "RPE objetivo",
        f"{plan['RPE']:.1f}"
    )


    col3.metric(
        "Carga planificada",
        f"{plan['Carga']:.0f}"
    )


    presentes = st.multiselect(
        "Alumnos presentes",
        alumnos,
        default=[]
    )


    st.divider()


    resultados = []


    for alumno in presentes:

        st.subheader(
            alumno
        )

        col1, col2 = (
            st.columns(2)
        )


        with col1:

            volumen_real = (
                st.number_input(
                    "Volumen real",
                    min_value=0,
                    max_value=2000,
                    value=int(
                        plan[
                            "Volumen"
                        ]
                    ),
                    key=(
                        f"vol_"
                        f"{alumno}"
                    )
                )
            )


        with col2:

            rpe_real = (
                st.slider(
                    "RPE real",
                    1,
                    10,
                    int(
                        round(
                            plan[
                                "RPE"
                            ]
                        )
                    ),
                    key=(
                        f"rpe_"
                        f"{alumno}"
                    )
                )
            )


        carga_real = (
            volumen_real
            *
            rpe_real
        )


        resultados.append({
            "Alumno":
                alumno,

            "Volumen planificado":
                plan[
                    "Volumen"
                ],

            "Volumen real":
                volumen_real,

            "RPE planificado":
                plan[
                    "RPE"
                ],

            "RPE real":
                rpe_real,

            "Carga planificada":
                plan[
                    "Carga"
                ],

            "Carga real":
                carga_real
        })


    # -----------------------------------------------------
    # POR AHORA NO ESCRIBE AL SHEET
    # -----------------------------------------------------

    if st.button(
        "Procesar sesión",
        use_container_width=True
    ):

        if not resultados:

            st.warning(
                "Selecciona al menos un alumno."
            )

        else:

            df_resultados = (
                pd.DataFrame(
                    resultados
                )
            )


            st.success(
                "Resultados procesados."
            )


            st.dataframe(
                df_resultados,
                use_container_width=True,
                hide_index=True
            )


            st.warning(
                "Esta versión está conectada a Google "
                "Sheets en modo lectura. Todavía no "
                "escribe resultados en la hoja."
            )


# =========================================================
# SEGUIMIENTO
# =========================================================

elif pagina == "Seguimiento":

    st.title(
        "Seguimiento"
    )


    try:

        df_historial = leer_hoja(
            "Historial semanal"
        )

    except Exception:

        st.warning(
            "No se pudo cargar Historial semanal."
        )

        st.stop()


    if df_historial.empty:

        st.info(
            "Todavía no hay historial."
        )

        st.stop()


    columnas_numericas = [
        "Semana",
        "Sesión",
        "Volumen planificado",
        "Volumen real",
        "RPE planificado",
        "RPE real",
        "Carga planificada",
        "Carga real"
    ]


    for columna in columnas_numericas:

        if columna in df_historial.columns:

            df_historial[
                columna
            ] = pd.to_numeric(
                df_historial[
                    columna
                ],
                errors="coerce"
            )


    # -----------------------------------------------------
    # BLOQUE
    # -----------------------------------------------------

    bloque_analisis = st.selectbox(
        "Bloque",
        [1, 2, 3, 4],
        index=3
    )


    rangos = {
        1: (1, 13),
        2: (14, 26),
        3: (27, 39),
        4: (40, 52)
    }


    inicio, fin = (
        rangos[
            bloque_analisis
        ]
    )


    df_bloque = df_historial[
        (
            df_historial[
                "Semana"
            ] >= inicio
        )
        &
        (
            df_historial[
                "Semana"
            ] <= fin
        )
    ].copy()


    if df_bloque.empty:

        st.info(
            "No hay datos registrados "
            "para este bloque."
        )

        st.stop()


    alumno = st.selectbox(
        "Alumno",
        sorted(
            df_bloque[
                "Alumno"
            ]
            .dropna()
            .astype(str)
            .unique()
        )
    )


    df_alumno = df_bloque[
        df_bloque[
            "Alumno"
        ].astype(str)
        ==
        alumno
    ]


    resumen = (
        df_alumno
        .groupby(
            "Semana",
            as_index=False
        )
        .agg({
            "Volumen planificado":
                "sum",

            "Volumen real":
                "sum",

            "RPE planificado":
                "mean",

            "RPE real":
                "mean",

            "Carga planificada":
                "sum",

            "Carga real":
                "sum"
        })
    )


    st.subheader(
        alumno
    )


    col1, col2, col3 = (
        st.columns(3)
    )


    volumen_pct = (
        resumen[
            "Volumen real"
        ].sum()
        /
        resumen[
            "Volumen planificado"
        ].sum()
        * 100
    )


    carga_pct = (
        resumen[
            "Carga real"
        ].sum()
        /
        resumen[
            "Carga planificada"
        ].sum()
        * 100
    )


    rpe_real = (
        resumen[
            "RPE real"
        ].mean()
    )


    col1.metric(
        "Volumen",
        f"{volumen_pct:.1f}%"
    )


    col2.metric(
        "RPE medio",
        f"{rpe_real:.1f}"
    )


    col3.metric(
        "Carga",
        f"{carga_pct:.1f}%"
    )


    # =====================================================
    # GRÁFICAS
    # =====================================================

    st.divider()


    st.subheader(
        "Volumen"
    )

    grafica_volumen = (
        resumen[
            [
                "Semana",
                "Volumen planificado",
                "Volumen real"
            ]
        ]
        .set_index(
            "Semana"
        )
    )

    st.line_chart(
        grafica_volumen
    )


    st.subheader(
        "RPE"
    )

    grafica_rpe = (
        resumen[
            [
                "Semana",
                "RPE planificado",
                "RPE real"
            ]
        ]
        .set_index(
            "Semana"
        )
    )

    st.line_chart(
        grafica_rpe
    )


    st.subheader(
        "Carga"
    )

    grafica_carga = (
        resumen[
            [
                "Semana",
                "Carga planificada",
                "Carga real"
            ]
        ]
        .set_index(
            "Semana"
        )
    )

    st.line_chart(
        grafica_carga
    )


# =========================================================
# ALERTAS
# =========================================================

elif pagina == "Alertas":

    st.title(
        "Alertas y recomendaciones"
    )


    try:

        df_seguimiento = leer_hoja(
            "Seguimiento por bloque"
        )

    except Exception:

        st.warning(
            "No se pudo cargar "
            "'Seguimiento por bloque'."
        )

        st.stop()


    if df_seguimiento.empty:

        st.info(
            "Todavía no hay seguimiento registrado."
        )

        st.stop()


    bloque_alertas = st.selectbox(
        "Bloque",
        [1, 2, 3, 4],
        index=3,
        key="bloque_alertas"
    )


    df_alertas = (
        df_seguimiento[
            pd.to_numeric(
                df_seguimiento[
                    "Bloque"
                ],
                errors="coerce"
            )
            ==
            bloque_alertas
        ]
        .copy()
    )


    if df_alertas.empty:

        st.info(
            "No hay alertas registradas "
            "para este bloque."
        )

        st.stop()


    # -----------------------------------------------------
    # ÚLTIMO REGISTRO POR ALUMNO
    # -----------------------------------------------------

    df_alertas[
        "Semana"
    ] = pd.to_numeric(
        df_alertas[
            "Semana"
        ],
        errors="coerce"
    )


    df_alertas = (
        df_alertas
        .sort_values(
            "Semana"
        )
        .groupby(
            "Alumno",
            as_index=False
        )
        .tail(1)
    )


    for _, fila in df_alertas.iterrows():

        alumno = limpiar_texto(
            fila.get(
                "Alumno"
            )
        )

        nivel = limpiar_texto(
            fila.get(
                "Nivel"
            )
        )


        with st.expander(
            f"{alumno} · {nivel}"
        ):

            col1, col2, col3 = (
                st.columns(3)
            )


            col1.metric(
                "Volumen",
                f"{fila.get('Volumen %', 0)}%"
            )


            col2.metric(
                "RPE real",
                fila.get(
                    "RPE real",
                    "-"
                )
            )


            col3.metric(
                "Carga",
                f"{fila.get('Carga %', 0)}%"
            )


            st.write(
                f"**Estado:** "
                f"{fila.get('Estado', '')}"
            )


            st.info(
                f"Recomendación: "
                f"{fila.get('Recomendación', '')}"
            )
