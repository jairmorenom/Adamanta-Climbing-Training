import streamlit as st
import pandas as pd
import random
import urllib.parse
import requests


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

st.set_page_config(
    page_title="Adamanta Training",
    page_icon="🧗",
    layout="wide"
)


# =========================================================
# LOGIN CON GOOGLE
# =========================================================

if not st.user.is_logged_in:

    st.title("ADAMANTA")
    st.subheader(
        "Sistema de planificación y seguimiento"
    )

    st.write(
        "Inicia sesión con Google para continuar."
    )

    if st.button(
        "Iniciar sesión con Google",
        type="primary",
        use_container_width=True
    ):
        st.login()

    st.stop()


# =========================================================
# USUARIO
# =========================================================

try:
    nombre_usuario = st.user.name
except Exception:
    nombre_usuario = "Usuario"


# =========================================================
# GOOGLE SHEET
# =========================================================

SPREADSHEET_ID = (
    "1liLy4wqzh5-dx6TCAN7XF62Jx7TYfusbPwftT0B9kjA"
)


# =========================================================
# HOJAS
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
# FUNCIONES GENERALES
# =========================================================

def limpiar_texto(valor):

    if pd.isna(valor):
        return ""

    return str(valor).strip()


def obtener_bloque(semana):

    if 1 <= semana <= 13:

        return (
            1,
            "Proyección en piedra"
        )

    elif 14 <= semana <= 26:

        return (
            2,
            "Volumen, fuerza e hipertrofia"
        )

    elif 27 <= semana <= 39:

        return (
            3,
            "Técnica avanzada + transición a competencia"
        )

    else:

        return (
            4,
            "Competencia + transición a roca"
        )


# =========================================================
# LECTURA PÚBLICA DEL GOOGLE SHEET
# =========================================================

@st.cache_data(ttl=60)
def leer_hoja(nombre_hoja):

    nombre_codificado = urllib.parse.quote(
        nombre_hoja
    )

    url = (
        "https://docs.google.com/spreadsheets/d/"
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


# =========================================================
# ACCESS TOKEN GOOGLE
# =========================================================

def obtener_access_token():

    try:

        return st.user.tokens["access"]

    except Exception:

        st.error(
            "No se encontró el token de Google."
        )

        st.info(
            "Cierra sesión y vuelve a iniciar sesión."
        )

        st.stop()


def api_headers():

    token = obtener_access_token()

    return {
        "Authorization":
            f"Bearer {token}",

        "Content-Type":
            "application/json"
    }


# =========================================================
# GOOGLE SHEETS API
# =========================================================

def sheets_get(rango):

    rango_url = urllib.parse.quote(
        rango,
        safe=""
    )

    url = (
        "https://sheets.googleapis.com/v4/"
        f"spreadsheets/{SPREADSHEET_ID}/"
        f"values/{rango_url}"
    )

    respuesta = requests.get(
        url,
        headers=api_headers(),
        timeout=20
    )


    if respuesta.status_code == 401:

        st.error(
            "La sesión de Google expiró."
        )

        st.info(
            "Cierra sesión y vuelve a entrar."
        )

        st.stop()


    if respuesta.status_code == 403:

        st.error(
            "Tu cuenta no tiene permiso para "
            "modificar esta hoja."
        )

        st.stop()


    respuesta.raise_for_status()

    return respuesta.json().get(
        "values",
        []
    )


def sheets_update(
    rango,
    valores
):

    rango_url = urllib.parse.quote(
        rango,
        safe=""
    )

    url = (
        "https://sheets.googleapis.com/v4/"
        f"spreadsheets/{SPREADSHEET_ID}/"
        f"values/{rango_url}"
        "?valueInputOption=USER_ENTERED"
    )


    respuesta = requests.put(
        url,
        headers=api_headers(),
        json={
            "range": rango,
            "majorDimension": "ROWS",
            "values": valores
        },
        timeout=20
    )


    respuesta.raise_for_status()

    return respuesta.json()


def sheets_append(
    rango,
    valores
):

    rango_url = urllib.parse.quote(
        rango,
        safe=""
    )

    url = (
        "https://sheets.googleapis.com/v4/"
        f"spreadsheets/{SPREADSHEET_ID}/"
        f"values/{rango_url}:append"
        "?valueInputOption=USER_ENTERED"
        "&insertDataOption=INSERT_ROWS"
    )


    respuesta = requests.post(
        url,
        headers=api_headers(),
        json={
            "majorDimension": "ROWS",
            "values": valores
        },
        timeout=20
    )


    respuesta.raise_for_status()

    return respuesta.json()


# =========================================================
# GUARDAR HISTORIAL SEMANAL
# =========================================================

def guardar_historial(
    semana,
    sesion,
    alumno,
    tipo_sesion,
    volumen_planificado,
    volumen_real,
    rpe_planificado,
    rpe_real,
    carga_planificada,
    carga_real
):

    valores = sheets_get(
        "'Historial semanal'!A:J"
    )


    nueva_fila = [

        int(semana),

        int(sesion),

        str(alumno),

        str(tipo_sesion),

        float(
            round(
                volumen_planificado,
                1
            )
        ),

        int(
            volumen_real
        ),

        float(
            round(
                rpe_planificado,
                1
            )
        ),

        int(
            rpe_real
        ),

        float(
            round(
                carga_planificada,
                1
            )
        ),

        float(
            round(
                carga_real,
                1
            )
        )
    ]


    fila_encontrada = None


    # -------------------------------------
    # EVITAR DUPLICADOS
    # Semana + Sesión + Alumno
    # -------------------------------------

    for numero_fila, fila in enumerate(
        valores[1:],
        start=2
    ):

        if len(fila) < 3:
            continue


        try:

            semana_existente = int(
                float(
                    fila[0]
                )
            )

            sesion_existente = int(
                float(
                    fila[1]
                )
            )

        except (
            ValueError,
            TypeError
        ):

            continue


        alumno_existente = (
            str(
                fila[2]
            )
            .strip()
            .lower()
        )


        if (
            semana_existente
            == int(semana)

            and sesion_existente
            == int(sesion)

            and alumno_existente
            == str(alumno)
            .strip()
            .lower()
        ):

            fila_encontrada = (
                numero_fila
            )

            break


    # -------------------------------------
    # ACTUALIZAR
    # -------------------------------------

    if fila_encontrada:

        sheets_update(
            (
                "'Historial semanal'!"
                f"A{fila_encontrada}:"
                f"J{fila_encontrada}"
            ),
            [
                nueva_fila
            ]
        )

        return "actualizado"


    # -------------------------------------
    # NUEVO
    # -------------------------------------

    sheets_append(
        "'Historial semanal'!A:J",
        [
            nueva_fila
        ]
    )

    return "creado"


# =========================================================
# ALERTAS
# =========================================================

def clasificar_estado(
    volumen_pct,
    carga_pct,
    dif_rpe
):

    # ALTA

    if (
        dif_rpe >= 2
        or carga_pct > 120
        or volumen_pct > 120
    ):

        return "ALTA"


    # REVISAR

    if (
        dif_rpe <= -2
        or carga_pct < 70
        or volumen_pct < 70
    ):

        return "REVISAR"


    # MONITOREAR

    if (
        75 <= carga_pct < 85
        or 115 < carga_pct <= 120

        or 75 <= volumen_pct < 85
        or 115 < volumen_pct <= 120

        or 1 <= abs(
            dif_rpe
        ) < 2
    ):

        return "MONITOREAR"


    return "OK"


# =========================================================
# ESTADO
# =========================================================

def generar_estado(
    volumen_pct,
    carga_pct,
    dif_rpe
):

    mensajes = []


    # RPE

    if dif_rpe >= 2:

        mensajes.append(
            "RPE mucho más alto de lo planificado"
        )

    elif dif_rpe >= 1:

        mensajes.append(
            "RPE ligeramente por encima del plan"
        )

    elif dif_rpe <= -2:

        mensajes.append(
            "RPE mucho más bajo de lo planificado"
        )

    elif dif_rpe <= -1:

        mensajes.append(
            "RPE ligeramente por debajo del plan"
        )


    # VOLUMEN

    if volumen_pct < 70:

        mensajes.append(
            "Volumen muy bajo"
        )

    elif volumen_pct < 85:

        mensajes.append(
            "Volumen ligeramente bajo"
        )

    elif volumen_pct > 120:

        mensajes.append(
            "Volumen muy alto"
        )

    elif volumen_pct > 115:

        mensajes.append(
            "Volumen ligeramente alto"
        )


    # CARGA

    if carga_pct < 70:

        mensajes.append(
            "Carga muy baja"
        )

    elif carga_pct < 85:

        mensajes.append(
            "Carga ligeramente baja"
        )

    elif carga_pct > 120:

        mensajes.append(
            "Carga muy alta"
        )

    elif carga_pct > 115:

        mensajes.append(
            "Carga ligeramente alta"
        )


    if not mensajes:

        return "Dentro de rango"


    return " | ".join(
        mensajes
    )


# =========================================================
# RECOMENDACIÓN
# =========================================================

def generar_recomendacion(
    volumen_pct,
    carga_pct,
    dif_rpe
):

    if dif_rpe >= 2:

        if carga_pct > 120:

            return (
                "Reducir carga en la siguiente sesión "
                "y revisar recuperación"
            )


        if volumen_pct < 85:

            return (
                "No aumentar volumen; revisar fatiga "
                "y calidad de ejecución"
            )


        return (
            "Reducir ligeramente intensidad "
            "y monitorear recuperación"
        )


    if carga_pct > 120:

        return (
            "Reducir volumen o intensidad "
            "en la siguiente sesión"
        )


    if volumen_pct > 120:

        return (
            "Reducir volumen y volver "
            "al rango planificado"
        )


    if volumen_pct < 70:

        if dif_rpe >= 1:

            return (
                "No subir volumen todavía; "
                "revisar por qué el esfuerzo fue alto"
            )


        return (
            "Aumentar volumen progresivamente "
            "en la siguiente sesión"
        )


    if carga_pct < 70:

        if dif_rpe <= -1:

            return (
                "Aumentar progresivamente "
                "el estímulo de entrenamiento"
            )


        return (
            "Revisar volumen ejecutado "
            "antes de aumentar intensidad"
        )


    if 75 <= volumen_pct < 85:

        if dif_rpe >= 1:

            return (
                "Mantener volumen por ahora "
                "y monitorear el RPE"
            )


        return (
            "Subir ligeramente el volumen "
            "en la próxima sesión"
        )


    if 75 <= carga_pct < 85:

        if dif_rpe < 0:

            return (
                "Aumentar ligeramente el estímulo "
                "si mantiene buena calidad"
            )


        return (
            "Mantener y observar "
            "la siguiente sesión"
        )


    if 1 <= dif_rpe < 2:

        return (
            "Mantener volumen "
            "y monitorear intensidad"
        )


    if -2 < dif_rpe <= -1:

        return (
            "Considerar aumentar ligeramente "
            "la dificultad"
        )


    return (
        "Mantener planificación actual"
    )


# =========================================================
# ACTUALIZAR SEGUIMIENTO POR BLOQUE
# =========================================================

def actualizar_seguimiento_bloque(
    bloque
):

    # -------------------------------------
    # LEER HISTORIAL
    # -------------------------------------

    valores = sheets_get(
        "'Historial semanal'!A:J"
    )


    if len(valores) <= 1:
        return


    encabezados = valores[0]

    filas = []


    for fila in valores[1:]:

        fila_completa = (
            fila
            + [""] * (
                len(encabezados)
                - len(fila)
            )
        )

        filas.append(
            fila_completa[
                :len(encabezados)
            ]
        )


    df = pd.DataFrame(
        filas,
        columns=encabezados
    )


    # -------------------------------------
    # NUMÉRICOS
    # -------------------------------------

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

        if columna in df.columns:

            df[columna] = pd.to_numeric(
                df[columna],
                errors="coerce"
            )


    # -------------------------------------
    # RANGO DEL BLOQUE
    # -------------------------------------

    rangos = {

        1: (1, 13),
        2: (14, 26),
        3: (27, 39),
        4: (40, 52)

    }


    inicio, fin = (
        rangos[
            bloque
        ]
    )


    df_bloque = df[
        (
            df["Semana"]
            >= inicio
        )
        &
        (
            df["Semana"]
            <= fin
        )
    ].copy()


    # -------------------------------------
    # LIMPIAR
    # -------------------------------------

    df_bloque = (
        df_bloque
        .dropna(
            subset=[
                "Semana",
                "Alumno",

                "Volumen planificado",
                "Volumen real",

                "RPE planificado",
                "RPE real",

                "Carga planificada",
                "Carga real"
            ]
        )
    )


    if df_bloque.empty:
        return


    df_bloque["Alumno"] = (
        df_bloque[
            "Alumno"
        ]
        .astype(str)
        .str.strip()
        .str.title()
    )


    semana_actual = int(
        df_bloque[
            "Semana"
        ].max()
    )


    # -------------------------------------
    # RESUMEN
    # -------------------------------------

    resumen = (
        df_bloque
        .groupby(
            "Alumno",
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


    # -------------------------------------
    # LEER SEGUIMIENTO EXISTENTE
    # -------------------------------------

    seguimiento_existente = (
        sheets_get(
            "'Seguimiento por bloque'!A:K"
        )
    )


    # -------------------------------------
    # CADA ALUMNO
    # -------------------------------------

    for _, fila in resumen.iterrows():

        alumno = (
            fila["Alumno"]
        )


        # VOLUMEN %

        if (
            fila[
                "Volumen planificado"
            ] > 0
        ):

            volumen_pct = (

                fila[
                    "Volumen real"
                ]
                /
                fila[
                    "Volumen planificado"
                ]
                * 100

            )

        else:

            volumen_pct = 0


        # CARGA %

        if (
            fila[
                "Carga planificada"
            ] > 0
        ):

            carga_pct = (

                fila[
                    "Carga real"
                ]
                /
                fila[
                    "Carga planificada"
                ]
                * 100

            )

        else:

            carga_pct = 0


        rpe_plan = float(
            fila[
                "RPE planificado"
            ]
        )


        rpe_real = float(
            fila[
                "RPE real"
            ]
        )


        dif_rpe = (
            rpe_real
            -
            rpe_plan
        )


        # ---------------------------------
        # ALERTAS
        # ---------------------------------

        nivel = (
            clasificar_estado(
                volumen_pct,
                carga_pct,
                dif_rpe
            )
        )


        estado = (
            generar_estado(
                volumen_pct,
                carga_pct,
                dif_rpe
            )
        )


        recomendacion = (
            generar_recomendacion(
                volumen_pct,
                carga_pct,
                dif_rpe
            )
        )


        nueva_fila = [

            int(
                bloque
            ),

            semana_actual,

            alumno,

            round(
                volumen_pct,
                1
            ),

            round(
                rpe_plan,
                1
            ),

            round(
                rpe_real,
                1
            ),

            round(
                dif_rpe,
                1
            ),

            round(
                carga_pct,
                1
            ),

            nivel,

            estado,

            recomendacion
        ]


        # ---------------------------------
        # EVITAR DUPLICADOS
        # Bloque + Semana + Alumno
        # ---------------------------------

        fila_encontrada = None


        for numero_fila, existente in enumerate(
            seguimiento_existente[1:],
            start=2
        ):

            if len(
                existente
            ) < 3:

                continue


            try:

                bloque_existente = int(
                    float(
                        existente[0]
                    )
                )


                semana_existente = int(
                    float(
                        existente[1]
                    )
                )

            except (
                ValueError,
                TypeError
            ):

                continue


            alumno_existente = (

                str(
                    existente[2]
                )
                .strip()
                .lower()

            )


            if (

                bloque_existente
                == int(
                    bloque
                )

                and semana_existente
                == semana_actual

                and alumno_existente
                == alumno
                .strip()
                .lower()

            ):

                fila_encontrada = (
                    numero_fila
                )

                break


        # ---------------------------------
        # ACTUALIZAR
        # ---------------------------------

        if fila_encontrada:

            sheets_update(

                (
                    "'Seguimiento por bloque'!"
                    f"A{fila_encontrada}:"
                    f"K{fila_encontrada}"
                ),

                [
                    nueva_fila
                ]
            )


        # ---------------------------------
        # NUEVO
        # ---------------------------------

        else:

            sheets_append(

                "'Seguimiento por bloque'!A:K",

                [
                    nueva_fila
                ]
            )


            seguimiento_existente.append(
                nueva_fila
            )


# =========================================================
# CARGAR DATOS PRINCIPALES
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


    st.code(
        str(
            error
        )
    )


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title(
    "ADAMANTA"
)


st.sidebar.caption(
    f"👤 {nombre_usuario}"
)


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


if st.sidebar.button(
    "Cerrar sesión",
    use_container_width=True
):

    st.logout()


# =========================================================
# DETENER SI NO HAY CONEXIÓN
# =========================================================

if not conexion_ok:

    st.stop()


# =========================================================
# DISTRIBUCIÓN SEMANAL
# =========================================================

df_distribucion["Semana"] = (
    pd.to_numeric(
        df_distribucion[
            "Semana"
        ],
        errors="coerce"
    )
)


# =========================================================
# ALUMNOS
# =========================================================

if (
    "Nombre"
    in df_alumnos.columns
):

    alumnos = (

        df_alumnos[
            "Nombre"
        ]
        .dropna()
        .astype(str)
        .str.strip()
        .tolist()

    )

else:

    alumnos = (

        df_alumnos
        .iloc[
            :,
            0
        ]
        .dropna()
        .astype(str)
        .str.strip()
        .tolist()

    )


# =========================================================
# INICIO
# =========================================================

if pagina == "Inicio":

    st.title(
        "ADAMANTA"
    )


    st.subheader(
        "Sistema de planificación y seguimiento"
    )


    st.caption(
        "Planificación · Carga · Seguimiento · Alertas"
    )


    st.divider()


    col1, col2, col3 = (
        st.columns(3)
    )


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
        len(
            alumnos
        )
    )


    st.divider()


    st.subheader(
        "Alumnos"
    )


    st.dataframe(

        pd.DataFrame({
            "Alumno":
                alumnos
        }),

        use_container_width=True,

        hide_index=True
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


    # --------------------------------------
    # SEMANA + SESIÓN
    # --------------------------------------

    col1, col2 = (
        st.columns(2)
    )


    with col1:

        semana = st.selectbox(

            "Semana",

            list(
                range(
                    1,
                    53
                )
            ),

            index=46
        )


    with col2:

        sesion = st.selectbox(

            "Sesión",

            [
                1,
                2,
                3,
                4
            ]
        )


    bloque, nombre_bloque = (
        obtener_bloque(
            semana
        )
    )


    # --------------------------------------
    # TIPO AUTOMÁTICO
    # --------------------------------------

    fila_semana = (
        df_distribucion[
            df_distribucion[
                "Semana"
            ]
            == semana
        ]
    )


    columna_sesion = (
        f"Sesión {sesion}"
    )


    if (
        fila_semana.empty
        or columna_sesion
        not in df_distribucion.columns
    ):

        st.error(
            "No se encontró la sesión programada."
        )

        st.stop()


    tipo_sesion = limpiar_texto(

        fila_semana
        .iloc[0][
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


    # --------------------------------------
    # EJERCICIOS
    # --------------------------------------

    df_lista = leer_hoja(
        HOJAS_EJERCICIOS[
            bloque
        ]
    )


    primera_columna = (
        df_lista.columns[
            0
        ]
    )


    coincidencia = (

        df_lista[
            df_lista[
                primera_columna
            ]
            .astype(str)
            .str.strip()
            .str.lower()
            ==
            tipo_sesion.lower()
        ]

    )


    ejercicios = []


    if not coincidencia.empty:

        indice = (
            coincidencia.index[
                0
            ]
        )


        fila = (
            df_lista.loc[
                indice
            ]
        )


        for columna in (
            df_lista.columns[
                1:6
            ]
        ):

            nombre = limpiar_texto(
                fila[
                    columna
                ]
            )


            if (
                nombre
                and not nombre
                .lower()
                .startswith(
                    "opción"
                )
            ):

                ejercicios.append(
                    nombre
                )


    # Formato alternativo

    if not ejercicios:

        for i in range(
            len(
                df_lista
            )
        ):

            valor = limpiar_texto(
                df_lista.iloc[
                    i,
                    0
                ]
            )


            if (
                valor.lower()
                ==
                tipo_sesion.lower()
            ):

                if (
                    i + 1
                    <
                    len(
                        df_lista
                    )
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
            "No se encontraron ejercicios "
            f"para {tipo_sesion}."
        )

        st.stop()


    # --------------------------------------
    # SELECCIÓN
    # --------------------------------------

    st.divider()


    st.subheader(
        "Ejercicios"
    )


    cantidad = st.slider(

        "Cantidad de ejercicios",

        min_value=1,

        max_value=min(
            5,
            len(
                ejercicios
            )
        ),

        value=min(
            3,
            len(
                ejercicios
            )
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


    if modo == "Manual":

        seleccion = st.multiselect(

            "Selecciona los ejercicios",

            ejercicios,

            max_selections=cantidad
        )


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


    # --------------------------------------
    # CARGA
    # --------------------------------------

    if seleccion:

        st.divider()


        df_carga = leer_hoja(
            HOJAS_CARGA[
                bloque
            ]
        )


        columnas_numericas = [

            "Series/Boulders",
            "Movimientos",
            "Vueltas",
            "RPE objetivo",
            "Descanso min"

        ]


        for columna in columnas_numericas:

            if columna in (
                df_carga.columns
            ):

                df_carga[
                    columna
                ] = pd.to_numeric(
                    df_carga[
                        columna
                    ],
                    errors="coerce"
                )


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


            if (
                coincidencia_carga.empty
            ):

                continue


            fila = (
                coincidencia_carga
                .iloc[
                    0
                ]
            )


            filas_plan.append({

                "Ejercicio":
                    ejercicio,

                "Series/Boulders":
                    fila[
                        "Series/Boulders"
                    ],

                "Movimientos":
                    fila[
                        "Movimientos"
                    ],

                "Vueltas":
                    fila[
                        "Vueltas"
                    ],

                "RPE":
                    fila[
                        "RPE objetivo"
                    ],

                "Descanso":
                    fila[
                        "Descanso min"
                    ],

                "Volumen":
                    fila[
                        "Volumen"
                    ]
            })


        df_plan = pd.DataFrame(
            filas_plan
        )


        if df_plan.empty:

            st.warning(
                "No se encontraron datos de carga."
            )

            st.stop()


        st.subheader(
            "Plan de la sesión"
        )


        st.dataframe(

            df_plan,

            use_container_width=True,

            hide_index=True
        )


        volumen_total = (

            pd.to_numeric(
                df_plan[
                    "Volumen"
                ],
                errors="coerce"
            )
            .sum()

        )


        rpe_medio = (

            pd.to_numeric(
                df_plan[
                    "RPE"
                ],
                errors="coerce"
            )
            .mean()

        )


        if pd.isna(
            rpe_medio
        ):

            rpe_medio = 0


        carga_planificada = (

            volumen_total
            *
            rpe_medio

        )


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


        if (
            len(
                seleccion
            )
            ==
            cantidad
        ):

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
                "Sesión lista para registrar."
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
            "Primero crea una sesión "
            "en 'Planear sesión'."
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

                    key=f"vol_{alumno}"
                )
            )


        with col2:

            rpe_inicial = max(
                1,
                min(
                    10,
                    int(
                        round(
                            plan[
                                "RPE"
                            ]
                        )
                    )
                )
            )


            rpe_real = (
                st.slider(

                    "RPE real",

                    1,

                    10,

                    rpe_inicial,

                    key=f"rpe_{alumno}"
                )
            )


        carga_real = (
            volumen_real
            *
            rpe_real
        )


        st.caption(
            f"Carga real: "
            f"{carga_real:.0f}"
        )


        resultados.append({

            "Alumno":
                alumno,

            "Volumen planificado":
                float(
                    plan[
                        "Volumen"
                    ]
                ),

            "Volumen real":
                int(
                    volumen_real
                ),

            "RPE planificado":
                float(
                    plan[
                        "RPE"
                    ]
                ),

            "RPE real":
                int(
                    rpe_real
                ),

            "Carga planificada":
                float(
                    plan[
                        "Carga"
                    ]
                ),

            "Carga real":
                float(
                    carga_real
                )
        })


    # --------------------------------------
    # GUARDAR
    # --------------------------------------

    if st.button(

        "Guardar sesión",

        type="primary",

        use_container_width=True

    ):


        if not resultados:

            st.warning(
                "Selecciona al menos un alumno."
            )


        else:

            guardados = 0
            actualizados = 0
            errores = []


            with st.spinner(
                "Guardando sesión..."
            ):


                # HISTORIAL SEMANAL

                for resultado in resultados:

                    try:

                        accion = guardar_historial(

                            plan[
                                "Semana"
                            ],

                            plan[
                                "Sesión"
                            ],

                            resultado[
                                "Alumno"
                            ],

                            plan[
                                "Tipo"
                            ],

                            resultado[
                                "Volumen planificado"
                            ],

                            resultado[
                                "Volumen real"
                            ],

                            resultado[
                                "RPE planificado"
                            ],

                            resultado[
                                "RPE real"
                            ],

                            resultado[
                                "Carga planificada"
                            ],

                            resultado[
                                "Carga real"
                            ]
                        )


                        if (
                            accion
                            ==
                            "creado"
                        ):

                            guardados += 1

                        else:

                            actualizados += 1


                    except Exception as error:

                        errores.append(

                            f"{resultado['Alumno']}: "
                            f"{str(error)}"

                        )


                # SEGUIMIENTO POR BLOQUE

                if not errores:

                    try:

                        actualizar_seguimiento_bloque(
                            plan[
                                "Bloque"
                            ]
                        )


                    except Exception as error:

                        errores.append(

                            "Seguimiento por bloque: "
                            f"{str(error)}"

                        )


            # ---------------------------------
            # RESULTADO
            # ---------------------------------

            if guardados:

                st.success(
                    f"✅ {guardados} registro(s) "
                    f"nuevos guardados."
                )


            if actualizados:

                st.info(
                    f"🔄 {actualizados} registro(s) "
                    f"actualizados."
                )


            if not errores:

                st.success(
                    "✅ Historial semanal actualizado."
                )


                st.success(
                    "✅ Seguimiento por bloque actualizado."
                )


                st.cache_data.clear()

                st.balloons()


            else:

                st.error(
                    "Hubo problemas al guardar:"
                )


                for error in errores:

                    st.write(
                        f"• {error}"
                    )


# =========================================================
# SEGUIMIENTO
# =========================================================

elif pagina == "Seguimiento":

    st.title(
        "Seguimiento"
    )


    df_historial = leer_hoja(
        "Historial semanal"
    )


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

        if columna in (
            df_historial.columns
        ):

            df_historial[
                columna
            ] = pd.to_numeric(

                df_historial[
                    columna
                ],

                errors="coerce"
            )


    bloque_analisis = st.selectbox(

        "Bloque",

        [
            1,
            2,
            3,
            4
        ],

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


    df_bloque = (

        df_historial[
            (
                df_historial[
                    "Semana"
                ]
                >= inicio
            )
            &
            (
                df_historial[
                    "Semana"
                ]
                <= fin
            )
        ]
        .copy()

    )


    if df_bloque.empty:

        st.info(
            "No hay datos para este bloque."
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


    df_alumno = (

        df_bloque[
            df_bloque[
                "Alumno"
            ]
            .astype(str)
            ==
            alumno
        ]

    )


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


    volumen_plan = (
        resumen[
            "Volumen planificado"
        ]
        .sum()
    )


    carga_plan = (
        resumen[
            "Carga planificada"
        ]
        .sum()
    )


    volumen_pct = (

        resumen[
            "Volumen real"
        ]
        .sum()
        /
        volumen_plan
        * 100

        if volumen_plan > 0

        else 0
    )


    carga_pct = (

        resumen[
            "Carga real"
        ]
        .sum()
        /
        carga_plan
        * 100

        if carga_plan > 0

        else 0
    )


    rpe_real = (
        resumen[
            "RPE real"
        ]
        .mean()
    )


    col1, col2, col3 = (
        st.columns(3)
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


    st.divider()


    st.subheader(
        "Volumen"
    )


    st.line_chart(

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


    st.subheader(
        "RPE"
    )


    st.line_chart(

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


    st.subheader(
        "Carga"
    )


    st.line_chart(

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


# =========================================================
# ALERTAS
# =========================================================

elif pagina == "Alertas":

    st.title(
        "Alertas y recomendaciones"
    )


    df_seguimiento = leer_hoja(
        "Seguimiento por bloque"
    )


    bloque_alertas = st.selectbox(

        "Bloque",

        [
            1,
            2,
            3,
            4
        ],

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
            "No hay alertas para este bloque."
        )

        st.stop()


    df_alertas[
        "Semana"
    ] = pd.to_numeric(

        df_alertas[
            "Semana"
        ],

        errors="coerce"
    )


    # Último seguimiento por alumno

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


    for _, fila in (
        df_alertas.iterrows()
    ):


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

                "**Estado:** "
                f"{fila.get('Estado', '')}"

            )


            st.info(

                "Recomendación: "
                f"{fila.get('Recomendación', '')}"

            )
