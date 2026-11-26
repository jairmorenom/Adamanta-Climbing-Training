import streamlit as st
import pandas as pd
import random
import urllib.parse
import requests
import altair as alt


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
    st.subheader("Sistema de planificación y seguimiento")
    st.write("Inicia sesión con Google para continuar.")

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
# GOOGLE SHEET PRINCIPAL
# =========================================================

SPREADSHEET_ID = "1liLy4wqzh5-dx6TCAN7XF62Jx7TYfusbPwftT0B9kjA"

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
# BASE DE DATOS ACONDICIONAMIENTO FÍSICO
# =========================================================

SPREADSHEET_ID_FISICO = "1b08hMJJafom4jtrpF0yRxWMcohpR_AjhMpv9XCzmd4k"

HOJAS_FISICO = {
    "ejercicios": "Ejercicios",
    "reglas": "Reglas",
    "sesion": "Sesión",
    "como_usar": "Cómo usar",
    "historial": "Historial físico",
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
        return 1, "Proyección en piedra"
    elif 14 <= semana <= 26:
        return 2, "Volumen, fuerza e hipertrofia"
    elif 27 <= semana <= 39:
        return 3, "Técnica avanzada + transición a competencia"
    return 4, "Competencia + transición a roca"


# =========================================================
# MOTOR DE CARGA FÍSICA
# =========================================================

ZONAS_FISICO = [
    "Dedos",
    "Antebrazo / muñeca",
    "Tracción (espalda/bíceps)",
    "Empuje (pecho/tríceps)",
    "Hombro",
    "Core",
    "Piernas / cadera",
]


def obtener_reglas_fisico(df_reglas):
    factores = {}
    umbrales = {}

    for _, fila in df_reglas.iterrows():
        valores = [
            limpiar_texto(valor)
            for valor in fila.tolist()
        ]

        for indice, valor in enumerate(valores):
            valor_normalizado = valor.strip().lower()

            if (
                valor_normalizado == "antes"
                and indice + 1 < len(fila)
            ):
                factor = pd.to_numeric(
                    fila.iloc[indice + 1],
                    errors="coerce"
                )

                if not pd.isna(factor):
                    factores["Antes"] = float(factor)

            elif (
                valor_normalizado
                in ["después", "despues"]
                and indice + 1 < len(fila)
            ):
                factor = pd.to_numeric(
                    fila.iloc[indice + 1],
                    errors="coerce"
                )

                if not pd.isna(factor):
                    factores["Después"] = float(factor)

        nombre = limpiar_texto(
            fila.iloc[0]
        )

        if nombre in ZONAS_FISICO:
            media = pd.to_numeric(
                fila.iloc[1],
                errors="coerce"
            )

            alta = pd.to_numeric(
                fila.iloc[2],
                errors="coerce"
            )

            recomendacion_media = limpiar_texto(
                fila.iloc[3]
            )

            recomendacion_alta = limpiar_texto(
                fila.iloc[4]
            )

            if (
                not pd.isna(media)
                and not pd.isna(alta)
            ):
                umbrales[nombre] = {
                    "Media": float(media),
                    "Alta": float(alta),
                    "Recomendación MEDIA":
                        recomendacion_media,
                    "Recomendación ALTA":
                        recomendacion_alta,
                }

    return factores, umbrales


def calcular_carga_fisica(
    ejercicios_fisicos,
    momento,
    df_ejercicios,
    df_reglas
):
    factores, umbrales = (
        obtener_reglas_fisico(
            df_reglas
        )
    )

    if momento == "Antes de escalar":
        clave_momento = "Antes"
        factor_default = 1.0
    else:
        clave_momento = "Después"
        factor_default = 0.5

    factor = factores.get(
        clave_momento,
        factor_default
    )

    carga_zonas = {
        zona: 0.0
        for zona in ZONAS_FISICO
    }

    for ejercicio in ejercicios_fisicos:
        nombre_ejercicio = ejercicio[
            "Ejercicio"
        ]

        series = float(
            ejercicio[
                "Series"
            ]
        )

        coincidencia = (
            df_ejercicios[
                df_ejercicios[
                    "Ejercicio"
                ]
                .astype(str)
                .str.strip()
                ==
                nombre_ejercicio
            ]
        )

        if coincidencia.empty:
            continue

        fila = coincidencia.iloc[0]

        tipo = limpiar_texto(
            fila.get(
                "Tipo",
                ""
            )
        )

        if tipo.lower() == "activación":
            continue

        for zona in ZONAS_FISICO:
            calificacion = pd.to_numeric(
                fila.get(
                    zona,
                    0
                ),
                errors="coerce"
            )

            if pd.isna(calificacion):
                calificacion = 0

            aporte = (
                float(calificacion)
                *
                series
                *
                factor
            )

            carga_zonas[
                zona
            ] += aporte

    resultados = {}

    for zona in ZONAS_FISICO:
        carga = carga_zonas[
            zona
        ]

        reglas_zona = umbrales.get(
            zona
        )

        if reglas_zona is None:
            resultados[zona] = {
                "Carga": float(carga),
                "Nivel": "SIN REGLA",
                "Recomendación": "",
            }

            continue

        if carga >= reglas_zona["Alta"]:
            nivel = "ALTA"

            recomendacion = (
                reglas_zona[
                    "Recomendación ALTA"
                ]
            )

        elif carga >= reglas_zona["Media"]:
            nivel = "MEDIA"

            recomendacion = (
                reglas_zona[
                    "Recomendación MEDIA"
                ]
            )

        else:
            nivel = "BAJA"

            recomendacion = (
                "Sin restricción específica."
            )

        resultados[zona] = {
            "Carga": float(carga),
            "Nivel": nivel,
            "Recomendación":
                recomendacion,
        }

    return {
        "Factor":
            float(factor),

        "Resultados":
            resultados,
    }


# =========================================================
# PASO 3C-1 — REGLAS DE COMPATIBILIDAD
# =========================================================

DEMANDA_ESCALADA = {

    "flash or trash": {
        "Dedos": 2,
        "Antebrazo / muñeca": 1,
        "Tracción (espalda/bíceps)": 2,
        "Empuje (pecho/tríceps)": 1,
        "Hombro": 2,
        "Core": 2,
        "Piernas / cadera": 2,
    },

    "simulación de competencia": {
        "Dedos": 3,
        "Antebrazo / muñeca": 2,
        "Tracción (espalda/bíceps)": 3,
        "Empuje (pecho/tríceps)": 2,
        "Hombro": 3,
        "Core": 3,
        "Piernas / cadera": 3,
    },

    "proyección": {
        "Dedos": 3,
        "Antebrazo / muñeca": 2,
        "Tracción (espalda/bíceps)": 3,
        "Empuje (pecho/tríceps)": 1,
        "Hombro": 2,
        "Core": 3,
        "Piernas / cadera": 2,
    },

    "corrección de técnica": {
        "Dedos": 1,
        "Antebrazo / muñeca": 1,
        "Tracción (espalda/bíceps)": 1,
        "Empuje (pecho/tríceps)": 1,
        "Hombro": 1,
        "Core": 1,
        "Piernas / cadera": 1,
    },

    "endurance técnico": {
        "Dedos": 2,
        "Antebrazo / muñeca": 3,
        "Tracción (espalda/bíceps)": 2,
        "Empuje (pecho/tríceps)": 1,
        "Hombro": 1,
        "Core": 2,
        "Piernas / cadera": 1,
    },

    "volumen/endurance técnico": {
        "Dedos": 2,
        "Antebrazo / muñeca": 3,
        "Tracción (espalda/bíceps)": 2,
        "Empuje (pecho/tríceps)": 1,
        "Hombro": 1,
        "Core": 2,
        "Piernas / cadera": 1,
    },

    "dinámicos": {
        "Dedos": 2,
        "Antebrazo / muñeca": 1,
        "Tracción (espalda/bíceps)": 2,
        "Empuje (pecho/tríceps)": 1,
        "Hombro": 3,
        "Core": 3,
        "Piernas / cadera": 3,
    },

    "coordinación": {
        "Dedos": 1,
        "Antebrazo / muñeca": 1,
        "Tracción (espalda/bíceps)": 1,
        "Empuje (pecho/tríceps)": 1,
        "Hombro": 2,
        "Core": 3,
        "Piernas / cadera": 3,
    },

    "habilidades técnicas": {
        "Dedos": 1,
        "Antebrazo / muñeca": 1,
        "Tracción (espalda/bíceps)": 1,
        "Empuje (pecho/tríceps)": 1,
        "Hombro": 1,
        "Core": 2,
        "Piernas / cadera": 2,
    },

    "movilidad aplicada": {
        "Dedos": 0,
        "Antebrazo / muñeca": 0,
        "Tracción (espalda/bíceps)": 0,
        "Empuje (pecho/tríceps)": 0,
        "Hombro": 1,
        "Core": 1,
        "Piernas / cadera": 1,
    },
}


def obtener_demanda_escalada(
    tipo_sesion
):
    tipo_normalizado = (
        limpiar_texto(
            tipo_sesion
        )
        .lower()
    )

    if tipo_normalizado in DEMANDA_ESCALADA:
        return DEMANDA_ESCALADA[
            tipo_normalizado
        ]

    return {
        "Dedos": 1,
        "Antebrazo / muñeca": 1,
        "Tracción (espalda/bíceps)": 1,
        "Empuje (pecho/tríceps)": 1,
        "Hombro": 1,
        "Core": 1,
        "Piernas / cadera": 1,
    }


# =========================================================
# PASO 3C-2 — CALCULAR COMPATIBILIDAD
# =========================================================

def calcular_compatibilidad(
    tipo_sesion,
    carga_por_zona,
    momento
):
    demanda_escalada = (
        obtener_demanda_escalada(
            tipo_sesion
        )
    )

    mapa_nivel_fisico = {
        "BAJA": 0,
        "MEDIA": 1,
        "ALTA": 2,
    }

    puntaje_total = 0.0

    coincidencias = []

    for zona in ZONAS_FISICO:

        demanda = (
            demanda_escalada.get(
                zona,
                0
            )
        )

        datos_fisicos = (
            carga_por_zona.get(
                zona,
                {}
            )
        )

        nivel_fisico = (
            datos_fisicos.get(
                "Nivel",
                "BAJA"
            )
        )

        intensidad_fisica = (
            mapa_nivel_fisico.get(
                nivel_fisico,
                0
            )
        )

        puntaje_zona = (
            demanda
            *
            intensidad_fisica
        )

        if momento == "Antes de escalar":
            puntaje_zona *= 1.25

        puntaje_total += (
            puntaje_zona
        )

        if (
            demanda >= 2
            and nivel_fisico in [
                "MEDIA",
                "ALTA"
            ]
        ):
            coincidencias.append({
                "Zona":
                    zona,

                "Demanda escalada":
                    demanda,

                "Carga física":
                    nivel_fisico,

                "Puntaje":
                    round(
                        puntaje_zona,
                        1
                    ),
            })

    if puntaje_total >= 12:
        nivel = "ALTA INTERFERENCIA"

    elif puntaje_total >= 6:
        nivel = "REVISAR"

    else:
        nivel = "COMPATIBLE"

    coincidencias = sorted(
        coincidencias,
        key=lambda x: x["Puntaje"],
        reverse=True
    )

    return {
        "Puntaje":
            round(
                puntaje_total,
                1
            ),

        "Nivel":
            nivel,

        "Coincidencias":
            coincidencias,

        "Demanda escalada":
            demanda_escalada,
    }


# =========================================================
# LECTURA PÚBLICA DEL GOOGLE SHEET
# =========================================================

@st.cache_data(ttl=60)
def leer_hoja(
    nombre_hoja,
    spreadsheet_id=SPREADSHEET_ID,
    header=0
):
    nombre_codificado = (
        urllib.parse.quote(
            nombre_hoja
        )
    )

    url = (
        "https://docs.google.com/spreadsheets/d/"
        f"{spreadsheet_id}/gviz/tq?"
        f"tqx=out:csv&sheet={nombre_codificado}"
    )

    df = pd.read_csv(
        url,
        header=header
    )

    if header is not None:
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
        return st.user.tokens[
            "access"
        ]

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
            "application/json",
    }


# =========================================================
# GOOGLE SHEETS API
# =========================================================

def sheets_get(rango):
    rango_url = (
        urllib.parse.quote(
            rango,
            safe=""
        )
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
            "Tu cuenta no tiene permiso para modificar esta hoja."
        )

        st.stop()

    respuesta.raise_for_status()

    return (
        respuesta
        .json()
        .get(
            "values",
            []
        )
    )


def sheets_update(
    rango,
    valores
):
    rango_url = (
        urllib.parse.quote(
            rango,
            safe=""
        )
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
            "range":
                rango,

            "majorDimension":
                "ROWS",

            "values":
                valores,
        },

        timeout=20
    )

    respuesta.raise_for_status()

    return respuesta.json()


def sheets_append(
    rango,
    valores
):
    rango_url = (
        urllib.parse.quote(
            rango,
            safe=""
        )
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
            "majorDimension":
                "ROWS",

            "values":
                valores,
        },

        timeout=20
    )

    respuesta.raise_for_status()

    return respuesta.json()
# =========================================================
# GOOGLE SHEETS API — ACONDICIONAMIENTO FÍSICO
# =========================================================

def sheets_get_fisico(rango):

    rango_url = urllib.parse.quote(
        rango,
        safe=""
    )

    url = (
        "https://sheets.googleapis.com/v4/"
        f"spreadsheets/{SPREADSHEET_ID_FISICO}/"
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
            "modificar la base de acondicionamiento físico."
        )

        st.stop()


    respuesta.raise_for_status()


    return respuesta.json().get(
        "values",
        []
    )


def sheets_update_fisico(
    rango,
    valores
):

    rango_url = urllib.parse.quote(
        rango,
        safe=""
    )

    url = (
        "https://sheets.googleapis.com/v4/"
        f"spreadsheets/{SPREADSHEET_ID_FISICO}/"
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


def sheets_append_fisico(
    rango,
    valores
):

    rango_url = urllib.parse.quote(
        rango,
        safe=""
    )

    url = (
        "https://sheets.googleapis.com/v4/"
        f"spreadsheets/{SPREADSHEET_ID_FISICO}/"
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
# GUARDAR HISTORIAL FÍSICO
# =========================================================

def guardar_historial_fisico(
    semana,
    sesion,
    alumno,
    tipo_sesion,
    tipo_fisico,
    momento,
    ejercicio,
    series_planificadas,
    series_reales,
    repeticiones_planificadas,
    repeticiones_reales,
    carga_externa_planificada,
    carga_externa_real,
    rpe_planificado,
    rpe_real,
    carga_zonas,
    compatibilidad,
    puntaje_interferencia
):

    # =====================================================
    # EXTRAER CARGA DE CADA ZONA
    # =====================================================

    def obtener_carga_zona(
        zona
    ):

        valor = carga_zonas.get(
            zona,
            0
        )

        # Permite recibir:
        # {"Dedos": 4}
        #
        # o:
        # {"Dedos": {"Carga": 4, "Nivel": "MEDIA"}}

        if isinstance(
            valor,
            dict
        ):

            valor = valor.get(
                "Carga",
                0
            )


        valor = pd.to_numeric(
            valor,
            errors="coerce"
        )


        if pd.isna(
            valor
        ):

            return 0.0


        return float(
            valor
        )


    # =====================================================
    # CREAR FILA
    # =====================================================

    nueva_fila = [

        int(
            semana
        ),

        int(
            sesion
        ),

        str(
            alumno
        ),

        str(
            tipo_sesion
        ),

        str(
            tipo_fisico
        ),

        str(
            momento
        ),

        str(
            ejercicio
        ),

        int(
            series_planificadas
        ),

        int(
            series_reales
        ),

        int(
            repeticiones_planificadas
        ),

        int(
            repeticiones_reales
        ),

        float(
            carga_externa_planificada
        ),

        float(
            carga_externa_real
        ),

        float(
            rpe_planificado
        ),

        float(
            rpe_real
        ),

        obtener_carga_zona(
            "Dedos"
        ),

        obtener_carga_zona(
            "Antebrazo / muñeca"
        ),

        obtener_carga_zona(
            "Tracción (espalda/bíceps)"
        ),

        obtener_carga_zona(
            "Empuje (pecho/tríceps)"
        ),

        obtener_carga_zona(
            "Hombro"
        ),

        obtener_carga_zona(
            "Core"
        ),

        obtener_carga_zona(
            "Piernas / cadera"
        ),

        str(
            compatibilidad
        ),

        float(
            puntaje_interferencia
        )
    ]


    # =====================================================
    # LEER HISTORIAL EXISTENTE
    # =====================================================

    nombre_hoja = (
        HOJAS_FISICO[
            "historial"
        ]
    )


    valores = sheets_get_fisico(
        f"'{nombre_hoja}'!A:X"
    )


    fila_encontrada = None


    # =====================================================
    # BUSCAR SI YA EXISTE
    # Semana + Sesión + Alumno + Ejercicio
    # =====================================================

    for numero_fila, fila in enumerate(
        valores[1:],
        start=2
    ):

        if len(
            fila
        ) < 7:

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


        ejercicio_existente = (
            str(
                fila[6]
            )
            .strip()
            .lower()
        )


        if (
            semana_existente
            ==
            int(
                semana
            )

            and

            sesion_existente
            ==
            int(
                sesion
            )

            and

            alumno_existente
            ==
            str(
                alumno
            )
            .strip()
            .lower()

            and

            ejercicio_existente
            ==
            str(
                ejercicio
            )
            .strip()
            .lower()
        ):

            fila_encontrada = (
                numero_fila
            )

            break


    # =====================================================
    # ACTUALIZAR SI YA EXISTE
    # =====================================================

    if fila_encontrada:

        sheets_update_fisico(
            (
                f"'{nombre_hoja}'!"
                f"A{fila_encontrada}:X{fila_encontrada}"
            ),
            [
                nueva_fila
            ]
        )

        return "actualizado"


    # =====================================================
    # CREAR SI NO EXISTE
    # =====================================================

    sheets_append_fisico(
        f"'{nombre_hoja}'!A:X",
        [
            nueva_fila
        ]
    )


    return "creado"
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
        int(volumen_real),
        float(
            round(
                rpe_planificado,
                1
            )
        ),
        int(rpe_real),
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
        ),
    ]

    fila_encontrada = None

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
            ==
            int(
                semana
            )
            and
            sesion_existente
            ==
            int(
                sesion
            )
            and
            alumno_existente
            ==
            str(
                alumno
            )
            .strip()
            .lower()
        ):
            fila_encontrada = (
                numero_fila
            )

            break

    if fila_encontrada:
        sheets_update(
            (
                "'Historial semanal'!"
                f"A{fila_encontrada}:J{fila_encontrada}"
            ),
            [
                nueva_fila
            ]
        )

        return "actualizado"

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
    if (
        dif_rpe >= 2
        or carga_pct > 120
        or volumen_pct > 120
    ):
        return "ALTA"

    if (
        dif_rpe <= -2
        or carga_pct < 70
        or volumen_pct < 70
    ):
        return "REVISAR"

    if (
        75 <= carga_pct < 85
        or 115 < carga_pct <= 120
        or 75 <= volumen_pct < 85
        or 115 < volumen_pct <= 120
        or 1 <= abs(dif_rpe) < 2
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
        return (
            "Dentro de rango"
        )

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
# COACH INSIGHTS
# =========================================================

def generar_coach_insights(
    resumen
):
    insights = []

    if resumen.empty:
        return insights

    resumen = (
        resumen
        .sort_values(
            "Semana"
        )
        .copy()
    )

    ultimas = (
        resumen
        .tail(
            3
        )
        .copy()
    )

    ultima = (
        resumen
        .iloc[-1]
    )

    volumen_plan_total = (
        resumen[
            "Volumen planificado"
        ]
        .sum()
    )

    volumen_real_total = (
        resumen[
            "Volumen real"
        ]
        .sum()
    )

    carga_plan_total = (
        resumen[
            "Carga planificada"
        ]
        .sum()
    )

    carga_real_total = (
        resumen[
            "Carga real"
        ]
        .sum()
    )

    volumen_pct_total = (
        volumen_real_total
        /
        volumen_plan_total
        *
        100
        if volumen_plan_total > 0
        else 0
    )

    carga_pct_total = (
        carga_real_total
        /
        carga_plan_total
        *
        100
        if carga_plan_total > 0
        else 0
    )

    rpe_plan_total = (
        resumen[
            "RPE planificado"
        ]
        .mean()
    )

    rpe_real_total = (
        resumen[
            "RPE real"
        ]
        .mean()
    )

    dif_rpe_total = (
        rpe_real_total
        -
        rpe_plan_total
    )

    if (
        90 <= volumen_pct_total <= 110
        and 90 <= carga_pct_total <= 110
        and abs(
            dif_rpe_total
        ) < 1
    ):
        insights.append({
            "nivel":
                "POSITIVO",

            "titulo":
                "Buena adherencia al plan",

            "mensaje":
                (
                    f"El atleta acumula "
                    f"{volumen_pct_total:.1f}% "
                    f"del volumen y "
                    f"{carga_pct_total:.1f}% "
                    "de la carga planificada, "
                    "con un RPE cercano al objetivo."
                ),

            "accion":
                (
                    "Mantener la planificación actual "
                    "mientras la calidad de ejecución "
                    "siga siendo buena."
                ),
        })

    if len(
        ultimas
    ) >= 2:
        rpe_alto = (
            ultimas[
                "Dif. RPE"
            ]
            >=
            1
        )

        if (
            rpe_alto
            .tail(
                2
            )
            .all()
        ):
            insights.append({
                "nivel":
                    "ATENCION",

                "titulo":
                    "RPE por encima del plan",

                "mensaje":
                    (
                        "Las últimas 2 semanas registradas "
                        "presentan un RPE medio superior al plan."
                    ),

                "accion":
                    (
                        "Evitar aumentar volumen o intensidad "
                        "hasta comprobar si el RPE vuelve "
                        "al rango previsto."
                    ),
            })

    if len(
        ultimas
    ) >= 3:
        if (
            ultimas[
                "Dif. RPE"
            ]
            >=
            1
        ).all():
            insights.append({
                "nivel":
                    "ALERTA",

                "titulo":
                    "RPE elevado durante 3 semanas",

                "mensaje":
                    (
                        "El esfuerzo percibido se ha mantenido "
                        "por encima de lo planificado durante "
                        "las últimas 3 semanas."
                    ),

                "accion":
                    (
                        "Revisar la carga de la siguiente semana "
                        "y considerar reducir temporalmente "
                        "volumen o intensidad."
                    ),
            })

    if len(
        ultimas
    ) >= 3:
        primera = (
            ultimas.iloc[0]
        )

        reciente = (
            ultimas.iloc[-1]
        )

        aumento_volumen = (
            reciente[
                "Volumen real"
            ]
            >
            primera[
                "Volumen real"
            ]
            *
            1.05
        )

        rpe_estable = (
            reciente[
                "RPE real"
            ]
            <=
            primera[
                "RPE real"
            ]
            +
            0.5
        )

        if (
            aumento_volumen
            and
            rpe_estable
        ):
            insights.append({
                "nivel":
                    "POSITIVO",

                "titulo":
                    "Posible adaptación positiva",

                "mensaje":
                    (
                        "El volumen real ha aumentado "
                        "en las últimas semanas sin "
                        "un aumento proporcional del RPE."
                    ),

                "accion":
                    (
                        "Mantener la progresión prevista. "
                        "Si la técnica y la recuperación son buenas, "
                        "puede continuar el incremento gradual planificado."
                    ),
            })

    if len(
        ultimas
    ) >= 2:
        anterior = (
            ultimas.iloc[-2]
        )

        reciente = (
            ultimas.iloc[-1]
        )

        volumen_baja = (
            reciente[
                "Volumen real"
            ]
            <
            anterior[
                "Volumen real"
            ]
            *
            0.90
        )

        rpe_sube = (
            reciente[
                "RPE real"
            ]
            >
            anterior[
                "RPE real"
            ]
            +
            0.5
        )

        if (
            volumen_baja
            and
            rpe_sube
        ):
            insights.append({
                "nivel":
                    "ALERTA",

                "titulo":
                    "Menor volumen con mayor esfuerzo",

                "mensaje":
                    (
                        "La última semana produjo menos volumen "
                        "que la anterior, pero con un RPE mayor."
                    ),

                "accion":
                    (
                        "No progresar la carga todavía. "
                        "Revisar recuperación, dificultad de los ejercicios "
                        "y calidad técnica."
                    ),
            })

    if len(
        ultimas
    ) >= 3:
        carga_inicio = (
            ultimas
            .iloc[0][
                "Carga real"
            ]
        )

        carga_final = (
            ultimas
            .iloc[-1][
                "Carga real"
            ]
        )

        if carga_inicio > 0:
            cambio_carga = (
                (
                    carga_final
                    -
                    carga_inicio
                )
                /
                carga_inicio
                *
                100
            )

            if cambio_carga > 20:
                insights.append({
                    "nivel":
                        "ATENCION",

                    "titulo":
                        "Aumento rápido de carga",

                    "mensaje":
                        (
                            f"La carga real aumentó aproximadamente "
                            f"{cambio_carga:.1f}% entre la primera "
                            "y la última de las 3 semanas recientes."
                        ),

                    "accion":
                        (
                            "Confirmar que el aumento estaba previsto "
                            "antes de seguir progresando la siguiente semana."
                        ),
                })

            elif cambio_carga < -20:
                insights.append({
                    "nivel":
                        "ATENCION",

                    "titulo":
                        "Caída marcada de carga",

                    "mensaje":
                        (
                            f"La carga real disminuyó aproximadamente "
                            f"{abs(cambio_carga):.1f}% durante "
                            "las últimas 3 semanas."
                        ),

                    "accion":
                        (
                            "Revisar si corresponde a una descarga programada, "
                            "ausencias o menor cumplimiento del entrenamiento."
                        ),
                })

    volumen_ultima = (
        ultima[
            "Volumen %"
        ]
    )

    carga_ultima = (
        ultima[
            "Carga %"
        ]
    )

    dif_rpe_ultima = (
        ultima[
            "Dif. RPE"
        ]
    )

    if (
        volumen_ultima < 80
        and
        dif_rpe_ultima < 1
    ):
        insights.append({
            "nivel":
                "ATENCION",

            "titulo":
                "Volumen por debajo del objetivo",

            "mensaje":
                (
                    f"La última semana alcanzó solamente "
                    f"{volumen_ultima:.1f}% "
                    "del volumen planificado."
                ),

            "accion":
                (
                    "Identificar si hubo ausencias o ejercicios incompletos. "
                    "Si el RPE y la técnica fueron adecuados, recuperar volumen "
                    "de forma progresiva."
                ),
        })

    if (
        carga_ultima > 120
        or
        volumen_ultima > 120
    ):
        insights.append({
            "nivel":
                "ALERTA",

            "titulo":
                "La última semana superó el plan",

            "mensaje":
                (
                    f"Volumen: {volumen_ultima:.1f}% · "
                    f"Carga: {carga_ultima:.1f}% del objetivo."
                ),

            "accion":
                (
                    "Evitar seguir aumentando la siguiente sesión "
                    "sin revisar si el exceso de carga fue intencional."
                ),
        })

    if not insights:
        insights.append({
            "nivel":
                "ESTABLE",

            "titulo":
                "Respuesta estable",

            "mensaje":
                (
                    "No se detectan desviaciones importantes "
                    "respecto a la planificación con los datos disponibles."
                ),

            "accion":
                (
                    "Mantener el plan y continuar registrando "
                    "volumen, RPE y carga."
                ),
        })

    return insights[:5]


# =========================================================
# ACTUALIZAR SEGUIMIENTO POR BLOQUE
# =========================================================

def actualizar_seguimiento_bloque(
    bloque
):
    valores = sheets_get(
        "'Historial semanal'!A:J"
    )

    if len(
        valores
    ) <= 1:
        return

    encabezados = (
        valores[0]
    )

    filas = []

    for fila in valores[1:]:
        fila_completa = (
            fila
            +
            [""] * (
                len(
                    encabezados
                )
                -
                len(
                    fila
                )
            )
        )

        filas.append(
            fila_completa[
                :len(
                    encabezados
                )
            ]
        )

    df = pd.DataFrame(
        filas,
        columns=encabezados
    )

    columnas_numericas = [
        "Semana",
        "Sesión",
        "Volumen planificado",
        "Volumen real",
        "RPE planificado",
        "RPE real",
        "Carga planificada",
        "Carga real",
    ]

    for columna in columnas_numericas:
        if columna in df.columns:
            df[columna] = (
                pd.to_numeric(
                    df[columna],
                    errors="coerce"
                )
            )

    rangos = {
        1: (1, 13),
        2: (14, 26),
        3: (27, 39),
        4: (40, 52),
    }

    inicio, fin = (
        rangos[
            bloque
        ]
    )

    df_bloque = (
        df[
            (
                df[
                    "Semana"
                ]
                >=
                inicio
            )
            &
            (
                df[
                    "Semana"
                ]
                <=
                fin
            )
        ]
        .copy()
    )

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
                "Carga real",
            ]
        )
    )

    if df_bloque.empty:
        return

    df_bloque[
        "Alumno"
    ] = (
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
        ]
        .max()
    )

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
                "sum",
        })
    )

    seguimiento_existente = (
        sheets_get(
            "'Seguimiento por bloque'!A:K"
        )
    )

    for _, fila in resumen.iterrows():
        alumno = (
            fila[
                "Alumno"
            ]
        )

        volumen_pct = (
            fila[
                "Volumen real"
            ]
            /
            fila[
                "Volumen planificado"
            ]
            *
            100
            if fila[
                "Volumen planificado"
            ] > 0
            else 0
        )

        carga_pct = (
            fila[
                "Carga real"
            ]
            /
            fila[
                "Carga planificada"
            ]
            *
            100
            if fila[
                "Carga planificada"
            ] > 0
            else 0
        )

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
            recomendacion,
        ]

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
                ==
                int(
                    bloque
                )
                and
                semana_existente
                ==
                semana_actual
                and
                alumno_existente
                ==
                alumno
                .strip()
                .lower()
            ):
                fila_encontrada = (
                    numero_fila
                )

                break

        if fila_encontrada:
            sheets_update(
                (
                    "'Seguimiento por bloque'!"
                    f"A{fila_encontrada}:K{fila_encontrada}"
                ),
                [
                    nueva_fila
                ]
            )

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
# CARGAR BASE DE ACONDICIONAMIENTO FÍSICO
# =========================================================

try:
    df_ejercicios_fisico = (
        leer_hoja(
            HOJAS_FISICO[
                "ejercicios"
            ],
            SPREADSHEET_ID_FISICO
        )
    )

    df_reglas_fisico = (
        leer_hoja(
            HOJAS_FISICO[
                "reglas"
            ],
            SPREADSHEET_ID_FISICO,
            header=None
        )
    )

    BASE_FISICO_CONECTADA = (
        True
    )

except Exception as e:
    df_ejercicios_fisico = (
        pd.DataFrame()
    )

    df_reglas_fisico = (
        pd.DataFrame()
    )

    BASE_FISICO_CONECTADA = (
        False
    )

    ERROR_BASE_FISICO = (
        str(
            e
        )
    )


# =========================================================
# CARGAR DATOS PRINCIPALES
# =========================================================

try:
    df_distribucion = (
        leer_hoja(
            "Distribucion semanal"
        )
    )

    df_alumnos = (
        leer_hoja(
            "Alumnos"
        )
    )

    conexion_ok = (
        True
    )

except Exception as error:
    conexion_ok = (
        False
    )

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

pagina = (
    st.sidebar.radio(
        "Navegación",
        [
            "Inicio",
            "Planear sesión",
            "Acondicionamiento físico",
            "Registrar sesión",
            "Seguimiento",
            "Vista grupo",
            "Alertas",
        ]
    )
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

df_distribucion[
    "Semana"
] = (
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

if "Nombre" in df_alumnos.columns:
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
        .iloc[:, 0]
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
        st.columns(
            3
        )
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
        "La programación se obtiene directamente de la base de datos."
    )

    col1, col2 = (
        st.columns(
            2
        )
    )

    with col1:
        semana = (
            st.selectbox(
                "Semana",
                list(
                    range(
                        1,
                        53
                    )
                ),
                index=None,
                placeholder="Selecciona una semana..."
            )
        )

    with col2:
        sesion = (
            st.selectbox(
                "Sesión",
                [
                    1,
                    2,
                    3,
                    4
                ],
                index=None,
                placeholder="Selecciona una sesión..."
            )
        )

    if (
        semana is None
        or
        sesion is None
    ):
        st.info(
            "Selecciona una semana y una sesión para comenzar."
        )

        st.stop()

    bloque, nombre_bloque = (
        obtener_bloque(
            semana
        )
    )

    fila_semana = (
        df_distribucion[
            df_distribucion[
                "Semana"
            ]
            ==
            semana
        ]
    )

    columna_sesion = (
        f"Sesión {sesion}"
    )

    if (
        fila_semana.empty
        or
        columna_sesion
        not in
        df_distribucion.columns
    ):
        st.error(
            "No se encontró la sesión programada."
        )

        st.stop()

    tipo_sesion = (
        limpiar_texto(
            fila_semana
            .iloc[0][
                columna_sesion
            ]
        )
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

    df_lista = (
        leer_hoja(
            HOJAS_EJERCICIOS[
                bloque
            ]
        )
    )

    primera_columna = (
        df_lista
        .columns[0]
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
            coincidencia
            .index[0]
        )

        fila = (
            df_lista
            .loc[
                indice
            ]
        )

        for columna in (
            df_lista
            .columns[
                1:6
            ]
        ):
            nombre = (
                limpiar_texto(
                    fila[
                        columna
                    ]
                )
            )

            if (
                nombre
                and
                not
                nombre
                .lower()
                .startswith(
                    "opción"
                )
            ):
                ejercicios.append(
                    nombre
                )

    if not ejercicios:
        for i in range(
            len(
                df_lista
            )
        ):
            valor = (
                limpiar_texto(
                    df_lista
                    .iloc[
                        i,
                        0
                    ]
                )
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
                        df_lista
                        .iloc[
                            i + 1
                        ]
                    )

                    for valor_ejercicio in (
                        fila_siguiente
                        .iloc[
                            1:6
                        ]
                    ):
                        ejercicio = (
                            limpiar_texto(
                                valor_ejercicio
                            )
                        )

                        if ejercicio:
                            ejercicios.append(
                                ejercicio
                            )

                break

    if not ejercicios:
        st.error(
            f"No se encontraron ejercicios para {tipo_sesion}."
        )

        st.stop()

    st.divider()

    st.subheader(
        "Ejercicios"
    )

    cantidad = (
        st.slider(
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
    )

    modo = (
        st.radio(
            "Modo de selección",
            [
                "Manual",
                "Aleatorio"
            ],
            horizontal=True
        )
    )

    if modo == "Manual":
        seleccion = (
            st.multiselect(
                "Selecciona los ejercicios",
                ejercicios,
                max_selections=cantidad
            )
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
            ] = (
                random.sample(
                    ejercicios,
                    cantidad
                )
            )

        seleccion = (
            st.session_state.get(
                clave,
                []
            )
        )

    if seleccion:
        st.divider()

        df_carga = (
            leer_hoja(
                HOJAS_CARGA[
                    bloque
                ]
            )
        )

        columnas_numericas = [
            "Series/Boulders",
            "Movimientos",
            "Vueltas",
            "RPE objetivo",
            "Descanso min",
        ]

        for columna in columnas_numericas:
            if columna in df_carga.columns:
                df_carga[
                    columna
                ] = (
                    pd.to_numeric(
                        df_carga[
                            columna
                        ],
                        errors="coerce"
                    )
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

            if coincidencia_carga.empty:
                continue

            fila = (
                coincidencia_carga
                .iloc[0]
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
                    ],
            })

        df_plan = (
            pd.DataFrame(
                filas_plan
            )
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
            st.columns(
                3
            )
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


        # =====================================================
        # ACONDICIONAMIENTO FÍSICO
        # =====================================================

        st.divider()

        st.subheader(
            "Acondicionamiento físico"
        )

        agregar_fisico = (
            st.toggle(
                "Agregar acondicionamiento físico a esta sesión",
                value=False,
                key=f"agregar_fisico_{semana}_{sesion}"
            )
        )

        acondicionamiento = {
            "Activo": False,
            "Tipo": None,
            "Momento": None,
            "Ejercicios": [],
        }

        if agregar_fisico:

            st.caption(
                "El acondicionamiento formará parte de esta misma sesión de escalada."
            )

            tipos_fisico = (
                sorted(
                    df_ejercicios_fisico[
                        "Tipo"
                    ]
                    .dropna()
                    .astype(str)
                    .str.strip()
                    .unique()
                    .tolist()
                )
            )

            tipo_fisico = (
                st.selectbox(
                    "Tipo de acondicionamiento",
                    tipos_fisico,
                    index=None,
                    placeholder="Selecciona el tipo...",
                    key=f"tipo_fisico_{semana}_{sesion}"
                )
            )

            momento_fisico = (
                st.radio(
                    "Momento",
                    [
                        "Antes de escalar",
                        "Después de escalar"
                    ],
                    horizontal=True,
                    key=f"momento_fisico_{semana}_{sesion}"
                )
            )

            if tipo_fisico is not None:

                df_tipo_fisico = (
                    df_ejercicios_fisico[
                        df_ejercicios_fisico[
                            "Tipo"
                        ]
                        .astype(str)
                        .str.strip()
                        ==
                        tipo_fisico
                    ]
                    .copy()
                )

                opciones_ejercicios = (
                    sorted(
                        df_tipo_fisico[
                            "Ejercicio"
                        ]
                        .dropna()
                        .astype(str)
                        .str.strip()
                        .unique()
                        .tolist()
                    )
                )

                numero_ejercicios_fisico = (
                    st.number_input(
                        "Número de ejercicios",
                        min_value=1,
                        max_value=10,
                        value=3,
                        step=1,
                        key=f"numero_fisico_{semana}_{sesion}"
                    )
                )

                ejercicios_fisicos = []

                ejercicios_utilizados = set()

                for i in range(
                    int(
                        numero_ejercicios_fisico
                    )
                ):

                    with st.expander(
                        f"Ejercicio {i + 1}",
                        expanded=True
                    ):
                        ejercicio_fisico = (
                            st.selectbox(
                                "Ejercicio",
                                opciones_ejercicios,
                                index=None,
                                placeholder="Selecciona ejercicio...",
                                key=(
                                    f"ejercicio_fisico_"
                                    f"{semana}_{sesion}_{i}"
                                )
                            )
                        )

                        if ejercicio_fisico is not None:

                            if (
                                ejercicio_fisico
                                in
                                ejercicios_utilizados
                            ):
                                st.warning(
                                    "Este ejercicio ya fue seleccionado."
                                )

                                continue

                            ejercicios_utilizados.add(
                                ejercicio_fisico
                            )

                            fila_ejercicio = (
                                df_tipo_fisico[
                                    df_tipo_fisico[
                                        "Ejercicio"
                                    ]
                                    .astype(str)
                                    .str.strip()
                                    ==
                                    ejercicio_fisico
                                ]
                                .iloc[0]
                            )

                            equipo = (
                                limpiar_texto(
                                    fila_ejercicio.get(
                                        "Equipo",
                                        ""
                                    )
                                )
                            )

                            zona_principal = (
                                limpiar_texto(
                                    fila_ejercicio.get(
                                        "Zona principal",
                                        ""
                                    )
                                )
                            )

                            col_info1, col_info2 = (
                                st.columns(
                                    2
                                )
                            )

                            col_info1.caption(
                                f"Equipo: "
                                f"{equipo if equipo else '—'}"
                            )

                            col_info2.caption(
                                f"Zona principal: "
                                f"{zona_principal if zona_principal else '—'}"
                            )

                            col1_f, col2_f = (
                                st.columns(
                                    2
                                )
                            )

                            series = (
                                col1_f.number_input(
                                    "Series",
                                    min_value=1,
                                    max_value=20,
                                    value=3,
                                    step=1,
                                    key=(
                                        f"series_fisico_"
                                        f"{semana}_{sesion}_{i}"
                                    )
                                )
                            )

                            repeticiones = (
                                col2_f.number_input(
                                    "Repeticiones",
                                    min_value=1,
                                    max_value=100,
                                    value=8,
                                    step=1,
                                    key=(
                                        f"reps_fisico_"
                                        f"{semana}_{sesion}_{i}"
                                    )
                                )
                            )

                            col3_f, col4_f = (
                                st.columns(
                                    2
                                )
                            )

                            carga_externa = (
                                col3_f.number_input(
                                    "Carga externa (kg)",
                                    min_value=0.0,
                                    value=0.0,
                                    step=0.5,
                                    key=(
                                        f"carga_fisico_"
                                        f"{semana}_{sesion}_{i}"
                                    )
                                )
                            )

                            rpe_objetivo = (
                                col4_f.number_input(
                                    "RPE objetivo",
                                    min_value=1.0,
                                    max_value=10.0,
                                    value=7.0,
                                    step=0.5,
                                    key=(
                                        f"rpe_fisico_"
                                        f"{semana}_{sesion}_{i}"
                                    )
                                )
                            )

                            ejercicios_fisicos.append({
                                "Ejercicio":
                                    ejercicio_fisico,

                                "Tipo":
                                    tipo_fisico,

                                "Equipo":
                                    equipo,

                                "Zona principal":
                                    zona_principal,

                                "Series":
                                    int(
                                        series
                                    ),

                                "Repeticiones":
                                    int(
                                        repeticiones
                                    ),

                                "Carga externa":
                                    float(
                                        carga_externa
                                    ),

                                "RPE objetivo":
                                    float(
                                        rpe_objetivo
                                    ),
                            })


                # =================================================
                # PASO 3A — CARGA FÍSICA
                # =================================================

                resultado_carga_fisica = (
                    calcular_carga_fisica(
                        ejercicios_fisicos,
                        momento_fisico,
                        df_ejercicios_fisico,
                        df_reglas_fisico
                    )
                )

                carga_por_zona = (
                    resultado_carga_fisica[
                        "Resultados"
                    ]
                )


                # =================================================
                # PASO 3C-2 — COMPATIBILIDAD
                # Se calcula y guarda; todavía no se muestra
                # =================================================

                compatibilidad = (
                    calcular_compatibilidad(
                        tipo_sesion,
                        carga_por_zona,
                        momento_fisico
                    )
                )


                acondicionamiento = {
                    "Activo":
                        True,

                    "Tipo":
                        tipo_fisico,

                    "Momento":
                        momento_fisico,

                    "Factor momento":
                        resultado_carga_fisica[
                            "Factor"
                        ],

                    "Ejercicios":
                        ejercicios_fisicos,

                    "Carga por zona":
                        carga_por_zona,

                    "Compatibilidad":
                        compatibilidad,
                }


                # =================================================
                # MOSTRAR SOLO UNA VEZ
                # =================================================

                if ejercicios_fisicos:

                    st.divider()

                    st.markdown(
                        "### Resumen del acondicionamiento"
                    )

                    col_f1, col_f2 = (
                        st.columns(
                            2
                        )
                    )

                    col_f1.write(
                        f"**Tipo:** "
                        f"{tipo_fisico}"
                    )

                    col_f2.write(
                        f"**Momento:** "
                        f"{momento_fisico}"
                    )

                    st.caption(
                        "Factor aplicado: "
                        f"{resultado_carga_fisica['Factor']:.1f}"
                    )

                    for numero, ejercicio in enumerate(
                        ejercicios_fisicos,
                        start=1
                    ):
                        st.write(
                            f"**{numero}. "
                            f"{ejercicio['Ejercicio']}** — "
                            f"{ejercicio['Series']} × "
                            f"{ejercicio['Repeticiones']} · "
                            f"{ejercicio['Carga externa']:.1f} kg · "
                            f"RPE {ejercicio['RPE objetivo']:.1f}"
                        )

                    st.markdown(
                        "### Carga física por zona"
                    )

                    filas_carga = []

                    for zona, datos in (
                        carga_por_zona.items()
                    ):
                        filas_carga.append({
                            "Zona":
                                zona,

                            "Carga":
                                round(
                                    datos[
                                        "Carga"
                                    ],
                                    1
                                ),

                            "Nivel":
                                datos[
                                    "Nivel"
                                ],
                        })

                    df_carga_fisica_visual = (
                        pd.DataFrame(
                            filas_carga
                        )
                    )

                    st.dataframe(
                        df_carga_fisica_visual,
                        use_container_width=True,
                        hide_index=True
                    )

                    niveles_altos = sum(
                        1
                        for datos in (
                            carga_por_zona.values()
                        )
                        if datos[
                            "Nivel"
                        ] == "ALTA"
                    )

                    niveles_medios = sum(
                        1
                        for datos in (
                            carga_por_zona.values()
                        )
                        if datos[
                            "Nivel"
                        ] == "MEDIA"
                    )

                    niveles_bajos = sum(
                        1
                        for datos in (
                            carga_por_zona.values()
                        )
                        if datos[
                            "Nivel"
                        ] == "BAJA"
                    )

                    col_n1, col_n2, col_n3 = (
                        st.columns(
                            3
                        )
                    )

                    col_n1.metric(
                        "Zonas ALTA",
                        niveles_altos
                    )

                    col_n2.metric(
                        "Zonas MEDIA",
                        niveles_medios
                    )

                    col_n3.metric(
                        "Zonas BAJA",
                        niveles_bajos
                    )

                    st.markdown(
                        "### Recomendaciones para la escalada"
                    )

                    hay_alertas = False

                    for zona, datos in (
                        carga_por_zona.items()
                    ):
                        nivel = (
                            datos[
                                "Nivel"
                            ]
                        )

                        recomendacion = (
                            datos[
                                "Recomendación"
                            ]
                        )

                        if nivel == "ALTA":
                            hay_alertas = True

                            st.error(
                                f"🔴 **{zona} · ALTA**\n\n"
                                f"{recomendacion}"
                            )

                        elif nivel == "MEDIA":
                            hay_alertas = True

                            st.warning(
                                f"🟠 **{zona} · MEDIA**\n\n"
                                f"{recomendacion}"
                            )

                    if not hay_alertas:
                        st.success(
                            "✅ Todas las zonas están en carga BAJA. "
                            "No hay restricciones específicas "
                            "para la sesión de escalada."
                        )
                                            # =================================================
                    # PASO 3C-3 — COMPATIBILIDAD ESCALADA + FÍSICO
                    # =================================================

                    st.divider()

                    st.markdown(
                        "### Compatibilidad escalada + físico"
                    )


                    nivel_compatibilidad = (
                        compatibilidad[
                            "Nivel"
                        ]
                    )

                    puntaje_compatibilidad = (
                        compatibilidad[
                            "Puntaje"
                        ]
                    )

                    coincidencias_compatibilidad = (
                        compatibilidad[
                            "Coincidencias"
                        ]
                    )


                    # =================================================
                    # RESULTADO GENERAL
                    # =================================================

                    if (
                        nivel_compatibilidad
                        ==
                        "COMPATIBLE"
                    ):

                        st.success(
                            "✅ **COMPATIBLE**\n\n"
                            "La carga del acondicionamiento físico "
                            "presenta poca interferencia con las zonas "
                            "más demandadas por esta sesión de escalada."
                        )


                    elif (
                        nivel_compatibilidad
                        ==
                        "REVISAR"
                    ):

                        st.warning(
                            "🟠 **REVISAR**\n\n"
                            "Existe coincidencia entre algunas zonas "
                            "cargadas en el acondicionamiento físico "
                            "y las demandas de la sesión de escalada."
                        )


                    else:

                        st.error(
                            "🔴 **ALTA INTERFERENCIA**\n\n"
                            "El acondicionamiento físico carga varias "
                            "de las mismas zonas que serán muy demandadas "
                            "durante esta sesión de escalada."
                        )


                    # =================================================
                    # PUNTAJE
                    # =================================================

                    st.metric(
                        "Puntaje de interferencia",
                        f"{puntaje_compatibilidad:.1f}"
                    )


                    st.caption(
                        "Menor puntaje = mayor compatibilidad. "
                        "El resultado considera la demanda de la "
                        "sesión de escalada, la carga física por zona "
                        "y si el acondicionamiento se realiza antes "
                        "o después de escalar."
                    )


                    # =================================================
                    # ZONAS QUE GENERAN INTERFERENCIA
                    # =================================================

                    if coincidencias_compatibilidad:

                        st.markdown(
                            "#### Zonas a considerar"
                        )


                        filas_compatibilidad = []


                        mapa_demanda_texto = {
                            0: "Nula",
                            1: "Baja",
                            2: "Media",
                            3: "Alta"
                        }


                        for coincidencia in (
                            coincidencias_compatibilidad
                        ):

                            demanda_numero = (
                                coincidencia[
                                    "Demanda escalada"
                                ]
                            )


                            filas_compatibilidad.append(
                                {
                                    "Zona":
                                        coincidencia[
                                            "Zona"
                                        ],

                                    "Demanda escalada":
                                        mapa_demanda_texto.get(
                                            demanda_numero,
                                            str(
                                                demanda_numero
                                            )
                                        ),

                                    "Carga física":
                                        coincidencia[
                                            "Carga física"
                                        ],

                                    "Interferencia":
                                        coincidencia[
                                            "Puntaje"
                                        ]
                                }
                            )


                        df_compatibilidad_visual = (
                            pd.DataFrame(
                                filas_compatibilidad
                            )
                        )


                        st.dataframe(
                            df_compatibilidad_visual,
                            use_container_width=True,
                            hide_index=True
                        )


                    else:

                        st.info(
                            "No se detectaron coincidencias relevantes "
                            "entre la carga física y las zonas más "
                            "demandadas por esta sesión de escalada."
                        )


                    # =================================================
                    # LECTURA PARA EL COACH
                    # =================================================

                    st.markdown(
                        "#### Lectura para el coach"
                    )


                    if (
                        nivel_compatibilidad
                        ==
                        "COMPATIBLE"
                    ):

                        st.write(
                            "La combinación puede mantenerse "
                            "como está planificada."
                        )


                    elif (
                        nivel_compatibilidad
                        ==
                        "REVISAR"
                    ):

                        if (
                            momento_fisico
                            ==
                            "Antes de escalar"
                        ):

                            st.write(
                                "Conviene revisar el volumen o la intensidad "
                                "del acondicionamiento antes de escalar, "
                                "especialmente en las zonas señaladas."
                            )

                        else:

                            st.write(
                                "La combinación es exigente, pero al realizar "
                                "el físico después de escalar se reduce su "
                                "interferencia con el rendimiento principal "
                                "de la sesión."
                            )


                    else:

                        if (
                            momento_fisico
                            ==
                            "Antes de escalar"
                        ):

                            st.write(
                                "Considera mover el acondicionamiento físico "
                                "después de escalar o reducir la carga de las "
                                "zonas con mayor coincidencia."
                            )

                        else:

                            st.write(
                                "La carga combinada de la sesión es alta. "
                                "Conviene revisar las zonas señaladas antes "
                                "de añadir más volumen físico."
                            )


        # =====================================================
        # GUARDAR SESIÓN COMPLETA
        # =====================================================

        if (
            len(seleccion)
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
                    ),

                "Acondicionamiento":
                    acondicionamiento
            }

            st.success(
                "Sesión lista para registrar."
            )

       
        # =====================================================
        # GUARDAR SESIÓN COMPLETA
        # =====================================================

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
                    ),

                "Acondicionamiento":
                    acondicionamiento,
            }


# =========================================================
# ACONDICIONAMIENTO FÍSICO
# =========================================================

elif pagina == "Acondicionamiento físico":

    st.title(
        "Acondicionamiento físico"
    )

    if not BASE_FISICO_CONECTADA:

        st.error(
            "No se pudo conectar con la base de acondicionamiento físico."
        )

        st.code(
            ERROR_BASE_FISICO
        )

        st.stop()

    st.success(
        "✅ Base de acondicionamiento físico conectada"
    )

    st.write(
        "Ejercicios cargados:",
        len(
            df_ejercicios_fisico
        )
    )

    total_ejercicios = (
        len(
            df_ejercicios_fisico
        )
    )

    tipos_ejercicio = (
        df_ejercicios_fisico[
            "Tipo"
        ]
        .dropna()
        .nunique()
    )

    zonas_principales = (
        df_ejercicios_fisico[
            "Zona principal"
        ]
        .dropna()
        .nunique()
    )

    col1, col2, col3 = (
        st.columns(
            3
        )
    )

    col1.metric(
        "Ejercicios",
        total_ejercicios
    )

    col2.metric(
        "Tipos",
        tipos_ejercicio
    )

    col3.metric(
        "Zonas principales",
        zonas_principales
    )

    st.divider()

    st.subheader(
        "Base de ejercicios"
    )

    tipo_seleccionado = (
        st.selectbox(
            "Tipo de ejercicio",
            sorted(
                df_ejercicios_fisico[
                    "Tipo"
                ]
                .dropna()
                .unique()
                .tolist()
            ),
            index=None,
            placeholder="Todos los tipos"
        )
    )

    if tipo_seleccionado is None:
        ejercicios_mostrar = (
            df_ejercicios_fisico
            .copy()
        )

    else:
        ejercicios_mostrar = (
            df_ejercicios_fisico[
                df_ejercicios_fisico[
                    "Tipo"
                ]
                ==
                tipo_seleccionado
            ]
            .copy()
        )

    buscar_ejercicio = (
        st.text_input(
            "Buscar ejercicio",
            placeholder=(
                "Ej. dominadas, press, core..."
            )
        )
    )

    if buscar_ejercicio:
        ejercicios_mostrar = (
            ejercicios_mostrar[
                ejercicios_mostrar[
                    "Ejercicio"
                ]
                .astype(str)
                .str.contains(
                    buscar_ejercicio,
                    case=False,
                    na=False
                )
            ]
        )

    columnas_mostrar = [
        "ID",
        "Ejercicio",
        "Tipo",
        "Equipo",
        "Zona principal",
        "Dedos",
        "Antebrazo / muñeca",
        "Tracción (espalda/bíceps)",
        "Empuje (pecho/tríceps)",
        "Hombro",
        "Core",
        "Piernas / cadera",
    ]

    columnas_disponibles = [
        columna
        for columna in columnas_mostrar
        if columna
        in ejercicios_mostrar.columns
    ]

    st.dataframe(
        ejercicios_mostrar[
            columnas_disponibles
        ],
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        f"Mostrando "
        f"{len(ejercicios_mostrar)} "
        f"de {total_ejercicios} ejercicios."
    )
    # =====================================================
    # PASO 4D — VERIFICAR HISTORIAL FÍSICO
    # =====================================================

    st.divider()

    st.subheader(
        "Verificación del historial físico"
    )


    try:

        df_historial_fisico = leer_hoja(
            HOJAS_FISICO[
                "historial"
            ],
            SPREADSHEET_ID_FISICO
        )


        # =================================================
        # COLUMNAS ESPERADAS
        # =================================================

        columnas_historial_fisico = [
            "Semana",
            "Sesión",
            "Alumno",
            "Tipo de sesión",
            "Tipo físico",
            "Momento",
            "Ejercicio",
            "Series planificadas",
            "Series reales",
            "Repeticiones planificadas",
            "Repeticiones reales",
            "Carga externa planificada",
            "Carga externa real",
            "RPE planificado",
            "RPE real",
            "Dedos",
            "Antebrazo / muñeca",
            "Tracción (espalda/bíceps)",
            "Empuje (pecho/tríceps)",
            "Hombro",
            "Core",
            "Piernas / cadera",
            "Compatibilidad",
            "Puntaje interferencia"
        ]


        columnas_faltantes = [
            columna
            for columna
            in columnas_historial_fisico
            if columna
            not in df_historial_fisico.columns
        ]


        # =================================================
        # VALIDACIÓN ESTRUCTURA
        # =================================================

        if columnas_faltantes:

            st.error(
                "❌ Faltan columnas en Historial físico:"
            )

            for columna in columnas_faltantes:

                st.write(
                    f"• {columna}"
                )


        else:

            st.success(
                "✅ Las 24 columnas del historial físico "
                "están correctamente configuradas."
            )


        # =================================================
        # NÚMERO DE REGISTROS
        # =================================================

        total_registros_fisicos = len(
            df_historial_fisico
        )


        if total_registros_fisicos == 0:

            st.info(
                "Todavía no existen registros físicos."
            )


        else:

            col_h1, col_h2, col_h3 = (
                st.columns(3)
            )


            col_h1.metric(
                "Registros físicos",
                total_registros_fisicos
            )


            col_h2.metric(
                "Alumnos",
                df_historial_fisico[
                    "Alumno"
                ]
                .dropna()
                .nunique()
            )


            col_h3.metric(
                "Ejercicios registrados",
                df_historial_fisico[
                    "Ejercicio"
                ]
                .dropna()
                .nunique()
            )


            # =================================================
            # REGISTROS INCOMPLETOS
            # =================================================

            columnas_obligatorias = [
                "Semana",
                "Sesión",
                "Alumno",
                "Ejercicio"
            ]


            registros_incompletos = (
                df_historial_fisico[
                    columnas_obligatorias
                ]
                .isna()
                .any(
                    axis=1
                )
                .sum()
            )


            if registros_incompletos > 0:

                st.warning(
                    f"🟠 Hay {registros_incompletos} "
                    "registro(s) incompletos."
                )

            else:

                st.success(
                    "✅ No hay registros incompletos."
                )


            # =================================================
            # DUPLICADOS
            # =================================================

            duplicados = (
                df_historial_fisico
                .duplicated(
                    subset=[
                        "Semana",
                        "Sesión",
                        "Alumno",
                        "Ejercicio"
                    ],
                    keep=False
                )
            )


            cantidad_duplicados = int(
                duplicados.sum()
            )


            if cantidad_duplicados > 0:

                st.warning(
                    f"🟠 Se detectaron "
                    f"{cantidad_duplicados} "
                    "filas duplicadas."
                )


                st.dataframe(
                    df_historial_fisico[
                        duplicados
                    ],
                    use_container_width=True,
                    hide_index=True
                )


            else:

                st.success(
                    "✅ No hay duplicados por "
                    "Semana + Sesión + Alumno + Ejercicio."
                )


            # =================================================
            # ÚLTIMOS REGISTROS
            # =================================================

            st.markdown(
                "### Últimos registros"
            )


            st.dataframe(
                df_historial_fisico.tail(
                    10
                ),
                use_container_width=True,
                hide_index=True
            )
                    # =====================================================
        # PASO 5A — DASHBOARD FÍSICO INDIVIDUAL
        # =====================================================

        st.divider()

        st.subheader(
            "Dashboard físico individual"
        )

        st.caption(
            "Consulta el trabajo de acondicionamiento físico "
            "registrado por atleta y por bloque."
        )


        if df_historial_fisico.empty:

            st.info(
                "Todavía no existen registros físicos "
                "para generar el dashboard."
            )


        else:

            # =================================================
            # PREPARAR DATOS
            # =================================================

            df_dashboard_fisico = (
                df_historial_fisico.copy()
            )


            columnas_numericas_dashboard = [
                "Semana",
                "Sesión",
                "Series planificadas",
                "Series reales",
                "Repeticiones planificadas",
                "Repeticiones reales",
                "Carga externa planificada",
                "Carga externa real",
                "RPE planificado",
                "RPE real",
                "Dedos",
                "Antebrazo / muñeca",
                "Tracción (espalda/bíceps)",
                "Empuje (pecho/tríceps)",
                "Hombro",
                "Core",
                "Piernas / cadera",
                "Puntaje interferencia"
            ]


            for columna in (
                columnas_numericas_dashboard
            ):

                if columna in (
                    df_dashboard_fisico.columns
                ):

                    df_dashboard_fisico[
                        columna
                    ] = pd.to_numeric(
                        df_dashboard_fisico[
                            columna
                        ],
                        errors="coerce"
                    )


            # =================================================
            # ELIMINAR REGISTROS SIN DATOS BÁSICOS
            # =================================================

            df_dashboard_fisico = (
                df_dashboard_fisico
                .dropna(
                    subset=[
                        "Semana",
                        "Sesión",
                        "Alumno",
                        "Ejercicio"
                    ]
                )
            )


            # =================================================
            # ASIGNAR BLOQUE SEGÚN SEMANA
            # =================================================

            df_dashboard_fisico[
                "Bloque"
            ] = (
                df_dashboard_fisico[
                    "Semana"
                ]
                .apply(
                    lambda semana:
                        obtener_bloque(
                            int(
                                semana
                            )
                        )[0]
                )
            )


            # =================================================
            # CARGA FÍSICA TOTAL POR REGISTRO
            # =================================================

            zonas_dashboard = [
                "Dedos",
                "Antebrazo / muñeca",
                "Tracción (espalda/bíceps)",
                "Empuje (pecho/tríceps)",
                "Hombro",
                "Core",
                "Piernas / cadera"
            ]


            df_dashboard_fisico[
                "Carga física total"
            ] = (
                df_dashboard_fisico[
                    zonas_dashboard
                ]
                .fillna(
                    0
                )
                .sum(
                    axis=1
                )
            )


            # =================================================
            # SELECCIÓN DE BLOQUE
            # =================================================

            bloque_fisico_dashboard = (
                st.selectbox(
                    "Bloque",
                    [
                        1,
                        2,
                        3,
                        4
                    ],
                    index=None,
                    placeholder=(
                        "Selecciona un bloque..."
                    ),
                    key=(
                        "dashboard_fisico_bloque"
                    )
                )
            )


            if bloque_fisico_dashboard is None:

                st.info(
                    "Selecciona un bloque para "
                    "consultar el dashboard físico."
                )


            else:

                # =============================================
                # FILTRAR BLOQUE
                # =============================================

                df_dashboard_bloque = (
                    df_dashboard_fisico[
                        df_dashboard_fisico[
                            "Bloque"
                        ]
                        ==
                        bloque_fisico_dashboard
                    ]
                    .copy()
                )


                if df_dashboard_bloque.empty:

                    st.info(
                        "No hay registros físicos "
                        "para este bloque."
                    )


                else:

                    # =========================================
                    # NOMBRE Y RANGO DEL BLOQUE
                    # =========================================

                    rangos_dashboard = {
                        1: (
                            1,
                            13
                        ),
                        2: (
                            14,
                            26
                        ),
                        3: (
                            27,
                            39
                        ),
                        4: (
                            40,
                            52
                        )
                    }


                    inicio_dashboard, fin_dashboard = (
                        rangos_dashboard[
                            bloque_fisico_dashboard
                        ]
                    )


                    _, nombre_bloque_dashboard = (
                        obtener_bloque(
                            inicio_dashboard
                        )
                    )


                    st.caption(
                        f"Bloque "
                        f"{bloque_fisico_dashboard} · "
                        f"{nombre_bloque_dashboard} · "
                        f"Semanas "
                        f"{inicio_dashboard}–"
                        f"{fin_dashboard}"
                    )


                    # =========================================
                    # SELECCIÓN DE ALUMNO
                    # =========================================

                    alumnos_dashboard_fisico = (
                        sorted(
                            df_dashboard_bloque[
                                "Alumno"
                            ]
                            .dropna()
                            .astype(
                                str
                            )
                            .str.strip()
                            .unique()
                            .tolist()
                        )
                    )


                    alumno_dashboard_fisico = (
                        st.selectbox(
                            "Alumno",
                            alumnos_dashboard_fisico,
                            index=None,
                            placeholder=(
                                "Selecciona un alumno..."
                            ),
                            key=(
                                "dashboard_fisico_alumno"
                            )
                        )
                    )


                    if (
                        alumno_dashboard_fisico
                        is None
                    ):

                        st.info(
                            "Selecciona un alumno "
                            "para ver su seguimiento físico."
                        )


                    else:

                        # =====================================
                        # FILTRAR ALUMNO
                        # =====================================

                        df_dashboard_alumno = (
                            df_dashboard_bloque[
                                df_dashboard_bloque[
                                    "Alumno"
                                ]
                                .astype(
                                    str
                                )
                                .str.strip()
                                ==
                                alumno_dashboard_fisico
                            ]
                            .copy()
                        )


                        # =====================================
                        # MÉTRICAS PRINCIPALES
                        # =====================================

                        semanas_registradas = (
                            df_dashboard_alumno[
                                "Semana"
                            ]
                            .nunique()
                        )


                        sesiones_registradas = (
                            df_dashboard_alumno[
                                [
                                    "Semana",
                                    "Sesión"
                                ]
                            ]
                            .drop_duplicates()
                            .shape[0]
                        )


                        ejercicios_unicos = (
                            df_dashboard_alumno[
                                "Ejercicio"
                            ]
                            .nunique()
                        )


                        carga_fisica_acumulada = (
                            df_dashboard_alumno[
                                "Carga física total"
                            ]
                            .sum()
                        )


                        st.divider()

                        st.subheader(
                            alumno_dashboard_fisico
                        )


                        col_d1, col_d2, col_d3, col_d4 = (
                            st.columns(
                                4
                            )
                        )


                        col_d1.metric(
                            "Semanas registradas",
                            int(
                                semanas_registradas
                            )
                        )


                        col_d2.metric(
                            "Sesiones físicas",
                            int(
                                sesiones_registradas
                            )
                        )


                        col_d3.metric(
                            "Ejercicios diferentes",
                            int(
                                ejercicios_unicos
                            )
                        )


                        col_d4.metric(
                            "Carga física acumulada",
                            f"{carga_fisica_acumulada:.1f}"
                        )


                        # =====================================
                        # RANGO DE SEMANAS REGISTRADAS
                        # =====================================

                        semana_primera = int(
                            df_dashboard_alumno[
                                "Semana"
                            ]
                            .min()
                        )


                        semana_ultima = int(
                            df_dashboard_alumno[
                                "Semana"
                            ]
                            .max()
                        )


                        st.caption(
                            f"Registros disponibles: "
                            f"semana {semana_primera} "
                            f"a semana {semana_ultima}."
                        )


                        # =====================================
                        # RESUMEN SEMANAL
                        # =====================================

                        resumen_fisico_semanal = (
                            df_dashboard_alumno
                            .groupby(
                                "Semana",
                                as_index=False
                            )
                            .agg(
                                {
                                    "Sesión":
                                        "nunique",

                                    "Ejercicio":
                                        "nunique",

                                    "Carga física total":
                                        "sum"
                                }
                            )
                            .rename(
                                columns={
                                    "Sesión":
                                        "Sesiones",

                                    "Ejercicio":
                                        "Ejercicios",

                                    "Carga física total":
                                        "Carga física"
                                }
                            )
                            .sort_values(
                                "Semana"
                            )
                        )


                        resumen_fisico_semanal[
                            "Carga física"
                        ] = (
                            resumen_fisico_semanal[
                                "Carga física"
                            ]
                            .round(
                                1
                            )
                        )


                        # =====================================
                        # GRÁFICA DE CARGA SEMANAL
                        # =====================================

                        st.markdown(
                            "### Carga física por semana"
                        )


                        grafica_carga_fisica = (
                            alt.Chart(
                                resumen_fisico_semanal
                            )
                            .mark_line(
                                point=True
                            )
                            .encode(

                                x=alt.X(
                                    "Semana:Q",
                                    title="Semana"
                                ),

                                y=alt.Y(
                                    "Carga física:Q",
                                    title=(
                                        "Carga física"
                                    )
                                ),

                                tooltip=[
                                    alt.Tooltip(
                                        "Semana:Q",
                                        title="Semana"
                                    ),

                                    alt.Tooltip(
                                        "Carga física:Q",
                                        title=(
                                            "Carga física"
                                        ),
                                        format=".1f"
                                    ),

                                    alt.Tooltip(
                                        "Sesiones:Q",
                                        title="Sesiones"
                                    ),

                                    alt.Tooltip(
                                        "Ejercicios:Q",
                                        title="Ejercicios"
                                    )
                                ]
                            )
                            .properties(
                                height=350
                            )
                            .interactive()
                        )


                        st.altair_chart(
                            grafica_carga_fisica,
                            use_container_width=True
                        )


                        # =====================================
                        # TABLA SEMANAL
                        # =====================================

                        st.markdown(
                            "### Resumen semanal"
                        )


                        st.dataframe(
                            resumen_fisico_semanal,
                            use_container_width=True,
                            hide_index=True
                        )


                        # =====================================
                        # ÚLTIMOS EJERCICIOS REALIZADOS
                        # =====================================

                        st.markdown(
                            "### Actividad física reciente"
                        )


                        columnas_actividad = [
                            "Semana",
                            "Sesión",
                            "Tipo físico",
                            "Momento",
                            "Ejercicio",
                            "Series reales",
                            "Repeticiones reales",
                            "Carga externa real",
                            "RPE real",
                            "Compatibilidad"
                        ]


                        columnas_actividad = [
                            columna
                            for columna in (
                                columnas_actividad
                            )
                            if columna
                            in df_dashboard_alumno.columns
                        ]


                        actividad_reciente = (
                            df_dashboard_alumno
                            .sort_values(
                                [
                                    "Semana",
                                    "Sesión"
                                ],
                                ascending=[
                                    False,
                                    False
                                ]
                            )
                            [
                                columnas_actividad
                            ]
                            .head(
                                10
                            )
                        )


                        st.dataframe(
                            actividad_reciente,
                            use_container_width=True,
                            hide_index=True
                        )
                        # =================================================
                        # PASO 5B — CARGA FÍSICA POR ZONA
                        # =================================================

                        st.divider()

                        st.subheader(
                            "Carga física por zona"
                        )

                        st.caption(
                            "Distribución de la carga acumulada y evolución "
                            "semanal por zona corporal."
                        )


                        # =================================================
                        # CARGA ACUMULADA POR ZONA
                        # =================================================

                        carga_acumulada_zonas = (
                            df_dashboard_alumno[
                                zonas_dashboard
                            ]
                            .fillna(0)
                            .sum()
                        )


                        df_carga_zonas = (
                            carga_acumulada_zonas
                            .reset_index()
                        )


                        df_carga_zonas.columns = [
                            "Zona",
                            "Carga"
                        ]


                        df_carga_zonas[
                            "Carga"
                        ] = (
                            pd.to_numeric(
                                df_carga_zonas[
                                    "Carga"
                                ],
                                errors="coerce"
                            )
                            .fillna(0)
                        )


                        carga_total_zonas = (
                            df_carga_zonas[
                                "Carga"
                            ]
                            .sum()
                        )


                        if carga_total_zonas > 0:

                            df_carga_zonas[
                                "Porcentaje"
                            ] = (
                                df_carga_zonas[
                                    "Carga"
                                ]
                                /
                                carga_total_zonas
                                *
                                100
                            )

                        else:

                            df_carga_zonas[
                                "Porcentaje"
                            ] = 0


                        df_carga_zonas[
                            "Carga"
                        ] = (
                            df_carga_zonas[
                                "Carga"
                            ]
                            .round(1)
                        )


                        df_carga_zonas[
                            "Porcentaje"
                        ] = (
                            df_carga_zonas[
                                "Porcentaje"
                            ]
                            .round(1)
                        )


                        df_carga_zonas = (
                            df_carga_zonas
                            .sort_values(
                                "Carga",
                                ascending=False
                            )
                            .reset_index(
                                drop=True
                            )
                        )


                        # =================================================
                        # MÉTRICAS PRINCIPALES
                        # =================================================

                        zona_mas_cargada = (
                            df_carga_zonas.iloc[0]
                        )


                        zonas_activas = int(
                            (
                                df_carga_zonas[
                                    "Carga"
                                ]
                                >
                                0
                            )
                            .sum()
                        )


                        col_z1, col_z2, col_z3 = (
                            st.columns(3)
                        )


                        col_z1.metric(
                            "Zona más cargada",
                            zona_mas_cargada[
                                "Zona"
                            ]
                        )


                        col_z2.metric(
                            "Carga de esa zona",
                            f"{zona_mas_cargada['Carga']:.1f}"
                        )


                        col_z3.metric(
                            "Participación",
                            f"{zona_mas_cargada['Porcentaje']:.1f}%"
                        )


                        st.caption(
                            f"Zonas con carga registrada: "
                            f"{zonas_activas} de "
                            f"{len(zonas_dashboard)}."
                        )


                        # =================================================
                        # GRÁFICA — CARGA ACUMULADA
                        # =================================================

                        st.markdown(
                            "### Distribución acumulada"
                        )


                        grafica_zonas_acumulada = (
                            alt.Chart(
                                df_carga_zonas
                            )
                            .mark_bar()
                            .encode(

                                x=alt.X(
                                    "Carga:Q",
                                    title="Carga acumulada"
                                ),

                                y=alt.Y(
                                    "Zona:N",
                                    title="",
                                    sort="-x"
                                ),

                                tooltip=[
                                    alt.Tooltip(
                                        "Zona:N",
                                        title="Zona"
                                    ),

                                    alt.Tooltip(
                                        "Carga:Q",
                                        title="Carga",
                                        format=".1f"
                                    ),

                                    alt.Tooltip(
                                        "Porcentaje:Q",
                                        title="% de la carga",
                                        format=".1f"
                                    )
                                ]
                            )
                            .properties(
                                height=350
                            )
                        )


                        st.altair_chart(
                            grafica_zonas_acumulada,
                            use_container_width=True
                        )


                        # =================================================
                        # TABLA DE DISTRIBUCIÓN
                        # =================================================

                        st.dataframe(
                            df_carga_zonas,
                            use_container_width=True,
                            hide_index=True
                        )


                        # =================================================
                        # EVOLUCIÓN SEMANAL POR ZONA
                        # =================================================

                        st.markdown(
                            "### Evolución semanal por zona"
                        )


                        carga_semanal_zonas = (
                            df_dashboard_alumno
                            .groupby(
                                "Semana",
                                as_index=False
                            )[
                                zonas_dashboard
                            ]
                            .sum()
                            .sort_values(
                                "Semana"
                            )
                        )


                        carga_semanal_long = (
                            carga_semanal_zonas
                            .melt(
                                id_vars=[
                                    "Semana"
                                ],
                                value_vars=
                                    zonas_dashboard,
                                var_name="Zona",
                                value_name="Carga"
                            )
                        )


                        carga_semanal_long[
                            "Carga"
                        ] = (
                            pd.to_numeric(
                                carga_semanal_long[
                                    "Carga"
                                ],
                                errors="coerce"
                            )
                            .fillna(0)
                        )


                        grafica_evolucion_zonas = (
                            alt.Chart(
                                carga_semanal_long
                            )
                            .mark_line(
                                point=True
                            )
                            .encode(

                                x=alt.X(
                                    "Semana:Q",
                                    title="Semana"
                                ),

                                y=alt.Y(
                                    "Carga:Q",
                                    title="Carga por zona"
                                ),

                                color=alt.Color(
                                    "Zona:N",
                                    title="Zona"
                                ),

                                tooltip=[
                                    alt.Tooltip(
                                        "Semana:Q",
                                        title="Semana"
                                    ),

                                    alt.Tooltip(
                                        "Zona:N",
                                        title="Zona"
                                    ),

                                    alt.Tooltip(
                                        "Carga:Q",
                                        title="Carga",
                                        format=".1f"
                                    )
                                ]
                            )
                            .properties(
                                height=400
                            )
                            .interactive()
                        )


                        st.altair_chart(
                            grafica_evolucion_zonas,
                            use_container_width=True
                        )


                        # =================================================
                        # FILTRO POR ZONA
                        # =================================================

                        zona_seleccionada_dashboard = (
                            st.selectbox(
                                "Analizar una zona",
                                zonas_dashboard,
                                index=None,
                                placeholder=(
                                    "Selecciona una zona..."
                                ),
                                key=(
                                    "dashboard_fisico_zona"
                                )
                            )
                        )


                        if (
                            zona_seleccionada_dashboard
                            is not None
                        ):

                            df_zona_individual = (
                                carga_semanal_zonas[
                                    [
                                        "Semana",
                                        zona_seleccionada_dashboard
                                    ]
                                ]
                                .copy()
                                .rename(
                                    columns={
                                        zona_seleccionada_dashboard:
                                            "Carga"
                                    }
                                )
                            )


                            carga_zona_total = (
                                df_zona_individual[
                                    "Carga"
                                ]
                                .sum()
                            )


                            carga_zona_media = (
                                df_zona_individual[
                                    "Carga"
                                ]
                                .mean()
                            )


                            carga_zona_maxima = (
                                df_zona_individual[
                                    "Carga"
                                ]
                                .max()
                            )


                            col_za1, col_za2, col_za3 = (
                                st.columns(3)
                            )


                            col_za1.metric(
                                "Carga acumulada",
                                f"{carga_zona_total:.1f}"
                            )


                            col_za2.metric(
                                "Media semanal",
                                f"{carga_zona_media:.1f}"
                            )


                            col_za3.metric(
                                "Máximo semanal",
                                f"{carga_zona_maxima:.1f}"
                            )


                            grafica_zona_individual = (
                                alt.Chart(
                                    df_zona_individual
                                )
                                .mark_line(
                                    point=True
                                )
                                .encode(

                                    x=alt.X(
                                        "Semana:Q",
                                        title="Semana"
                                    ),

                                    y=alt.Y(
                                        "Carga:Q",
                                        title=(
                                            f"Carga · "
                                            f"{zona_seleccionada_dashboard}"
                                        )
                                    ),

                                    tooltip=[
                                        alt.Tooltip(
                                            "Semana:Q",
                                            title="Semana"
                                        ),

                                        alt.Tooltip(
                                            "Carga:Q",
                                            title="Carga",
                                            format=".1f"
                                        )
                                    ]
                                )
                                .properties(
                                    height=320
                                )
                                .interactive()
                            )


                            st.altair_chart(
                                grafica_zona_individual,
                                use_container_width=True
                            )
                        # =================================================
                        # PASO 5C — PLANIFICADO VS REAL
                        # =================================================

                        st.divider()

                        st.subheader(
                            "Planificado vs real"
                        )

                        st.caption(
                            "Compara la ejecución real del acondicionamiento "
                            "con la prescripción original."
                        )


                        # =================================================
                        # PREPARAR DATOS
                        # =================================================

                        df_plan_real = (
                            df_dashboard_alumno.copy()
                        )


                        columnas_plan_real = [
                            "Series planificadas",
                            "Series reales",
                            "Repeticiones planificadas",
                            "Repeticiones reales",
                            "Carga externa planificada",
                            "Carga externa real",
                            "RPE planificado",
                            "RPE real"
                        ]


                        for columna in columnas_plan_real:

                            df_plan_real[
                                columna
                            ] = pd.to_numeric(
                                df_plan_real[
                                    columna
                                ],
                                errors="coerce"
                            ).fillna(0)


                        # =================================================
                        # CUMPLIMIENTO DE SERIES
                        # =================================================

                        series_plan_total = (
                            df_plan_real[
                                "Series planificadas"
                            ]
                            .sum()
                        )


                        series_real_total = (
                            df_plan_real[
                                "Series reales"
                            ]
                            .sum()
                        )


                        if series_plan_total > 0:

                            series_pct = (
                                series_real_total
                                /
                                series_plan_total
                                *
                                100
                            )

                        else:

                            series_pct = 0


                        # =================================================
                        # CUMPLIMIENTO DE REPETICIONES
                        # =================================================

                        reps_plan_total = (
                            df_plan_real[
                                "Repeticiones planificadas"
                            ]
                            .sum()
                        )


                        reps_real_total = (
                            df_plan_real[
                                "Repeticiones reales"
                            ]
                            .sum()
                        )


                        if reps_plan_total > 0:

                            reps_pct = (
                                reps_real_total
                                /
                                reps_plan_total
                                *
                                100
                            )

                        else:

                            reps_pct = 0


                        # =================================================
                        # RPE
                        # =================================================

                        rpe_plan_fisico_medio = (
                            df_plan_real[
                                "RPE planificado"
                            ]
                            .mean()
                        )


                        rpe_real_fisico_medio = (
                            df_plan_real[
                                "RPE real"
                            ]
                            .mean()
                        )


                        dif_rpe_fisico = (
                            rpe_real_fisico_medio
                            -
                            rpe_plan_fisico_medio
                        )


                        # =================================================
                        # CARGA EXTERNA
                        # Solo ejercicios donde existe carga externa
                        # =================================================

                        df_con_carga_externa = (
                            df_plan_real[
                                (
                                    df_plan_real[
                                        "Carga externa planificada"
                                    ]
                                    >
                                    0
                                )
                                |
                                (
                                    df_plan_real[
                                        "Carga externa real"
                                    ]
                                    >
                                    0
                                )
                            ]
                            .copy()
                        )


                        if not df_con_carga_externa.empty:

                            carga_externa_plan_media = (
                                df_con_carga_externa[
                                    "Carga externa planificada"
                                ]
                                .mean()
                            )


                            carga_externa_real_media = (
                                df_con_carga_externa[
                                    "Carga externa real"
                                ]
                                .mean()
                            )


                            dif_carga_externa = (
                                carga_externa_real_media
                                -
                                carga_externa_plan_media
                            )

                        else:

                            carga_externa_plan_media = 0
                            carga_externa_real_media = 0
                            dif_carga_externa = 0


                        # =================================================
                        # KPIs
                        # =================================================

                        col_pr1, col_pr2, col_pr3, col_pr4 = (
                            st.columns(4)
                        )


                        col_pr1.metric(
                            "Series cumplidas",
                            f"{series_pct:.1f}%",
                            delta=(
                                f"{series_real_total - series_plan_total:+.0f} "
                                "series"
                            )
                        )


                        col_pr2.metric(
                            "Repeticiones cumplidas",
                            f"{reps_pct:.1f}%",
                            delta=(
                                f"{reps_real_total - reps_plan_total:+.0f} "
                                "reps"
                            )
                        )


                        col_pr3.metric(
                            "RPE real medio",
                            f"{rpe_real_fisico_medio:.1f}",
                            delta=(
                                f"{dif_rpe_fisico:+.1f} "
                                "vs plan"
                            ),
                            delta_color="inverse"
                        )


                        col_pr4.metric(
                            "Carga externa media",
                            f"{carga_externa_real_media:.1f} kg",
                            delta=(
                                f"{dif_carga_externa:+.1f} kg "
                                "vs plan"
                            )
                        )


                        # =================================================
                        # TRABAJO EXTERNO
                        # Series × reps × kg
                        # =================================================

                        df_plan_real[
                            "Trabajo externo planificado"
                        ] = (
                            df_plan_real[
                                "Series planificadas"
                            ]
                            *
                            df_plan_real[
                                "Repeticiones planificadas"
                            ]
                            *
                            df_plan_real[
                                "Carga externa planificada"
                            ]
                        )


                        df_plan_real[
                            "Trabajo externo real"
                        ] = (
                            df_plan_real[
                                "Series reales"
                            ]
                            *
                            df_plan_real[
                                "Repeticiones reales"
                            ]
                            *
                            df_plan_real[
                                "Carga externa real"
                            ]
                        )


                        trabajo_plan_total = (
                            df_plan_real[
                                "Trabajo externo planificado"
                            ]
                            .sum()
                        )


                        trabajo_real_total = (
                            df_plan_real[
                                "Trabajo externo real"
                            ]
                            .sum()
                        )


                        if trabajo_plan_total > 0:

                            trabajo_pct = (
                                trabajo_real_total
                                /
                                trabajo_plan_total
                                *
                                100
                            )

                        else:

                            trabajo_pct = 0


                        if trabajo_plan_total > 0:

                            st.metric(
                                "Trabajo externo acumulado",
                                f"{trabajo_real_total:.0f} kg",
                                delta=(
                                    f"{trabajo_pct - 100:+.1f}% "
                                    "vs plan"
                                )
                            )


                        # =================================================
                        # RESUMEN SEMANAL
                        # =================================================

                        resumen_plan_real_semana = (
                            df_plan_real
                            .groupby(
                                "Semana",
                                as_index=False
                            )
                            .agg({
                                "Series planificadas":
                                    "sum",

                                "Series reales":
                                    "sum",

                                "Repeticiones planificadas":
                                    "sum",

                                "Repeticiones reales":
                                    "sum",

                                "RPE planificado":
                                    "mean",

                                "RPE real":
                                    "mean",

                                "Trabajo externo planificado":
                                    "sum",

                                "Trabajo externo real":
                                    "sum"
                            })
                            .sort_values(
                                "Semana"
                            )
                        )


                        # =================================================
                        # DIFERENCIA RPE SEMANAL
                        # =================================================

                        resumen_plan_real_semana[
                            "Dif. RPE"
                        ] = (
                            resumen_plan_real_semana[
                                "RPE real"
                            ]
                            -
                            resumen_plan_real_semana[
                                "RPE planificado"
                            ]
                        )


                        # =================================================
                        # GRÁFICA SERIES
                        # =================================================

                        st.markdown(
                            "### Series planificadas vs reales"
                        )


                        series_long = (
                            resumen_plan_real_semana[
                                [
                                    "Semana",
                                    "Series planificadas",
                                    "Series reales"
                                ]
                            ]
                            .melt(
                                id_vars="Semana",
                                var_name="Tipo",
                                value_name="Series"
                            )
                        )


                        grafica_series_fisico = (
                            alt.Chart(
                                series_long
                            )
                            .mark_line(
                                point=True
                            )
                            .encode(

                                x=alt.X(
                                    "Semana:Q",
                                    title="Semana"
                                ),

                                y=alt.Y(
                                    "Series:Q",
                                    title="Series"
                                ),

                                color=alt.Color(
                                    "Tipo:N",
                                    title=""
                                ),

                                tooltip=[
                                    alt.Tooltip(
                                        "Semana:Q",
                                        title="Semana"
                                    ),

                                    alt.Tooltip(
                                        "Tipo:N",
                                        title=""
                                    ),

                                    alt.Tooltip(
                                        "Series:Q",
                                        title="Series",
                                        format=".0f"
                                    )
                                ]
                            )
                            .properties(
                                height=320
                            )
                            .interactive()
                        )


                        st.altair_chart(
                            grafica_series_fisico,
                            use_container_width=True
                        )


                        # =================================================
                        # GRÁFICA REPETICIONES
                        # =================================================

                        st.markdown(
                            "### Repeticiones planificadas vs reales"
                        )


                        reps_long = (
                            resumen_plan_real_semana[
                                [
                                    "Semana",
                                    "Repeticiones planificadas",
                                    "Repeticiones reales"
                                ]
                            ]
                            .melt(
                                id_vars="Semana",
                                var_name="Tipo",
                                value_name="Repeticiones"
                            )
                        )


                        grafica_reps_fisico = (
                            alt.Chart(
                                reps_long
                            )
                            .mark_line(
                                point=True
                            )
                            .encode(

                                x=alt.X(
                                    "Semana:Q",
                                    title="Semana"
                                ),

                                y=alt.Y(
                                    "Repeticiones:Q",
                                    title="Repeticiones"
                                ),

                                color=alt.Color(
                                    "Tipo:N",
                                    title=""
                                ),

                                tooltip=[
                                    alt.Tooltip(
                                        "Semana:Q",
                                        title="Semana"
                                    ),

                                    alt.Tooltip(
                                        "Tipo:N",
                                        title=""
                                    ),

                                    alt.Tooltip(
                                        "Repeticiones:Q",
                                        title="Repeticiones",
                                        format=".0f"
                                    )
                                ]
                            )
                            .properties(
                                height=320
                            )
                            .interactive()
                        )


                        st.altair_chart(
                            grafica_reps_fisico,
                            use_container_width=True
                        )


                        # =================================================
                        # GRÁFICA RPE
                        # =================================================

                        st.markdown(
                            "### RPE planificado vs real"
                        )


                        rpe_fisico_long = (
                            resumen_plan_real_semana[
                                [
                                    "Semana",
                                    "RPE planificado",
                                    "RPE real"
                                ]
                            ]
                            .melt(
                                id_vars="Semana",
                                var_name="Tipo",
                                value_name="RPE"
                            )
                        )


                        grafica_rpe_fisico = (
                            alt.Chart(
                                rpe_fisico_long
                            )
                            .mark_line(
                                point=True
                            )
                            .encode(

                                x=alt.X(
                                    "Semana:Q",
                                    title="Semana"
                                ),

                                y=alt.Y(
                                    "RPE:Q",
                                    title="RPE",
                                    scale=alt.Scale(
                                        domain=[
                                            0,
                                            10
                                        ]
                                    )
                                ),

                                color=alt.Color(
                                    "Tipo:N",
                                    title=""
                                ),

                                tooltip=[
                                    alt.Tooltip(
                                        "Semana:Q",
                                        title="Semana"
                                    ),

                                    alt.Tooltip(
                                        "Tipo:N",
                                        title=""
                                    ),

                                    alt.Tooltip(
                                        "RPE:Q",
                                        title="RPE",
                                        format=".1f"
                                    )
                                ]
                            )
                            .properties(
                                height=320
                            )
                            .interactive()
                        )


                        st.altair_chart(
                            grafica_rpe_fisico,
                            use_container_width=True
                        )


                        # =================================================
                        # TABLA DETALLADA POR EJERCICIO
                        # =================================================

                        st.markdown(
                            "### Detalle por ejercicio"
                        )


                        tabla_plan_real = (
                            df_plan_real[
                                [
                                    "Semana",
                                    "Sesión",
                                    "Ejercicio",
                                    "Series planificadas",
                                    "Series reales",
                                    "Repeticiones planificadas",
                                    "Repeticiones reales",
                                    "Carga externa planificada",
                                    "Carga externa real",
                                    "RPE planificado",
                                    "RPE real"
                                ]
                            ]
                            .copy()
                            .sort_values(
                                [
                                    "Semana",
                                    "Sesión"
                                ],
                                ascending=[
                                    False,
                                    False
                                ]
                            )
                        )


                        st.dataframe(
                            tabla_plan_real,
                            use_container_width=True,
                            hide_index=True
                        )
                        # =================================================
                        # PASO 5D — PROGRESIÓN POR EJERCICIO
                        # =================================================

                        st.divider()

                        st.subheader(
                            "Progresión por ejercicio"
                        )

                        st.caption(
                            "Analiza cómo evoluciona un ejercicio específico "
                            "a lo largo del bloque."
                        )


                        # =================================================
                        # LISTA DE EJERCICIOS DISPONIBLES
                        # =================================================

                        ejercicios_progresion = (
                            df_dashboard_alumno[
                                "Ejercicio"
                            ]
                            .dropna()
                            .astype(str)
                            .str.strip()
                            .unique()
                            .tolist()
                        )

                        ejercicios_progresion = sorted(
                            ejercicios_progresion
                        )


                        ejercicio_progresion = (
                            st.selectbox(
                                "Ejercicio a analizar",
                                ejercicios_progresion,
                                index=None,
                                placeholder=(
                                    "Selecciona un ejercicio..."
                                ),
                                key=(
                                    "dashboard_fisico_ejercicio"
                                )
                            )
                        )


                        if ejercicio_progresion is not None:

                            # =============================================
                            # FILTRAR EJERCICIO
                            # =============================================

                            df_ejercicio_progresion = (
                                df_dashboard_alumno[
                                    df_dashboard_alumno[
                                        "Ejercicio"
                                    ]
                                    .astype(str)
                                    .str.strip()
                                    ==
                                    ejercicio_progresion
                                ]
                                .copy()
                            )


                            # =============================================
                            # ASEGURAR COLUMNAS NUMÉRICAS
                            # =============================================

                            columnas_progresion = [
                                "Semana",
                                "Sesión",
                                "Series planificadas",
                                "Series reales",
                                "Repeticiones planificadas",
                                "Repeticiones reales",
                                "Carga externa planificada",
                                "Carga externa real",
                                "RPE planificado",
                                "RPE real"
                            ]


                            for columna in columnas_progresion:

                                df_ejercicio_progresion[
                                    columna
                                ] = pd.to_numeric(
                                    df_ejercicio_progresion[
                                        columna
                                    ],
                                    errors="coerce"
                                )


                            df_ejercicio_progresion = (
                                df_ejercicio_progresion
                                .dropna(
                                    subset=[
                                        "Semana",
                                        "Sesión"
                                    ]
                                )
                                .sort_values(
                                    [
                                        "Semana",
                                        "Sesión"
                                    ]
                                )
                            )


                            # =============================================
                            # MÉTRICAS DERIVADAS
                            # =============================================

                            df_ejercicio_progresion[
                                "Volumen real"
                            ] = (
                                df_ejercicio_progresion[
                                    "Series reales"
                                ]
                                *
                                df_ejercicio_progresion[
                                    "Repeticiones reales"
                                ]
                            )


                            df_ejercicio_progresion[
                                "Volumen planificado"
                            ] = (
                                df_ejercicio_progresion[
                                    "Series planificadas"
                                ]
                                *
                                df_ejercicio_progresion[
                                    "Repeticiones planificadas"
                                ]
                            )


                            df_ejercicio_progresion[
                                "Trabajo externo real"
                            ] = (
                                df_ejercicio_progresion[
                                    "Volumen real"
                                ]
                                *
                                df_ejercicio_progresion[
                                    "Carga externa real"
                                ]
                            )


                            df_ejercicio_progresion[
                                "Trabajo externo planificado"
                            ] = (
                                df_ejercicio_progresion[
                                    "Volumen planificado"
                                ]
                                *
                                df_ejercicio_progresion[
                                    "Carga externa planificada"
                                ]
                            )


                            # =============================================
                            # PRIMER Y ÚLTIMO REGISTRO
                            # =============================================

                            primer_registro = (
                                df_ejercicio_progresion
                                .iloc[0]
                            )


                            ultimo_registro = (
                                df_ejercicio_progresion
                                .iloc[-1]
                            )


                            # =============================================
                            # KPIs PRINCIPALES
                            # =============================================

                            carga_inicial = float(
                                primer_registro[
                                    "Carga externa real"
                                ]
                            )

                            carga_actual = float(
                                ultimo_registro[
                                    "Carga externa real"
                                ]
                            )


                            volumen_inicial = float(
                                primer_registro[
                                    "Volumen real"
                                ]
                            )

                            volumen_actual = float(
                                ultimo_registro[
                                    "Volumen real"
                                ]
                            )


                            rpe_inicial = float(
                                primer_registro[
                                    "RPE real"
                                ]
                            )

                            rpe_actual = float(
                                ultimo_registro[
                                    "RPE real"
                                ]
                            )


                            sesiones_ejercicio = len(
                                df_ejercicio_progresion
                            )


                            col_e1, col_e2, col_e3, col_e4 = (
                                st.columns(4)
                            )


                            col_e1.metric(
                                "Sesiones registradas",
                                sesiones_ejercicio
                            )


                            col_e2.metric(
                                "Carga externa actual",
                                f"{carga_actual:.1f} kg",
                                delta=(
                                    f"{carga_actual - carga_inicial:+.1f} kg "
                                    "desde el primer registro"
                                )
                            )


                            col_e3.metric(
                                "Volumen actual",
                                f"{volumen_actual:.0f} reps",
                                delta=(
                                    f"{volumen_actual - volumen_inicial:+.0f} "
                                    "reps"
                                )
                            )


                            col_e4.metric(
                                "RPE actual",
                                f"{rpe_actual:.1f}",
                                delta=(
                                    f"{rpe_actual - rpe_inicial:+.1f} "
                                    "desde el inicio"
                                ),
                                delta_color="inverse"
                            )


                            # =============================================
                            # INFORMACIÓN DEL ÚLTIMO REGISTRO
                            # =============================================

                            st.caption(
                                f"Último registro: semana "
                                f"{int(ultimo_registro['Semana'])} · "
                                f"sesión "
                                f"{int(ultimo_registro['Sesión'])}."
                            )


                            # =============================================
                            # RESUMEN SEMANAL DEL EJERCICIO
                            # =============================================

                            resumen_ejercicio_semanal = (
                                df_ejercicio_progresion
                                .groupby(
                                    "Semana",
                                    as_index=False
                                )
                                .agg({
                                    "Series planificadas":
                                        "sum",

                                    "Series reales":
                                        "sum",

                                    "Repeticiones planificadas":
                                        "mean",

                                    "Repeticiones reales":
                                        "mean",

                                    "Carga externa planificada":
                                        "mean",

                                    "Carga externa real":
                                        "mean",

                                    "RPE planificado":
                                        "mean",

                                    "RPE real":
                                        "mean",

                                    "Volumen planificado":
                                        "sum",

                                    "Volumen real":
                                        "sum",

                                    "Trabajo externo planificado":
                                        "sum",

                                    "Trabajo externo real":
                                        "sum"
                                })
                                .sort_values(
                                    "Semana"
                                )
                            )


                            # =============================================
                            # CARGA EXTERNA
                            # =============================================

                            hay_carga_externa = (
                                (
                                    resumen_ejercicio_semanal[
                                        "Carga externa planificada"
                                    ]
                                    >
                                    0
                                )
                                |
                                (
                                    resumen_ejercicio_semanal[
                                        "Carga externa real"
                                    ]
                                    >
                                    0
                                )
                            ).any()


                            if hay_carga_externa:

                                st.markdown(
                                    "### Evolución de carga externa"
                                )


                                carga_ejercicio_long = (
                                    resumen_ejercicio_semanal[
                                        [
                                            "Semana",
                                            "Carga externa planificada",
                                            "Carga externa real"
                                        ]
                                    ]
                                    .melt(
                                        id_vars="Semana",
                                        var_name="Tipo",
                                        value_name="Carga"
                                    )
                                )


                                grafica_carga_ejercicio = (
                                    alt.Chart(
                                        carga_ejercicio_long
                                    )
                                    .mark_line(
                                        point=True
                                    )
                                    .encode(

                                        x=alt.X(
                                            "Semana:Q",
                                            title="Semana"
                                        ),

                                        y=alt.Y(
                                            "Carga:Q",
                                            title="Carga externa (kg)"
                                        ),

                                        color=alt.Color(
                                            "Tipo:N",
                                            title=""
                                        ),

                                        tooltip=[
                                            alt.Tooltip(
                                                "Semana:Q",
                                                title="Semana"
                                            ),

                                            alt.Tooltip(
                                                "Tipo:N",
                                                title=""
                                            ),

                                            alt.Tooltip(
                                                "Carga:Q",
                                                title="kg",
                                                format=".1f"
                                            )
                                        ]
                                    )
                                    .properties(
                                        height=320
                                    )
                                    .interactive()
                                )


                                st.altair_chart(
                                    grafica_carga_ejercicio,
                                    use_container_width=True
                                )


                            # =============================================
                            # VOLUMEN
                            # =============================================

                            st.markdown(
                                "### Evolución del volumen"
                            )


                            volumen_ejercicio_long = (
                                resumen_ejercicio_semanal[
                                    [
                                        "Semana",
                                        "Volumen planificado",
                                        "Volumen real"
                                    ]
                                ]
                                .melt(
                                    id_vars="Semana",
                                    var_name="Tipo",
                                    value_name="Volumen"
                                )
                            )


                            grafica_volumen_ejercicio = (
                                alt.Chart(
                                    volumen_ejercicio_long
                                )
                                .mark_line(
                                    point=True
                                )
                                .encode(

                                    x=alt.X(
                                        "Semana:Q",
                                        title="Semana"
                                    ),

                                    y=alt.Y(
                                        "Volumen:Q",
                                        title=(
                                            "Series × repeticiones"
                                        )
                                    ),

                                    color=alt.Color(
                                        "Tipo:N",
                                        title=""
                                    ),

                                    tooltip=[
                                        alt.Tooltip(
                                            "Semana:Q",
                                            title="Semana"
                                        ),

                                        alt.Tooltip(
                                            "Tipo:N",
                                            title=""
                                        ),

                                        alt.Tooltip(
                                            "Volumen:Q",
                                            title="Volumen",
                                            format=".0f"
                                        )
                                    ]
                                )
                                .properties(
                                    height=320
                                )
                                .interactive()
                            )


                            st.altair_chart(
                                grafica_volumen_ejercicio,
                                use_container_width=True
                            )


                            # =============================================
                            # RPE
                            # =============================================

                            st.markdown(
                                "### Evolución del RPE"
                            )


                            rpe_ejercicio_long = (
                                resumen_ejercicio_semanal[
                                    [
                                        "Semana",
                                        "RPE planificado",
                                        "RPE real"
                                    ]
                                ]
                                .melt(
                                    id_vars="Semana",
                                    var_name="Tipo",
                                    value_name="RPE"
                                )
                            )


                            grafica_rpe_ejercicio = (
                                alt.Chart(
                                    rpe_ejercicio_long
                                )
                                .mark_line(
                                    point=True
                                )
                                .encode(

                                    x=alt.X(
                                        "Semana:Q",
                                        title="Semana"
                                    ),

                                    y=alt.Y(
                                        "RPE:Q",
                                        title="RPE",
                                        scale=alt.Scale(
                                            domain=[
                                                0,
                                                10
                                            ]
                                        )
                                    ),

                                    color=alt.Color(
                                        "Tipo:N",
                                        title=""
                                    ),

                                    tooltip=[
                                        alt.Tooltip(
                                            "Semana:Q",
                                            title="Semana"
                                        ),

                                        alt.Tooltip(
                                            "Tipo:N",
                                            title=""
                                        ),

                                        alt.Tooltip(
                                            "RPE:Q",
                                            title="RPE",
                                            format=".1f"
                                        )
                                    ]
                                )
                                .properties(
                                    height=320
                                )
                                .interactive()
                            )


                            st.altair_chart(
                                grafica_rpe_ejercicio,
                                use_container_width=True
                            )


                            # =============================================
                            # TRABAJO EXTERNO
                            # =============================================

                            if hay_carga_externa:

                                st.markdown(
                                    "### Trabajo externo"
                                )


                                trabajo_ejercicio_long = (
                                    resumen_ejercicio_semanal[
                                        [
                                            "Semana",
                                            "Trabajo externo planificado",
                                            "Trabajo externo real"
                                        ]
                                    ]
                                    .melt(
                                        id_vars="Semana",
                                        var_name="Tipo",
                                        value_name="Trabajo"
                                    )
                                )


                                grafica_trabajo_ejercicio = (
                                    alt.Chart(
                                        trabajo_ejercicio_long
                                    )
                                    .mark_line(
                                        point=True
                                    )
                                    .encode(

                                        x=alt.X(
                                            "Semana:Q",
                                            title="Semana"
                                        ),

                                        y=alt.Y(
                                            "Trabajo:Q",
                                            title=(
                                                "Trabajo externo (kg)"
                                            )
                                        ),

                                        color=alt.Color(
                                            "Tipo:N",
                                            title=""
                                        ),

                                        tooltip=[
                                            alt.Tooltip(
                                                "Semana:Q",
                                                title="Semana"
                                            ),

                                            alt.Tooltip(
                                                "Tipo:N",
                                                title=""
                                            ),

                                            alt.Tooltip(
                                                "Trabajo:Q",
                                                title="Trabajo",
                                                format=".0f"
                                            )
                                        ]
                                    )
                                    .properties(
                                        height=320
                                    )
                                    .interactive()
                                )


                                st.altair_chart(
                                    grafica_trabajo_ejercicio,
                                    use_container_width=True
                                )


                            # =============================================
                            # TABLA HISTÓRICA
                            # =============================================

                            st.markdown(
                                "### Historial del ejercicio"
                            )


                            columnas_historial_ejercicio = [
                                "Semana",
                                "Sesión",
                                "Series planificadas",
                                "Series reales",
                                "Repeticiones planificadas",
                                "Repeticiones reales",
                                "Carga externa planificada",
                                "Carga externa real",
                                "RPE planificado",
                                "RPE real",
                                "Volumen planificado",
                                "Volumen real"
                            ]


                            st.dataframe(
                                df_ejercicio_progresion[
                                    columnas_historial_ejercicio
                                ]
                                .sort_values(
                                    [
                                        "Semana",
                                        "Sesión"
                                    ],
                                    ascending=[
                                        False,
                                        False
                                    ]
                                ),
                                use_container_width=True,
                                hide_index=True
                            )
                                                    # =================================================
                        # PASO 5E — ESCALADA + FÍSICO
                        # =================================================

                        st.divider()

                        st.subheader(
                            "Escalada + acondicionamiento físico"
                        )

                        st.caption(
                            "Analiza en conjunto la carga de escalada, "
                            "la carga física y la compatibilidad de las sesiones."
                        )


                        # =================================================
                        # LEER HISTORIAL DE ESCALADA
                        # =================================================

                        df_escalada_5e = leer_hoja(
                            "Historial semanal"
                        )


                        columnas_escalada_5e = [
                            "Semana",
                            "Sesión",
                            "Volumen planificado",
                            "Volumen real",
                            "RPE planificado",
                            "RPE real",
                            "Carga planificada",
                            "Carga real"
                        ]


                        for columna in columnas_escalada_5e:

                            if columna in df_escalada_5e.columns:

                                df_escalada_5e[
                                    columna
                                ] = pd.to_numeric(
                                    df_escalada_5e[
                                        columna
                                    ],
                                    errors="coerce"
                                )


                        # =================================================
                        # FILTRAR MISMO ALUMNO Y BLOQUE
                        # =================================================

                        df_escalada_alumno_5e = (
                            df_escalada_5e[
                                (
                                    df_escalada_5e[
                                        "Alumno"
                                    ]
                                    .astype(str)
                                    .str.strip()
                                    ==
                                    alumno_dashboard_fisico
                                )
                                &
                                (
                                    df_escalada_5e[
                                        "Semana"
                                    ]
                                    >=
                                    inicio_dashboard
                                )
                                &
                                (
                                    df_escalada_5e[
                                        "Semana"
                                    ]
                                    <=
                                    fin_dashboard
                                )
                            ]
                            .copy()
                        )


                        if df_escalada_alumno_5e.empty:

                            st.info(
                                "No existen registros de escalada "
                                "para este atleta en el bloque seleccionado."
                            )


                        else:

                            # =============================================
                            # RESUMEN SEMANAL ESCALADA
                            # =============================================

                            semanal_escalada_5e = (
                                df_escalada_alumno_5e
                                .groupby(
                                    "Semana",
                                    as_index=False
                                )
                                .agg({
                                    "Carga planificada":
                                        "sum",

                                    "Carga real":
                                        "sum",

                                    "Volumen planificado":
                                        "sum",

                                    "Volumen real":
                                        "sum",

                                    "RPE planificado":
                                        "mean",

                                    "RPE real":
                                        "mean",

                                    "Sesión":
                                        "nunique"
                                })
                                .rename(
                                    columns={
                                        "Sesión":
                                            "Sesiones escalada"
                                    }
                                )
                                .sort_values(
                                    "Semana"
                                )
                            )


                            # =============================================
                            # RESUMEN SEMANAL FÍSICO
                            # =============================================

                            semanal_fisico_5e = (
                                df_dashboard_alumno
                                .groupby(
                                    "Semana",
                                    as_index=False
                                )
                                .agg({
                                    "Carga física total":
                                        "sum",

                                    "RPE planificado":
                                        "mean",

                                    "RPE real":
                                        "mean",

                                    "Sesión":
                                        "nunique"
                                })
                                .rename(
                                    columns={
                                        "Carga física total":
                                            "Carga física",

                                        "RPE planificado":
                                            "RPE físico plan",

                                        "RPE real":
                                            "RPE físico real",

                                        "Sesión":
                                            "Sesiones físico"
                                    }
                                )
                                .sort_values(
                                    "Semana"
                                )
                            )


                            # =============================================
                            # UNIR ESCALADA + FÍSICO
                            # =============================================

                            combinado_5e = pd.merge(
                                semanal_escalada_5e,
                                semanal_fisico_5e,
                                on="Semana",
                                how="outer"
                            )


                            combinado_5e = (
                                combinado_5e
                                .sort_values(
                                    "Semana"
                                )
                            )


                            columnas_rellenar_5e = [
                                "Carga planificada",
                                "Carga real",
                                "Volumen planificado",
                                "Volumen real",
                                "Sesiones escalada",
                                "Carga física",
                                "Sesiones físico"
                            ]


                            for columna in columnas_rellenar_5e:

                                if columna in combinado_5e.columns:

                                    combinado_5e[
                                        columna
                                    ] = (
                                        combinado_5e[
                                            columna
                                        ]
                                        .fillna(0)
                                    )


                            # =============================================
                            # CUMPLIMIENTO ESCALADA
                            # =============================================

                            combinado_5e[
                                "Carga escalada %"
                            ] = combinado_5e.apply(
                                lambda fila:
                                    (
                                        fila[
                                            "Carga real"
                                        ]
                                        /
                                        fila[
                                            "Carga planificada"
                                        ]
                                        *
                                        100
                                    )
                                    if fila[
                                        "Carga planificada"
                                    ] > 0
                                    else 0,
                                axis=1
                            )


                            # =============================================
                            # Δ RPE FÍSICO
                            # =============================================

                            combinado_5e[
                                "Δ RPE físico"
                            ] = (
                                combinado_5e[
                                    "RPE físico real"
                                ]
                                -
                                combinado_5e[
                                    "RPE físico plan"
                                ]
                            )


                            # =============================================
                            # ÍNDICES RELATIVOS 0–100
                            #
                            # No sumamos escalada y físico porque sus
                            # unidades de carga son diferentes.
                            # =============================================

                            max_carga_escalada = (
                                combinado_5e[
                                    "Carga real"
                                ]
                                .max()
                            )


                            max_carga_fisica = (
                                combinado_5e[
                                    "Carga física"
                                ]
                                .max()
                            )


                            if max_carga_escalada > 0:

                                combinado_5e[
                                    "Índice escalada"
                                ] = (
                                    combinado_5e[
                                        "Carga real"
                                    ]
                                    /
                                    max_carga_escalada
                                    *
                                    100
                                )

                            else:

                                combinado_5e[
                                    "Índice escalada"
                                ] = 0


                            if max_carga_fisica > 0:

                                combinado_5e[
                                    "Índice físico"
                                ] = (
                                    combinado_5e[
                                        "Carga física"
                                    ]
                                    /
                                    max_carga_fisica
                                    *
                                    100
                                )

                            else:

                                combinado_5e[
                                    "Índice físico"
                                ] = 0


                            # =================================================
                            # COMPATIBILIDAD POR SESIÓN
                            # =================================================

                            compatibilidad_sesiones_5e = (
                                df_dashboard_alumno[
                                    [
                                        "Semana",
                                        "Sesión",
                                        "Compatibilidad",
                                        "Puntaje interferencia"
                                    ]
                                ]
                                .copy()
                            )


                            compatibilidad_sesiones_5e = (
                                compatibilidad_sesiones_5e
                                .drop_duplicates(
                                    subset=[
                                        "Semana",
                                        "Sesión"
                                    ]
                                )
                            )


                            compatibilidad_sesiones_5e[
                                "Puntaje interferencia"
                            ] = pd.to_numeric(
                                compatibilidad_sesiones_5e[
                                    "Puntaje interferencia"
                                ],
                                errors="coerce"
                            ).fillna(0)


                            sesiones_compatibles = int(
                                (
                                    compatibilidad_sesiones_5e[
                                        "Compatibilidad"
                                    ]
                                    ==
                                    "COMPATIBLE"
                                )
                                .sum()
                            )


                            sesiones_revisar = int(
                                (
                                    compatibilidad_sesiones_5e[
                                        "Compatibilidad"
                                    ]
                                    ==
                                    "REVISAR"
                                )
                                .sum()
                            )


                            sesiones_interferencia = int(
                                (
                                    compatibilidad_sesiones_5e[
                                        "Compatibilidad"
                                    ]
                                    ==
                                    "ALTA INTERFERENCIA"
                                )
                                .sum()
                            )


                            puntaje_interferencia_medio = (
                                compatibilidad_sesiones_5e[
                                    "Puntaje interferencia"
                                ]
                                .mean()
                            )


                            # =================================================
                            # KPIs COMBINADOS
                            # =================================================

                            st.markdown(
                                "### Resumen combinado"
                            )


                            carga_escalada_total_5e = (
                                combinado_5e[
                                    "Carga real"
                                ]
                                .sum()
                            )


                            carga_fisica_total_5e = (
                                combinado_5e[
                                    "Carga física"
                                ]
                                .sum()
                            )


                            col_5e1, col_5e2, col_5e3, col_5e4 = (
                                st.columns(4)
                            )


                            col_5e1.metric(
                                "Carga escalada",
                                f"{carga_escalada_total_5e:.0f}"
                            )


                            col_5e2.metric(
                                "Carga física",
                                f"{carga_fisica_total_5e:.1f}"
                            )


                            col_5e3.metric(
                                "Sesiones alta interferencia",
                                sesiones_interferencia
                            )


                            col_5e4.metric(
                                "Interferencia media",
                                f"{puntaje_interferencia_medio:.1f}"
                            )


                            st.caption(
                                "Carga de escalada y carga física se muestran "
                                "por separado porque utilizan escalas distintas."
                            )


                            # =================================================
                            # COMPATIBILIDAD
                            # =================================================

                            st.markdown(
                                "### Compatibilidad de las sesiones"
                            )


                            col_cp1, col_cp2, col_cp3 = (
                                st.columns(3)
                            )


                            col_cp1.metric(
                                "✅ Compatible",
                                sesiones_compatibles
                            )


                            col_cp2.metric(
                                "🟠 Revisar",
                                sesiones_revisar
                            )


                            col_cp3.metric(
                                "🔴 Alta interferencia",
                                sesiones_interferencia
                            )


                            # =================================================
                            # GRÁFICA — PATRÓN DE CARGA RELATIVO
                            # =================================================

                            st.markdown(
                                "### Patrón semanal de carga"
                            )


                            indices_5e = (
                                combinado_5e[
                                    [
                                        "Semana",
                                        "Índice escalada",
                                        "Índice físico"
                                    ]
                                ]
                                .melt(
                                    id_vars="Semana",
                                    var_name="Tipo",
                                    value_name="Índice"
                                )
                            )


                            grafica_indices_5e = (
                                alt.Chart(
                                    indices_5e
                                )
                                .mark_line(
                                    point=True
                                )
                                .encode(

                                    x=alt.X(
                                        "Semana:Q",
                                        title="Semana"
                                    ),

                                    y=alt.Y(
                                        "Índice:Q",
                                        title=(
                                            "Índice relativo de carga"
                                        ),
                                        scale=alt.Scale(
                                            domain=[
                                                0,
                                                100
                                            ]
                                        )
                                    ),

                                    color=alt.Color(
                                        "Tipo:N",
                                        title=""
                                    ),

                                    tooltip=[
                                        alt.Tooltip(
                                            "Semana:Q",
                                            title="Semana"
                                        ),

                                        alt.Tooltip(
                                            "Tipo:N",
                                            title=""
                                        ),

                                        alt.Tooltip(
                                            "Índice:Q",
                                            title="Índice",
                                            format=".1f"
                                        )
                                    ]
                                )
                                .properties(
                                    height=380
                                )
                                .interactive()
                            )


                            st.altair_chart(
                                grafica_indices_5e,
                                use_container_width=True
                            )


                            st.caption(
                                "100 representa la semana de mayor carga "
                                "registrada dentro del bloque para cada modalidad. "
                                "Sirve para comparar el patrón, no para sumar "
                                "las dos cargas."
                            )


                            # =================================================
                            # TABLA SEMANAL COMBINADA
                            # =================================================

                            st.markdown(
                                "### Resumen semanal combinado"
                            )


                            tabla_5e = (
                                combinado_5e[
                                    [
                                        "Semana",
                                        "Carga real",
                                        "Carga escalada %",
                                        "RPE real",
                                        "Carga física",
                                        "RPE físico real",
                                        "Δ RPE físico",
                                        "Índice escalada",
                                        "Índice físico"
                                    ]
                                ]
                                .copy()
                            )


                            tabla_5e = tabla_5e.rename(
                                columns={
                                    "Carga real":
                                        "Carga escalada real",

                                    "RPE real":
                                        "RPE escalada"
                                }
                            )


                            columnas_redondear_5e = [
                                "Carga escalada real",
                                "Carga escalada %",
                                "RPE escalada",
                                "Carga física",
                                "RPE físico real",
                                "Δ RPE físico",
                                "Índice escalada",
                                "Índice físico"
                            ]


                            for columna in columnas_redondear_5e:

                                tabla_5e[
                                    columna
                                ] = (
                                    pd.to_numeric(
                                        tabla_5e[
                                            columna
                                        ],
                                        errors="coerce"
                                    )
                                    .round(1)
                                )


                            st.dataframe(
                                tabla_5e,
                                use_container_width=True,
                                hide_index=True
                            )


                            # =================================================
                            # COACH INSIGHTS COMBINADOS
                            # =================================================

                            st.markdown(
                                "### Coach Insights combinados"
                            )


                            # ---------------------------------------------
                            # DATOS GENERALES
                            # ---------------------------------------------

                            carga_escalada_plan_total = (
                                combinado_5e[
                                    "Carga planificada"
                                ]
                                .sum()
                            )


                            if carga_escalada_plan_total > 0:

                                carga_escalada_pct_total = (
                                    carga_escalada_total_5e
                                    /
                                    carga_escalada_plan_total
                                    *
                                    100
                                )

                            else:

                                carga_escalada_pct_total = 0


                            rpe_fisico_plan_medio_5e = (
                                df_dashboard_alumno[
                                    "RPE planificado"
                                ]
                                .mean()
                            )


                            rpe_fisico_real_medio_5e = (
                                df_dashboard_alumno[
                                    "RPE real"
                                ]
                                .mean()
                            )


                            dif_rpe_fisico_5e = (
                                rpe_fisico_real_medio_5e
                                -
                                rpe_fisico_plan_medio_5e
                            )


                            # ---------------------------------------------
                            # 1. ALTA INTERFERENCIA
                            # ---------------------------------------------

                            if sesiones_interferencia > 0:

                                st.error(
                                    f"🔴 Se registraron "
                                    f"{sesiones_interferencia} sesión(es) "
                                    "con alta interferencia entre escalada "
                                    "y acondicionamiento físico."
                                )

                                st.write(
                                    "Conviene revisar qué zonas se repiten "
                                    "entre ambos estímulos y si el trabajo "
                                    "físico puede moverse después de escalar "
                                    "o reducirse en esas sesiones."
                                )


                            # ---------------------------------------------
                            # 2. ESCALADA ALTA + RPE FÍSICO ALTO
                            # ---------------------------------------------

                            if (
                                carga_escalada_pct_total > 110
                                and
                                dif_rpe_fisico_5e >= 1
                            ):

                                st.warning(
                                    "🟠 La carga de escalada está por encima "
                                    "del plan y el RPE físico también supera "
                                    "lo previsto."
                                )

                                st.write(
                                    "Antes de aumentar el estímulo, conviene "
                                    "mantener o reducir temporalmente alguna "
                                    "de las dos cargas."
                                )


                            # ---------------------------------------------
                            # 3. BUENA RESPUESTA GENERAL
                            # ---------------------------------------------

                            elif (
                                90
                                <=
                                carga_escalada_pct_total
                                <=
                                110
                                and
                                abs(
                                    dif_rpe_fisico_5e
                                )
                                <
                                1
                                and
                                sesiones_interferencia == 0
                            ):

                                st.success(
                                    "✅ La respuesta combinada está cerca "
                                    "de lo planificado."
                                )

                                st.write(
                                    "La carga de escalada se mantiene en rango, "
                                    "el RPE físico está cerca del objetivo "
                                    "y no hay sesiones de alta interferencia."
                                )


                            # ---------------------------------------------
                            # 4. SESIONES A REVISAR
                            # ---------------------------------------------

                            if (
                                sesiones_revisar > 0
                                and
                                sesiones_interferencia == 0
                            ):

                                st.info(
                                    f"🟠 Hay {sesiones_revisar} sesión(es) "
                                    "clasificadas como REVISAR."
                                )

                                st.write(
                                    "No necesariamente implica exceso de carga, "
                                    "pero sí una coincidencia relevante entre "
                                    "las zonas trabajadas en físico y escalada."
                                )


                            # ---------------------------------------------
                            # 5. CAMBIO SIMULTÁNEO DE CARGAS
                            # ---------------------------------------------

                            combinado_tendencia_5e = (
                                combinado_5e[
                                    (
                                        combinado_5e[
                                            "Carga real"
                                        ]
                                        >
                                        0
                                    )
                                    &
                                    (
                                        combinado_5e[
                                            "Carga física"
                                        ]
                                        >
                                        0
                                    )
                                ]
                                .sort_values(
                                    "Semana"
                                )
                            )


                            if len(
                                combinado_tendencia_5e
                            ) >= 2:

                                primera_5e = (
                                    combinado_tendencia_5e
                                    .iloc[0]
                                )

                                ultima_5e = (
                                    combinado_tendencia_5e
                                    .iloc[-1]
                                )


                                if (
                                    primera_5e[
                                        "Carga real"
                                    ] > 0
                                    and
                                    primera_5e[
                                        "Carga física"
                                    ] > 0
                                ):

                                    cambio_escalada_5e = (
                                        (
                                            ultima_5e[
                                                "Carga real"
                                            ]
                                            -
                                            primera_5e[
                                                "Carga real"
                                            ]
                                        )
                                        /
                                        primera_5e[
                                            "Carga real"
                                        ]
                                        *
                                        100
                                    )


                                    cambio_fisico_5e = (
                                        (
                                            ultima_5e[
                                                "Carga física"
                                            ]
                                            -
                                            primera_5e[
                                                "Carga física"
                                            ]
                                        )
                                        /
                                        primera_5e[
                                            "Carga física"
                                        ]
                                        *
                                        100
                                    )


                                    if (
                                        cambio_escalada_5e > 20
                                        and
                                        cambio_fisico_5e > 20
                                    ):

                                        st.warning(
                                            "🟠 La carga de escalada y la "
                                            "carga física han aumentado "
                                            "simultáneamente más de 20% "
                                            "entre los registros comparados."
                                        )

                                        st.write(
                                            "Comprueba que este incremento "
                                            "simultáneo forme parte de la "
                                            "progresión planificada antes "
                                            "de seguir aumentando."
                                        )


    except Exception as error:

        st.error(
            "No se pudo verificar el historial físico."
        )

        st.code(
            str(
                error
            )
        )


# =========================================================
# REGISTRAR SESIÓN
# =========================================================

elif pagina == "Registrar sesión":

    st.title(
        "Registrar sesión"
    )

    plan = (
        st.session_state.get(
            "sesion_planificada"
        )
    )

    if not plan:
        st.warning(
            "Primero crea una sesión en 'Planear sesión'."
        )

        st.stop()
    # =====================================================
    # ACONDICIONAMIENTO PLANIFICADO
    # =====================================================

    acondicionamiento_plan = plan.get(
        "Acondicionamiento",
        {}
    )

    ejercicios_fisicos_plan = (
        acondicionamiento_plan.get(
            "Ejercicios",
            []
        )
    )

    fisico_activo = (
        acondicionamiento_plan.get(
            "Activo",
            False
        )
        and
        len(ejercicios_fisicos_plan) > 0
    )
    st.info(
        f"Semana {plan['Semana']} · "
        f"Sesión {plan['Sesión']} · "
        f"{plan['Tipo']}"
    )

    col1, col2, col3 = (
        st.columns(
            3
        )
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

    presentes = (
        st.multiselect(
            "Alumnos presentes",
            alumnos,
            default=[]
        )
    )

    st.divider()

    resultados = []

    # Aquí guardaremos temporalmente
    # el físico real de cada alumno
    resultados_fisicos = []
    for alumno in presentes:

        st.subheader(
            alumno
        )

        col1, col2 = (
            st.columns(
                2
            )
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
                ),
        })
        # =================================================
        # PASO 4B — REGISTRAR ACONDICIONAMIENTO REAL
        # =================================================

        if fisico_activo:

            st.markdown(
                "#### Acondicionamiento físico"
            )

            st.caption(
                f"{acondicionamiento_plan.get('Tipo', '')} · "
                f"{acondicionamiento_plan.get('Momento', '')}"
            )


            for indice_fisico, ejercicio_plan in enumerate(
                ejercicios_fisicos_plan
            ):

                nombre_ejercicio_fisico = (
                    ejercicio_plan.get(
                        "Ejercicio",
                        "Ejercicio"
                    )
                )


                with st.expander(
                    f"🏋️ {nombre_ejercicio_fisico}",
                    expanded=False
                ):

                    # =========================================
                    # PLANIFICADO
                    # =========================================

                    series_plan = int(
                        ejercicio_plan.get(
                            "Series",
                            0
                        )
                    )

                    reps_plan = int(
                        ejercicio_plan.get(
                            "Repeticiones",
                            0
                        )
                    )

                    carga_plan = float(
                        ejercicio_plan.get(
                            "Carga externa",
                            0
                        )
                    )

                    rpe_plan_fisico = float(
                        ejercicio_plan.get(
                            "RPE objetivo",
                            0
                        )
                    )


                    st.caption(
                        f"Plan: "
                        f"{series_plan} × {reps_plan} · "
                        f"{carga_plan:.1f} kg · "
                        f"RPE {rpe_plan_fisico:.1f}"
                    )


                    # =========================================
                    # SERIES Y REPETICIONES REALES
                    # =========================================

                    col_fs1, col_fs2 = st.columns(2)


                    series_reales_fisico = (
                        col_fs1.number_input(
                            "Series reales",
                            min_value=0,
                            max_value=20,
                            value=series_plan,
                            step=1,
                            key=(
                                f"fis_series_"
                                f"{plan['Semana']}_"
                                f"{plan['Sesión']}_"
                                f"{alumno}_"
                                f"{indice_fisico}"
                            )
                        )
                    )


                    repeticiones_reales_fisico = (
                        col_fs2.number_input(
                            "Repeticiones reales",
                            min_value=0,
                            max_value=100,
                            value=reps_plan,
                            step=1,
                            key=(
                                f"fis_reps_"
                                f"{plan['Semana']}_"
                                f"{plan['Sesión']}_"
                                f"{alumno}_"
                                f"{indice_fisico}"
                            )
                        )
                    )


                    # =========================================
                    # CARGA Y RPE REALES
                    # =========================================

                    col_fs3, col_fs4 = st.columns(2)


                    carga_real_fisico = (
                        col_fs3.number_input(
                            "Carga externa real (kg)",
                            min_value=0.0,
                            value=carga_plan,
                            step=0.5,
                            key=(
                                f"fis_carga_"
                                f"{plan['Semana']}_"
                                f"{plan['Sesión']}_"
                                f"{alumno}_"
                                f"{indice_fisico}"
                            )
                        )
                    )


                    rpe_real_fisico = (
                        col_fs4.number_input(
                            "RPE real",
                            min_value=0.0,
                            max_value=10.0,
                            value=rpe_plan_fisico,
                            step=0.5,
                            key=(
                                f"fis_rpe_"
                                f"{plan['Semana']}_"
                                f"{plan['Sesión']}_"
                                f"{alumno}_"
                                f"{indice_fisico}"
                            )
                        )
                    )


                    # =========================================
                    # GUARDAR TEMPORALMENTE
                    # =========================================

                    resultados_fisicos.append(
                        {
                            "Alumno":
                                alumno,

                            "Tipo de sesión":
                                plan[
                                    "Tipo"
                                ],

                            "Tipo físico":
                                acondicionamiento_plan.get(
                                    "Tipo",
                                    ""
                                ),

                            "Momento":
                                acondicionamiento_plan.get(
                                    "Momento",
                                    ""
                                ),

                            "Ejercicio":
                                nombre_ejercicio_fisico,

                            "Series planificadas":
                                series_plan,

                            "Series reales":
                                int(
                                    series_reales_fisico
                                ),

                            "Repeticiones planificadas":
                                reps_plan,

                            "Repeticiones reales":
                                int(
                                    repeticiones_reales_fisico
                                ),

                            "Carga externa planificada":
                                carga_plan,

                            "Carga externa real":
                                float(
                                    carga_real_fisico
                                ),

                            "RPE planificado":
                                rpe_plan_fisico,

                            "RPE real":
                                float(
                                    rpe_real_fisico
                                ),

                            "Compatibilidad":
                                acondicionamiento_plan
                                .get(
                                    "Compatibilidad",
                                    {}
                                )
                                .get(
                                    "Nivel",
                                    ""
                                ),

                            "Puntaje interferencia":
                                acondicionamiento_plan
                                .get(
                                    "Compatibilidad",
                                    {}
                                )
                                .get(
                                    "Puntaje",
                                    0
                                )
                        }
                    )

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

            # =================================================
            # CONTADORES ESCALADA
            # =================================================

            guardados = 0
            actualizados = 0


            # =================================================
            # CONTADORES FÍSICO
            # =================================================

            guardados_fisicos = 0
            actualizados_fisicos = 0


            errores = []


            with st.spinner(
                "Guardando sesión..."
            ):

                # =================================================
                # GUARDAR ESCALADA
                # =================================================

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


                        if accion == "creado":

                            guardados += 1

                        else:

                            actualizados += 1


                    except Exception as error:

                        errores.append(
                            f"Escalada · "
                            f"{resultado['Alumno']}: "
                            f"{str(error)}"
                        )


                # =================================================
                # ACTUALIZAR SEGUIMIENTO DE ESCALADA
                # =================================================

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


                # =================================================
                # PASO 4C — GUARDAR HISTORIAL FÍSICO
                # =================================================

                for registro_fisico in resultados_fisicos:

                    try:

                        # =========================================
                        # CALCULAR CARGA REAL POR ZONA
                        # DE ESTE EJERCICIO
                        # =========================================

                        ejercicio_para_carga = {
                            "Ejercicio":
                                registro_fisico[
                                    "Ejercicio"
                                ],

                            "Series":
                                registro_fisico[
                                    "Series reales"
                                ]
                        }


                        resultado_carga_ejercicio = (
                            calcular_carga_fisica(
                                [
                                    ejercicio_para_carga
                                ],
                                registro_fisico[
                                    "Momento"
                                ],
                                df_ejercicios_fisico,
                                df_reglas_fisico
                            )
                        )


                        carga_zonas_ejercicio = (
                            resultado_carga_ejercicio[
                                "Resultados"
                            ]
                        )


                        # =========================================
                        # GUARDAR EN HISTORIAL FÍSICO
                        # =========================================

                        accion_fisica = (
                            guardar_historial_fisico(

                                plan[
                                    "Semana"
                                ],

                                plan[
                                    "Sesión"
                                ],

                                registro_fisico[
                                    "Alumno"
                                ],

                                registro_fisico[
                                    "Tipo de sesión"
                                ],

                                registro_fisico[
                                    "Tipo físico"
                                ],

                                registro_fisico[
                                    "Momento"
                                ],

                                registro_fisico[
                                    "Ejercicio"
                                ],

                                registro_fisico[
                                    "Series planificadas"
                                ],

                                registro_fisico[
                                    "Series reales"
                                ],

                                registro_fisico[
                                    "Repeticiones planificadas"
                                ],

                                registro_fisico[
                                    "Repeticiones reales"
                                ],

                                registro_fisico[
                                    "Carga externa planificada"
                                ],

                                registro_fisico[
                                    "Carga externa real"
                                ],

                                registro_fisico[
                                    "RPE planificado"
                                ],

                                registro_fisico[
                                    "RPE real"
                                ],

                                carga_zonas_ejercicio,

                                registro_fisico[
                                    "Compatibilidad"
                                ],

                                registro_fisico[
                                    "Puntaje interferencia"
                                ]
                            )
                        )


                        if accion_fisica == "creado":

                            guardados_fisicos += 1

                        else:

                            actualizados_fisicos += 1


                    except Exception as error:

                        errores.append(
                            f"Físico · "
                            f"{registro_fisico['Alumno']} · "
                            f"{registro_fisico['Ejercicio']}: "
                            f"{str(error)}"
                        )


            # =================================================
            # RESULTADOS ESCALADA
            # =================================================

            if guardados:

                st.success(
                    f"✅ {guardados} registro(s) "
                    "de escalada guardados."
                )


            if actualizados:

                st.info(
                    f"🔄 {actualizados} registro(s) "
                    "de escalada actualizados."
                )


            # =================================================
            # RESULTADOS FÍSICO
            # =================================================

            if guardados_fisicos:

                st.success(
                    f"✅ {guardados_fisicos} registro(s) "
                    "de acondicionamiento físico guardados."
                )


            if actualizados_fisicos:

                st.info(
                    f"🔄 {actualizados_fisicos} registro(s) "
                    "de acondicionamiento físico actualizados."
                )


            # =================================================
            # FINAL
            # =================================================

            if not errores:

                st.success(
                    "✅ Historial semanal actualizado."
                )

                st.success(
                    "✅ Historial físico actualizado."
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

    st.caption(
        "Compara la planificación con la ejecución real "
        "y analiza la evolución semanal del atleta."
    )

    df_historial = (
        leer_hoja(
            "Historial semanal"
        )
    )

    columnas_numericas = [
        "Semana",
        "Sesión",
        "Volumen planificado",
        "Volumen real",
        "RPE planificado",
        "RPE real",
        "Carga planificada",
        "Carga real",
    ]

    for columna in columnas_numericas:
        if columna in df_historial.columns:
            df_historial[
                columna
            ] = (
                pd.to_numeric(
                    df_historial[
                        columna
                    ],
                    errors="coerce"
                )
            )

    bloque_analisis = (
        st.selectbox(
            "Bloque",
            [
                1,
                2,
                3,
                4
            ],
            index=None,
            placeholder="Selecciona un bloque..."
        )
    )

    if bloque_analisis is None:
        st.info(
            "Selecciona un bloque para consultar el seguimiento."
        )

        st.stop()

    rangos = {
        1: (1, 13),
        2: (14, 26),
        3: (27, 39),
        4: (40, 52),
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
                >=
                inicio
            )
            &
            (
                df_historial[
                    "Semana"
                ]
                <=
                fin
            )
        ]
        .copy()
    )

    if df_bloque.empty:
        st.info(
            "No hay datos para este bloque."
        )

        st.stop()

    alumno = (
        st.selectbox(
            "Alumno",
            sorted(
                df_bloque[
                    "Alumno"
                ]
                .dropna()
                .astype(str)
                .unique()
            ),
            index=None,
            placeholder="Selecciona un alumno..."
        )
    )

    if alumno is None:
        st.info(
            "Selecciona un alumno para ver su seguimiento."
        )

        st.stop()

    df_alumno = (
        df_bloque[
            df_bloque[
                "Alumno"
            ]
            .astype(str)
            ==
            alumno
        ]
        .copy()
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
                "sum",
        })
        .sort_values(
            "Semana"
        )
    )

    resumen[
        "Volumen %"
    ] = (
        resumen[
            "Volumen real"
        ]
        /
        resumen[
            "Volumen planificado"
        ]
        *
        100
    )

    resumen[
        "Carga %"
    ] = (
        resumen[
            "Carga real"
        ]
        /
        resumen[
            "Carga planificada"
        ]
        *
        100
    )

    resumen[
        "Dif. RPE"
    ] = (
        resumen[
            "RPE real"
        ]
        -
        resumen[
            "RPE planificado"
        ]
    )

    volumen_plan_total = (
        resumen[
            "Volumen planificado"
        ]
        .sum()
    )

    volumen_real_total = (
        resumen[
            "Volumen real"
        ]
        .sum()
    )

    carga_plan_total = (
        resumen[
            "Carga planificada"
        ]
        .sum()
    )

    carga_real_total = (
        resumen[
            "Carga real"
        ]
        .sum()
    )

    volumen_pct_total = (
        volumen_real_total
        /
        volumen_plan_total
        *
        100
        if volumen_plan_total > 0
        else 0
    )

    carga_pct_total = (
        carga_real_total
        /
        carga_plan_total
        *
        100
        if carga_plan_total > 0
        else 0
    )

    rpe_plan_total = (
        resumen[
            "RPE planificado"
        ]
        .mean()
    )

    rpe_real_total = (
        resumen[
            "RPE real"
        ]
        .mean()
    )

    dif_rpe_total = (
        rpe_real_total
        -
        rpe_plan_total
    )

    sesiones_realizadas = (
        len(
            df_alumno
        )
    )

    ultima_semana = (
        resumen
        .iloc[-1]
    )

    st.divider()

    st.subheader(
        alumno
    )

    st.caption(
        f"Bloque {bloque_analisis} · "
        f"Semanas {inicio}–{fin} · "
        f"{sesiones_realizadas} sesiones registradas"
    )

    col1, col2, col3, col4 = (
        st.columns(
            4
        )
    )

    col1.metric(
        "Volumen cumplido",
        f"{volumen_pct_total:.1f}%",
        delta=(
            f"{volumen_pct_total - 100:+.1f}% "
            "vs plan"
        )
    )

    col2.metric(
        "Carga cumplida",
        f"{carga_pct_total:.1f}%",
        delta=(
            f"{carga_pct_total - 100:+.1f}% "
            "vs plan"
        )
    )

    col3.metric(
        "RPE medio",
        f"{rpe_real_total:.1f}",
        delta=(
            f"{dif_rpe_total:+.1f} "
            "vs plan"
        ),
        delta_color="inverse"
    )

    col4.metric(
        "Última semana",
        int(
            ultima_semana[
                "Semana"
            ]
        ),
        delta=(
            f"{ultima_semana['Carga %']:.1f}% "
            "carga"
        )
    )

    st.divider()

    st.subheader(
        "Coach Insights"
    )

    st.caption(
        "Interpretación automática de la respuesta del atleta "
        "respecto a la planificación."
    )

    insights = (
        generar_coach_insights(
            resumen
        )
    )

    for insight in insights:

        nivel = (
            insight[
                "nivel"
            ]
        )

        titulo = (
            insight[
                "titulo"
            ]
        )

        mensaje = (
            insight[
                "mensaje"
            ]
        )

        accion = (
            insight[
                "accion"
            ]
        )

        with st.container(
            border=True
        ):

            if nivel == "POSITIVO":
                st.markdown(
                    f"### ✅ {titulo}"
                )

                st.write(
                    mensaje
                )

                st.success(
                    f"**Acción sugerida:** {accion}"
                )

            elif nivel == "ALERTA":
                st.markdown(
                    f"### 🔴 {titulo}"
                )

                st.write(
                    mensaje
                )

                st.error(
                    f"**Acción sugerida:** {accion}"
                )

            elif nivel == "ATENCION":
                st.markdown(
                    f"### 🟠 {titulo}"
                )

                st.write(
                    mensaje
                )

                st.warning(
                    f"**Acción sugerida:** {accion}"
                )

            else:
                st.markdown(
                    f"### 🔵 {titulo}"
                )

                st.write(
                    mensaje
                )

                st.info(
                    f"**Acción sugerida:** {accion}"
                )

    st.divider()

    st.subheader(
        "Última semana registrada"
    )

    col1, col2, col3 = (
        st.columns(
            3
        )
    )

    col1.metric(
        "Volumen",
        f"{ultima_semana['Volumen %']:.1f}%"
    )

    col2.metric(
        "Carga",
        f"{ultima_semana['Carga %']:.1f}%"
    )

    col3.metric(
        "Δ RPE",
        f"{ultima_semana['Dif. RPE']:+.1f}"
    )

    st.divider()

    tab_volumen, tab_carga, tab_rpe, tab_tabla = (
        st.tabs(
            [
                "Volumen",
                "Carga",
                "RPE",
                "Datos semanales"
            ]
        )
    )

    with tab_volumen:

        st.subheader(
            "Volumen planificado vs real"
        )

        volumen_long = (
            resumen[
                [
                    "Semana",
                    "Volumen planificado",
                    "Volumen real"
                ]
            ]
            .melt(
                id_vars="Semana",
                var_name="Tipo",
                value_name="Volumen"
            )
        )

        grafica_volumen = (
            alt.Chart(
                volumen_long
            )
            .mark_line(
                point=True
            )
            .encode(
                x=alt.X(
                    "Semana:Q",
                    title="Semana"
                ),

                y=alt.Y(
                    "Volumen:Q",
                    title="Volumen"
                ),

                color=alt.Color(
                    "Tipo:N",
                    title=""
                ),

                tooltip=[
                    alt.Tooltip(
                        "Semana:Q",
                        title="Semana"
                    ),
                    alt.Tooltip(
                        "Tipo:N",
                        title=""
                    ),
                    alt.Tooltip(
                        "Volumen:Q",
                        title="Volumen",
                        format=".0f"
                    ),
                ]
            )
            .properties(
                height=400
            )
            .interactive()
        )

        st.altair_chart(
            grafica_volumen,
            use_container_width=True
        )

        st.caption(
            "El objetivo es observar si el volumen real se mantiene cerca "
            "de la planificación a lo largo del bloque."
        )

    with tab_carga:

        st.subheader(
            "Carga planificada vs real"
        )

        carga_long = (
            resumen[
                [
                    "Semana",
                    "Carga planificada",
                    "Carga real"
                ]
            ]
            .melt(
                id_vars="Semana",
                var_name="Tipo",
                value_name="Carga"
            )
        )

        grafica_carga = (
            alt.Chart(
                carga_long
            )
            .mark_line(
                point=True
            )
            .encode(
                x=alt.X(
                    "Semana:Q",
                    title="Semana"
                ),

                y=alt.Y(
                    "Carga:Q",
                    title="Carga"
                ),

                color=alt.Color(
                    "Tipo:N",
                    title=""
                ),

                tooltip=[
                    alt.Tooltip(
                        "Semana:Q",
                        title="Semana"
                    ),
                    alt.Tooltip(
                        "Tipo:N",
                        title=""
                    ),
                    alt.Tooltip(
                        "Carga:Q",
                        title="Carga",
                        format=".0f"
                    ),
                ]
            )
            .properties(
                height=400
            )
            .interactive()
        )

        st.altair_chart(
            grafica_carga,
            use_container_width=True
        )

        st.caption(
            "La carga combina el volumen realizado con el RPE reportado."
        )

    with tab_rpe:

        st.subheader(
            "RPE planificado vs real"
        )

        rpe_long = (
            resumen[
                [
                    "Semana",
                    "RPE planificado",
                    "RPE real"
                ]
            ]
            .melt(
                id_vars="Semana",
                var_name="Tipo",
                value_name="RPE"
            )
        )

        grafica_rpe = (
            alt.Chart(
                rpe_long
            )
            .mark_line(
                point=True
            )
            .encode(
                x=alt.X(
                    "Semana:Q",
                    title="Semana"
                ),

                y=alt.Y(
                    "RPE:Q",
                    title="RPE",
                    scale=alt.Scale(
                        domain=[
                            0,
                            10
                        ]
                    )
                ),

                color=alt.Color(
                    "Tipo:N",
                    title=""
                ),

                tooltip=[
                    alt.Tooltip(
                        "Semana:Q",
                        title="Semana"
                    ),
                    alt.Tooltip(
                        "Tipo:N",
                        title=""
                    ),
                    alt.Tooltip(
                        "RPE:Q",
                        title="RPE",
                        format=".1f"
                    ),
                ]
            )
            .properties(
                height=400
            )
            .interactive()
        )

        st.altair_chart(
            grafica_rpe,
            use_container_width=True
        )

        st.caption(
            "Una separación creciente entre RPE planificado y RPE real "
            "indica que la respuesta del atleta está cambiando respecto al plan."
        )

    with tab_tabla:

        st.subheader(
            "Cumplimiento semanal"
        )

        tabla = (
            resumen[
                [
                    "Semana",
                    "Volumen planificado",
                    "Volumen real",
                    "Volumen %",
                    "RPE planificado",
                    "RPE real",
                    "Dif. RPE",
                    "Carga planificada",
                    "Carga real",
                    "Carga %",
                ]
            ]
            .copy()
        )

        tabla[
            "Volumen %"
        ] = (
            tabla[
                "Volumen %"
            ]
            .round(
                1
            )
        )

        tabla[
            "Carga %"
        ] = (
            tabla[
                "Carga %"
            ]
            .round(
                1
            )
        )

        tabla[
            "RPE planificado"
        ] = (
            tabla[
                "RPE planificado"
            ]
            .round(
                1
            )
        )

        tabla[
            "RPE real"
        ] = (
            tabla[
                "RPE real"
            ]
            .round(
                1
            )
        )

        tabla[
            "Dif. RPE"
        ] = (
            tabla[
                "Dif. RPE"
            ]
            .round(
                1
            )
        )

        st.dataframe(
            tabla,
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    st.subheader(
        "Relación Volumen – RPE"
    )

    st.caption(
        "Cada punto representa una semana registrada. "
        "La posición muestra cuánto volumen produjo el atleta "
        "para el nivel de esfuerzo percibido."
    )

    scatter_data = (
        resumen[
            [
                "Semana",
                "Volumen real",
                "RPE real",
                "Volumen %",
                "Carga %",
                "Dif. RPE",
            ]
        ]
        .copy()
    )

    scatter_data = (
        scatter_data
        .dropna(
            subset=[
                "Semana",
                "Volumen real",
                "RPE real"
            ]
        )
    )

    scatter_data[
        "Semana texto"
    ] = (
        "Semana "
        +
        scatter_data[
            "Semana"
        ]
        .astype(int)
        .astype(str)
    )

    scatter_volumen_rpe = (
        alt.Chart(
            scatter_data
        )
        .mark_circle(
            size=180,
            opacity=0.85
        )
        .encode(
            x=alt.X(
                "Volumen real:Q",
                title="Volumen real"
            ),

            y=alt.Y(
                "RPE real:Q",
                title="RPE real",
                scale=alt.Scale(
                    domain=[
                        0,
                        10
                    ]
                )
            ),

            color=alt.Color(
                "Dif. RPE:Q",
                title="Δ RPE",
                scale=alt.Scale(
                    domain=[
                        -3,
                        0,
                        3
                    ],
                    range=[
                        "#3498DB",
                        "#2ECC71",
                        "#E74C3C"
                    ]
                )
            ),

            tooltip=[
                alt.Tooltip(
                    "Semana texto:N",
                    title="Semana"
                ),

                alt.Tooltip(
                    "Volumen real:Q",
                    title="Volumen real",
                    format=".0f"
                ),

                alt.Tooltip(
                    "RPE real:Q",
                    title="RPE real",
                    format=".1f"
                ),

                alt.Tooltip(
                    "Volumen %:Q",
                    title="Volumen %",
                    format=".1f"
                ),

                alt.Tooltip(
                    "Carga %:Q",
                    title="Carga %",
                    format=".1f"
                ),

                alt.Tooltip(
                    "Dif. RPE:Q",
                    title="Δ RPE",
                    format="+.1f"
                ),
            ]
        )
        .properties(
            height=420
        )
        .interactive()
    )

    st.altair_chart(
        scatter_volumen_rpe,
        use_container_width=True
    )

    if len(
        scatter_data
    ) >= 2:

        primera_semana_scatter = (
            scatter_data
            .sort_values(
                "Semana"
            )
            .iloc[0]
        )

        ultima_semana_scatter = (
            scatter_data
            .sort_values(
                "Semana"
            )
            .iloc[-1]
        )

        cambio_volumen = (
            ultima_semana_scatter[
                "Volumen real"
            ]
            -
            primera_semana_scatter[
                "Volumen real"
            ]
        )

        cambio_rpe = (
            ultima_semana_scatter[
                "RPE real"
            ]
            -
            primera_semana_scatter[
                "RPE real"
            ]
        )

        st.subheader(
            "Interpretación"
        )

        if (
            cambio_volumen > 0
            and
            cambio_rpe <= 0.5
        ):
            st.success(
                "✅ Posible adaptación positiva: "
                "el atleta está produciendo más volumen "
                "sin un aumento proporcional del RPE."
            )

            st.write(
                "Esto puede indicar una mejor tolerancia al estímulo. "
                "Si la técnica y la recuperación son buenas, "
                "la progresión puede mantenerse."
            )

        elif (
            cambio_volumen < 0
            and
            cambio_rpe > 0.5
        ):
            st.error(
                "🔴 Señal de atención: "
                "el atleta está produciendo menos volumen "
                "con mayor esfuerzo percibido."
            )

            st.write(
                "Conviene revisar recuperación, dificultad de las sesiones "
                "y calidad de ejecución antes de progresar la carga."
            )

        elif (
            abs(
                cambio_volumen
            )
            <=
            primera_semana_scatter[
                "Volumen real"
            ]
            *
            0.10
            and
            cambio_rpe < -0.5
        ):
            st.success(
                "✅ Mejora de tolerancia: "
                "el atleta mantiene un volumen similar "
                "con menor esfuerzo percibido."
            )

            st.write(
                "Puede ser una buena señal para considerar "
                "una progresión gradual del estímulo."
            )

        elif (
            cambio_volumen > 0
            and
            cambio_rpe > 0.5
        ):
            st.warning(
                "🟠 La carga de trabajo está aumentando "
                "junto con el esfuerzo percibido."
            )

            st.write(
                "No necesariamente es negativo si estaba planificado. "
                "Conviene observar las próximas semanas "
                "antes de seguir aumentando."
            )

        else:
            st.info(
                "🔵 Relación Volumen–RPE estable."
            )

            st.write(
                "No se observa un cambio suficientemente grande "
                "para inferir una tendencia clara."
            )

    else:
        st.info(
            "Se necesitan al menos 2 semanas registradas "
            "para interpretar la tendencia Volumen–RPE."
        )

    st.divider()

    st.subheader(
        "Perfil de carga por tipo de sesión"
    )

    st.caption(
        "Analiza qué tipos de entrenamiento están aportando más carga al bloque "
        "y cuánto se ejecutó respecto al plan."
    )

    df_tipo = (
        df_alumno[
            [
                "Tipo de sesión",
                "Volumen planificado",
                "Volumen real",
                "RPE planificado",
                "RPE real",
                "Carga planificada",
                "Carga real",
            ]
        ]
        .copy()
    )

    df_tipo = (
        df_tipo
        .dropna(
            subset=[
                "Tipo de sesión"
            ]
        )
    )

    df_tipo[
        "Tipo de sesión"
    ] = (
        df_tipo[
            "Tipo de sesión"
        ]
        .astype(str)
        .str.strip()
    )

    perfil_tipo = (
        df_tipo
        .groupby(
            "Tipo de sesión",
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
                "sum",
        })
    )

    perfil_tipo[
        "Volumen %"
    ] = (
        perfil_tipo[
            "Volumen real"
        ]
        /
        perfil_tipo[
            "Volumen planificado"
        ]
        *
        100
    )

    perfil_tipo[
        "Carga %"
    ] = (
        perfil_tipo[
            "Carga real"
        ]
        /
        perfil_tipo[
            "Carga planificada"
        ]
        *
        100
    )

    perfil_tipo[
        "Dif. RPE"
    ] = (
        perfil_tipo[
            "RPE real"
        ]
        -
        perfil_tipo[
            "RPE planificado"
        ]
    )

    perfil_tipo = (
        perfil_tipo
        .replace(
            [
                float(
                    "inf"
                ),
                float(
                    "-inf"
                )
            ],
            pd.NA
        )
    )

    carga_total_tipo = (
        perfil_tipo[
            "Carga real"
        ]
        .sum()
    )

    if carga_total_tipo > 0:
        perfil_tipo[
            "Participación carga %"
        ] = (
            perfil_tipo[
                "Carga real"
            ]
            /
            carga_total_tipo
            *
            100
        )

    else:
        perfil_tipo[
            "Participación carga %"
        ] = 0

    if not perfil_tipo.empty:

        tipo_mayor_carga = (
            perfil_tipo
            .sort_values(
                "Carga real",
                ascending=False
            )
            .iloc[0]
        )

        tipo_mayor_rpe = (
            perfil_tipo
            .sort_values(
                "RPE real",
                ascending=False
            )
            .iloc[0]
        )

        tipo_mayor_desviacion = (
            perfil_tipo
            .assign(
                Desviacion_abs=lambda x:
                    x[
                        "Dif. RPE"
                    ]
                    .abs()
            )
            .sort_values(
                "Desviacion_abs",
                ascending=False
            )
            .iloc[0]
        )

        col1, col2, col3 = (
            st.columns(
                3
            )
        )

        col1.metric(
            "Mayor carga",
            tipo_mayor_carga[
                "Tipo de sesión"
            ],
            delta=(
                f"{tipo_mayor_carga['Participación carga %']:.1f}% "
                "de la carga total"
            )
        )

        col2.metric(
            "Mayor RPE",
            tipo_mayor_rpe[
                "Tipo de sesión"
            ],
            delta=(
                f"RPE "
                f"{tipo_mayor_rpe['RPE real']:.1f}"
            ),
            delta_color="off"
        )

        col3.metric(
            "Mayor desviación de RPE",
            tipo_mayor_desviacion[
                "Tipo de sesión"
            ],
            delta=(
                f"{tipo_mayor_desviacion['Dif. RPE']:+.1f} "
                "vs plan"
            ),
            delta_color="inverse"
        )

    tab_tipo_carga, tab_tipo_cumplimiento, tab_tipo_rpe = (
        st.tabs(
            [
                "Carga por tipo",
                "Cumplimiento",
                "RPE por tipo"
            ]
        )
    )

    with tab_tipo_carga:

        st.subheader(
            "Distribución de carga real"
        )

        grafica_carga_tipo = (
            alt.Chart(
                perfil_tipo
            )
            .mark_bar()
            .encode(
                x=alt.X(
                    "Carga real:Q",
                    title="Carga real"
                ),

                y=alt.Y(
                    "Tipo de sesión:N",
                    title="",
                    sort="-x"
                ),

                tooltip=[
                    alt.Tooltip(
                        "Tipo de sesión:N",
                        title="Tipo"
                    ),

                    alt.Tooltip(
                        "Carga real:Q",
                        title="Carga real",
                        format=".0f"
                    ),

                    alt.Tooltip(
                        "Participación carga %:Q",
                        title="% de la carga total",
                        format=".1f"
                    ),

                    alt.Tooltip(
                        "RPE real:Q",
                        title="RPE medio",
                        format=".1f"
                    ),
                ]
            )
            .properties(
                height=max(
                    280,
                    len(
                        perfil_tipo
                    )
                    *
                    45
                )
            )
        )

        st.altair_chart(
            grafica_carga_tipo,
            use_container_width=True
        )

        st.caption(
            "Permite detectar qué tipos de sesión están aportando "
            "la mayor proporción de carga del bloque."
        )

    with tab_tipo_cumplimiento:

        st.subheader(
            "Carga planificada vs real"
        )

        carga_tipo_long = (
            perfil_tipo[
                [
                    "Tipo de sesión",
                    "Carga planificada",
                    "Carga real"
                ]
            ]
            .melt(
                id_vars="Tipo de sesión",
                var_name="Tipo",
                value_name="Carga"
            )
        )

        grafica_cumplimiento_tipo = (
            alt.Chart(
                carga_tipo_long
            )
            .mark_bar()
            .encode(
                x=alt.X(
                    "Carga:Q",
                    title="Carga"
                ),

                y=alt.Y(
                    "Tipo de sesión:N",
                    title="",
                    sort="-x"
                ),

                color=alt.Color(
                    "Tipo:N",
                    title=""
                ),

                xOffset="Tipo:N",

                tooltip=[
                    alt.Tooltip(
                        "Tipo de sesión:N",
                        title="Sesión"
                    ),

                    alt.Tooltip(
                        "Tipo:N",
                        title=""
                    ),

                    alt.Tooltip(
                        "Carga:Q",
                        title="Carga",
                        format=".0f"
                    ),
                ]
            )
            .properties(
                height=max(
                    280,
                    len(
                        perfil_tipo
                    )
                    *
                    55
                )
            )
        )

        st.altair_chart(
            grafica_cumplimiento_tipo,
            use_container_width=True
        )

        st.subheader(
            "Cumplimiento por tipo"
        )

        tabla_tipo = (
            perfil_tipo[
                [
                    "Tipo de sesión",
                    "Volumen %",
                    "Carga %",
                    "RPE planificado",
                    "RPE real",
                    "Dif. RPE",
                ]
            ]
            .copy()
        )

        tabla_tipo[
            "Volumen %"
        ] = (
            tabla_tipo[
                "Volumen %"
            ]
            .round(
                1
            )
        )

        tabla_tipo[
            "Carga %"
        ] = (
            tabla_tipo[
                "Carga %"
            ]
            .round(
                1
            )
        )

        tabla_tipo[
            "RPE planificado"
        ] = (
            tabla_tipo[
                "RPE planificado"
            ]
            .round(
                1
            )
        )

        tabla_tipo[
            "RPE real"
        ] = (
            tabla_tipo[
                "RPE real"
            ]
            .round(
                1
            )
        )

        tabla_tipo[
            "Dif. RPE"
        ] = (
            tabla_tipo[
                "Dif. RPE"
            ]
            .round(
                1
            )
        )

        st.dataframe(
            tabla_tipo,
            use_container_width=True,
            hide_index=True
        )

    with tab_tipo_rpe:

        st.subheader(
            "RPE planificado vs real por tipo de sesión"
        )

        rpe_tipo_long = (
            perfil_tipo[
                [
                    "Tipo de sesión",
                    "RPE planificado",
                    "RPE real"
                ]
            ]
            .melt(
                id_vars="Tipo de sesión",
                var_name="Tipo",
                value_name="RPE"
            )
        )

        grafica_rpe_tipo = (
            alt.Chart(
                rpe_tipo_long
            )
            .mark_bar()
            .encode(
                x=alt.X(
                    "Tipo de sesión:N",
                    title="Tipo de sesión"
                ),

                y=alt.Y(
                    "RPE:Q",
                    title="RPE",
                    scale=alt.Scale(
                        domain=[
                            0,
                            10
                        ]
                    )
                ),

                color=alt.Color(
                    "Tipo:N",
                    title=""
                ),

                xOffset="Tipo:N",

                tooltip=[
                    alt.Tooltip(
                        "Tipo de sesión:N",
                        title="Sesión"
                    ),

                    alt.Tooltip(
                        "Tipo:N",
                        title=""
                    ),

                    alt.Tooltip(
                        "RPE:Q",
                        title="RPE",
                        format=".1f"
                    ),
                ]
            )
            .properties(
                height=400
            )
        )

        st.altair_chart(
            grafica_rpe_tipo,
            use_container_width=True
        )

    st.subheader(
        "Lectura del bloque"
    )

    for _, fila_tipo in perfil_tipo.iterrows():

        tipo = (
            fila_tipo[
                "Tipo de sesión"
            ]
        )

        volumen_pct = (
            fila_tipo[
                "Volumen %"
            ]
        )

        carga_pct = (
            fila_tipo[
                "Carga %"
            ]
        )

        dif_rpe = (
            fila_tipo[
                "Dif. RPE"
            ]
        )

        if (
            carga_pct > 115
            and
            dif_rpe >= 1
        ):
            st.error(
                f"🔴 **{tipo}:** carga {carga_pct:.1f}% "
                f"y ΔRPE {dif_rpe:+.1f}. "
                "Este estímulo está siendo más exigente de lo previsto."
            )

        elif (
            carga_pct < 85
            and
            dif_rpe <= 0
        ):
            st.info(
                f"🔵 **{tipo}:** carga {carga_pct:.1f}% "
                f"y ΔRPE {dif_rpe:+.1f}. "
                "El estímulo ejecutado está por debajo de lo planificado."
            )

        elif (
            volumen_pct < 85
            and
            dif_rpe >= 1
        ):
            st.warning(
                f"🟠 **{tipo}:** solo se completó "
                f"{volumen_pct:.1f}% del volumen, "
                f"pero el RPE estuvo {dif_rpe:+.1f} sobre el plan. "
                "Conviene revisar la dificultad del estímulo."
            )

        elif (
            90 <= carga_pct <= 110
            and
            abs(
                dif_rpe
            ) < 1
        ):
            st.success(
                f"✅ **{tipo}:** respuesta acorde al plan "
                f"(Carga {carga_pct:.1f}% · "
                f"ΔRPE {dif_rpe:+.1f})."
            )

        else:
            st.info(
                f"🟡 **{tipo}:** "
                f"Volumen {volumen_pct:.1f}% · "
                f"Carga {carga_pct:.1f}% · "
                f"ΔRPE {dif_rpe:+.1f}. "
                "Continuar monitoreando."
            )


# =========================================================
# VISTA GRUPO
# =========================================================

elif pagina == "Vista grupo":

    st.title(
        "Vista del grupo"
    )

    st.caption(
        "Detecta rápidamente patrones de carga, volumen y RPE "
        "entre todos los atletas."
    )

    df_grupo = (
        leer_hoja(
            "Historial semanal"
        )
    )

    columnas_numericas = [
        "Semana",
        "Sesión",
        "Volumen planificado",
        "Volumen real",
        "RPE planificado",
        "RPE real",
        "Carga planificada",
        "Carga real",
    ]

    for columna in columnas_numericas:

        if columna in df_grupo.columns:

            df_grupo[
                columna
            ] = (
                pd.to_numeric(
                    df_grupo[
                        columna
                    ],
                    errors="coerce"
                )
            )

    bloque_grupo = (
        st.selectbox(
            "Bloque",
            [
                1,
                2,
                3,
                4
            ],
            index=None,
            placeholder="Selecciona un bloque...",
            key="bloque_grupo"
        )
    )

    if bloque_grupo is None:

        st.info(
            "Selecciona un bloque para analizar al grupo."
        )

        st.stop()

    rangos = {
        1: (1, 13),
        2: (14, 26),
        3: (27, 39),
        4: (40, 52),
    }

    inicio, fin = (
        rangos[
            bloque_grupo
        ]
    )

    df_grupo = (
        df_grupo[
            (
                df_grupo[
                    "Semana"
                ]
                >=
                inicio
            )
            &
            (
                df_grupo[
                    "Semana"
                ]
                <=
                fin
            )
        ]
        .copy()
    )

    if df_grupo.empty:
        st.info(
            "No existen registros para este bloque."
        )

        st.stop()

    df_grupo = (
        df_grupo
        .dropna(
            subset=[
                "Alumno",
                "Semana",
                "Volumen planificado",
                "Volumen real",
                "RPE planificado",
                "RPE real",
                "Carga planificada",
                "Carga real",
            ]
        )
    )

    df_grupo[
        "Alumno"
    ] = (
        df_grupo[
            "Alumno"
        ]
        .astype(str)
        .str.strip()
    )

    resumen_grupo = (
        df_grupo
        .groupby(
            [
                "Alumno",
                "Semana"
            ],
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
                "sum",

            "Sesión":
                "count",
        })
        .rename(
            columns={
                "Sesión":
                    "Sesiones registradas"
            }
        )
    )

    resumen_grupo[
        "Volumen %"
    ] = (
        resumen_grupo[
            "Volumen real"
        ]
        /
        resumen_grupo[
            "Volumen planificado"
        ]
        *
        100
    )

    resumen_grupo[
        "Carga %"
    ] = (
        resumen_grupo[
            "Carga real"
        ]
        /
        resumen_grupo[
            "Carga planificada"
        ]
        *
        100
    )

    resumen_grupo[
        "RPE planificado"
    ] = (
        pd.to_numeric(
            resumen_grupo[
                "RPE planificado"
            ],
            errors="coerce"
        )
    )

    resumen_grupo[
        "RPE real"
    ] = (
        pd.to_numeric(
            resumen_grupo[
                "RPE real"
            ],
            errors="coerce"
        )
    )

    resumen_grupo[
        "Dif. RPE"
    ] = (
        resumen_grupo[
            "RPE real"
        ]
        -
        resumen_grupo[
            "RPE planificado"
        ]
    )

    resumen_grupo[
        "Dif. RPE"
    ] = (
        pd.to_numeric(
            resumen_grupo[
                "Dif. RPE"
            ],
            errors="coerce"
        )
    )

    resumen_grupo = (
        resumen_grupo
        .replace(
            [
                float(
                    "inf"
                ),
                float(
                    "-inf"
                )
            ],
            pd.NA
        )
    )

    resumen_grupo = (
        resumen_grupo
        .dropna(
            subset=[
                "Volumen %",
                "Carga %",
                "Dif. RPE"
            ]
        )
    )

    resumen_grupo[
        "Nivel"
    ] = (
        resumen_grupo
        .apply(
            lambda fila:
                clasificar_estado(
                    fila[
                        "Volumen %"
                    ],
                    fila[
                        "Carga %"
                    ],
                    fila[
                        "Dif. RPE"
                    ]
                ),
            axis=1
        )
    )

    mapa_nivel = {
        "OK": 0,
        "MONITOREAR": 1,
        "REVISAR": 2,
        "ALTA": 3,
    }

    resumen_grupo[
        "Nivel numérico"
    ] = (
        resumen_grupo[
            "Nivel"
        ]
        .map(
            mapa_nivel
        )
    )

    resumen_grupo[
        "Nivel corto"
    ] = (
        resumen_grupo[
            "Nivel"
        ]
        .replace({
            "MONITOREAR":
                "MON",

            "REVISAR":
                "REV",
        })
    )

    semana_reciente = int(
        resumen_grupo[
            "Semana"
        ]
        .max()
    )

    ultima_grupo = (
        resumen_grupo[
            resumen_grupo[
                "Semana"
            ]
            ==
            semana_reciente
        ]
        .copy()
    )

    atletas_registrados = (
        resumen_grupo[
            "Alumno"
        ]
        .nunique()
    )

    atletas_atencion = (
        ultima_grupo[
            ultima_grupo[
                "Nivel"
            ]
            .isin(
                [
                    "MONITOREAR",
                    "REVISAR",
                    "ALTA"
                ]
            )
        ][
            "Alumno"
        ]
        .nunique()
    )

    carga_media = (
        ultima_grupo[
            "Carga %"
        ]
        .mean()
    )

    rpe_diff_media = (
        ultima_grupo[
            "Dif. RPE"
        ]
        .mean()
    )

    st.divider()

    st.subheader(
        f"Semana más reciente: "
        f"{semana_reciente}"
    )

    col1, col2, col3, col4 = (
        st.columns(
            4
        )
    )

    col1.metric(
        "Atletas registrados",
        atletas_registrados
    )

    col2.metric(
        "Requieren atención",
        atletas_atencion
    )

    col3.metric(
        "Carga media",
        f"{carga_media:.1f}%"
    )

    col4.metric(
        "Δ RPE medio",
        f"{rpe_diff_media:+.1f}"
    )

    st.divider()

    st.subheader(
        "Heatmap del grupo"
    )

    metrica_heatmap = (
        st.selectbox(
            "Variable a visualizar",
            [
                "Nivel de atención",
                "Carga %",
                "Volumen %",
                "Δ RPE"
            ],
            index=None,
            placeholder="Selecciona una métrica...",
            key="metrica_heatmap"
        )
    )

    if metrica_heatmap is None:

        st.info(
            "Selecciona una métrica para generar el heatmap."
        )

    else:
        df_heatmap = (
            resumen_grupo
            .copy()
        )

        df_heatmap[
            "Semana"
        ] = (
            pd.to_numeric(
                df_heatmap[
                    "Semana"
                ],
                errors="coerce"
            )
        )

        df_heatmap[
            "Carga %"
        ] = (
            pd.to_numeric(
                df_heatmap[
                    "Carga %"
                ],
                errors="coerce"
            )
        )

        df_heatmap[
            "Volumen %"
        ] = (
            pd.to_numeric(
                df_heatmap[
                    "Volumen %"
                ],
                errors="coerce"
            )
        )

        df_heatmap[
            "Dif. RPE"
        ] = (
            pd.to_numeric(
                df_heatmap[
                    "Dif. RPE"
                ],
                errors="coerce"
            )
        )

        df_heatmap[
            "RPE planificado"
        ] = (
            pd.to_numeric(
                df_heatmap[
                    "RPE planificado"
                ],
                errors="coerce"
            )
        )

        df_heatmap[
            "RPE real"
        ] = (
            pd.to_numeric(
                df_heatmap[
                    "RPE real"
                ],
                errors="coerce"
            )
        )

        df_heatmap = (
            df_heatmap
            .dropna(
                subset=[
                    "Alumno",
                    "Semana"
                ]
            )
        )

        if (
            metrica_heatmap
            ==
            "Nivel de atención"
        ):
            df_chart = (
                df_heatmap
                .dropna(
                    subset=[
                        "Nivel"
                    ]
                )
            )

            grafica_final = (
                alt.Chart(
                    df_chart
                )
                .mark_rect(
                    cornerRadius=5
                )
                .encode(
                    x=alt.X(
                        "Semana:O",
                        title="Semana"
                    ),

                    y=alt.Y(
                        "Alumno:N",
                        title="Atleta",
                        sort="ascending"
                    ),

                    color=alt.Color(
                        "Nivel:N",
                        title="Nivel",
                        scale=alt.Scale(
                            domain=[
                                "OK",
                                "MONITOREAR",
                                "REVISAR",
                                "ALTA"
                            ],
                            range=[
                                "#2ECC71",
                                "#F1C40F",
                                "#E67E22",
                                "#E74C3C"
                            ]
                        )
                    ),

                    tooltip=[
                        alt.Tooltip(
                            "Alumno:N",
                            title="Atleta"
                        ),

                        alt.Tooltip(
                            "Semana:O",
                            title="Semana"
                        ),

                        alt.Tooltip(
                            "Nivel:N",
                            title="Nivel"
                        ),

                        alt.Tooltip(
                            "Volumen %:Q",
                            title="Volumen %",
                            format=".1f"
                        ),

                        alt.Tooltip(
                            "Carga %:Q",
                            title="Carga %",
                            format=".1f"
                        ),

                        alt.Tooltip(
                            "RPE planificado:Q",
                            title="RPE planificado",
                            format=".1f"
                        ),

                        alt.Tooltip(
                            "RPE real:Q",
                            title="RPE real",
                            format=".1f"
                        ),

                        alt.Tooltip(
                            "Dif. RPE:Q",
                            title="Δ RPE",
                            format="+.1f"
                        ),
                    ]
                )
                .properties(
                    height=max(
                        250,
                        atletas_registrados
                        *
                        55
                    )
                )
            )

        elif (
            metrica_heatmap
            ==
            "Carga %"
        ):
            df_chart = (
                df_heatmap
                .dropna(
                    subset=[
                        "Carga %"
                    ]
                )
            )

            grafica_final = (
                alt.Chart(
                    df_chart
                )
                .mark_rect(
                    cornerRadius=5
                )
                .encode(
                    x=alt.X(
                        "Semana:O",
                        title="Semana"
                    ),

                    y=alt.Y(
                        "Alumno:N",
                        title="Atleta",
                        sort="ascending"
                    ),

                    color=alt.Color(
                        "Carga %:Q",
                        title="Carga %",
                        scale=alt.Scale(
                            domain=[
                                70,
                                100,
                                130
                            ],
                            range=[
                                "#3498DB",
                                "#2ECC71",
                                "#E74C3C"
                            ]
                        )
                    ),

                    tooltip=[
                        alt.Tooltip(
                            "Alumno:N",
                            title="Atleta"
                        ),

                        alt.Tooltip(
                            "Semana:O",
                            title="Semana"
                        ),

                        alt.Tooltip(
                            "Carga %:Q",
                            title="Carga %",
                            format=".1f"
                        ),

                        alt.Tooltip(
                            "Volumen %:Q",
                            title="Volumen %",
                            format=".1f"
                        ),

                        alt.Tooltip(
                            "Dif. RPE:Q",
                            title="Δ RPE",
                            format="+.1f"
                        ),

                        alt.Tooltip(
                            "Nivel:N",
                            title="Nivel"
                        ),
                    ]
                )
                .properties(
                    height=max(
                        250,
                        atletas_registrados
                        *
                        55
                    )
                )
            )

        elif (
            metrica_heatmap
            ==
            "Volumen %"
        ):
            df_chart = (
                df_heatmap
                .dropna(
                    subset=[
                        "Volumen %"
                    ]
                )
            )

            grafica_final = (
                alt.Chart(
                    df_chart
                )
                .mark_rect(
                    cornerRadius=5
                )
                .encode(
                    x=alt.X(
                        "Semana:O",
                        title="Semana"
                    ),

                    y=alt.Y(
                        "Alumno:N",
                        title="Atleta",
                        sort="ascending"
                    ),

                    color=alt.Color(
                        "Volumen %:Q",
                        title="Volumen %",
                        scale=alt.Scale(
                            domain=[
                                70,
                                100,
                                130
                            ],
                            range=[
                                "#3498DB",
                                "#2ECC71",
                                "#E74C3C"
                            ]
                        )
                    ),

                    tooltip=[
                        alt.Tooltip(
                            "Alumno:N",
                            title="Atleta"
                        ),

                        alt.Tooltip(
                            "Semana:O",
                            title="Semana"
                        ),

                        alt.Tooltip(
                            "Volumen %:Q",
                            title="Volumen %",
                            format=".1f"
                        ),

                        alt.Tooltip(
                            "Carga %:Q",
                            title="Carga %",
                            format=".1f"
                        ),

                        alt.Tooltip(
                            "Dif. RPE:Q",
                            title="Δ RPE",
                            format="+.1f"
                        ),

                        alt.Tooltip(
                            "Nivel:N",
                            title="Nivel"
                        ),
                    ]
                )
                .properties(
                    height=max(
                        250,
                        atletas_registrados
                        *
                        55
                    )
                )
            )

        else:
            df_chart = (
                df_heatmap[
                    [
                        "Alumno",
                        "Semana",
                        "RPE planificado",
                        "RPE real",
                        "Dif. RPE",
                        "Carga %",
                        "Volumen %",
                        "Nivel",
                    ]
                ]
                .copy()
            )

            df_chart[
                "Dif. RPE"
            ] = (
                pd.to_numeric(
                    df_chart[
                        "Dif. RPE"
                    ],
                    errors="coerce"
                )
            )

            df_chart[
                "RPE planificado"
            ] = (
                pd.to_numeric(
                    df_chart[
                        "RPE planificado"
                    ],
                    errors="coerce"
                )
            )

            df_chart[
                "RPE real"
            ] = (
                pd.to_numeric(
                    df_chart[
                        "RPE real"
                    ],
                    errors="coerce"
                )
            )

            df_chart = (
                df_chart
                .dropna(
                    subset=[
                        "Alumno",
                        "Semana",
                        "Dif. RPE"
                    ]
                )
            )

            df_chart[
                "Dif. RPE"
            ] = (
                df_chart[
                    "Dif. RPE"
                ]
                .astype(
                    float
                )
            )

            df_chart[
                "Semana heatmap"
            ] = (
                df_chart[
                    "Semana"
                ]
                .astype(int)
                .astype(str)
            )

            df_chart[
                "Δ RPE texto"
            ] = (
                df_chart[
                    "Dif. RPE"
                ]
                .map(
                    lambda x:
                        f"{x:+.1f}"
                )
            )

            heatmap_rpe = (
                alt.Chart(
                    df_chart
                )
                .mark_rect(
                    cornerRadius=6
                )
                .encode(
                    x=alt.X(
                        "Semana heatmap:N",
                        title="Semana",
                        sort=None
                    ),

                    y=alt.Y(
                        "Alumno:N",
                        title="Atleta",
                        sort="ascending"
                    ),

                    color=alt.Color(
                        "Dif. RPE:Q",
                        title="Δ RPE",
                        scale=alt.Scale(
                            domain=[
                                -3,
                                3
                            ],
                            scheme="redyellowgreen",
                            reverse=True
                        )
                    ),

                    tooltip=[
                        alt.Tooltip(
                            "Alumno:N",
                            title="Atleta"
                        ),

                        alt.Tooltip(
                            "Semana heatmap:N",
                            title="Semana"
                        ),

                        alt.Tooltip(
                            "RPE planificado:Q",
                            title="RPE planificado",
                            format=".1f"
                        ),

                        alt.Tooltip(
                            "RPE real:Q",
                            title="RPE real",
                            format=".1f"
                        ),

                        alt.Tooltip(
                            "Dif. RPE:Q",
                            title="Δ RPE",
                            format="+.1f"
                        ),

                        alt.Tooltip(
                            "Volumen %:Q",
                            title="Volumen %",
                            format=".1f"
                        ),

                        alt.Tooltip(
                            "Carga %:Q",
                            title="Carga %",
                            format=".1f"
                        ),

                        alt.Tooltip(
                            "Nivel:N",
                            title="Nivel"
                        ),
                    ]
                )
                .properties(
                    height=max(
                        250,
                        atletas_registrados
                        *
                        55
                    )
                )
            )

            texto_rpe = (
                alt.Chart(
                    df_chart
                )
                .mark_text(
                    fontSize=13,
                    fontWeight="bold",
                    color="white"
                )
                .encode(
                    x=alt.X(
                        "Semana heatmap:N",
                        sort=None
                    ),

                    y=alt.Y(
                        "Alumno:N",
                        sort="ascending"
                    ),

                    text=alt.Text(
                        "Δ RPE texto:N"
                    )
                )
            )

            grafica_final = (
                heatmap_rpe
                +
                texto_rpe
            )

        if df_chart.empty:

            st.warning(
                "No hay datos suficientes para mostrar esta métrica."
            )

        else:
            st.altair_chart(
                grafica_final,
                use_container_width=True
            )

            st.caption(
                f"Mostrando {len(df_chart)} registros "
                f"de {df_chart['Alumno'].nunique()} atletas."
            )

    st.divider()

    st.subheader(
        "Prioridades del coach"
    )

    prioridad = (
        ultima_grupo
        .sort_values(
            [
                "Nivel numérico",
                "Dif. RPE"
            ],
            ascending=[
                False,
                False
            ]
        )
    )

    for _, fila in prioridad.iterrows():

        nivel = (
            fila[
                "Nivel"
            ]
        )

        texto = (
            f"**{fila['Alumno']}** · "
            f"Carga {fila['Carga %']:.1f}% · "
            f"Volumen {fila['Volumen %']:.1f}% · "
            f"ΔRPE {fila['Dif. RPE']:+.1f}"
        )

        if nivel == "ALTA":
            st.error(
                f"🔴 {texto}"
            )

        elif nivel == "REVISAR":
            st.warning(
                f"🟠 {texto}"
            )

        elif nivel == "MONITOREAR":
            st.info(
                f"🟡 {texto}"
            )

        else:
            st.success(
                f"✅ {texto}"
            )
    # =========================================================
    # PASO 6A — DASHBOARD FÍSICO DEL GRUPO
    # =========================================================

    st.divider()

    st.header(
        "Acondicionamiento físico del grupo"
    )

    st.caption(
        "Resumen del trabajo físico realizado por todos "
        "los atletas del bloque seleccionado."
    )


    try:

        # =====================================================
        # LEER HISTORIAL FÍSICO
        # =====================================================

        df_fisico_grupo = leer_hoja(
            HOJAS_FISICO["historial"],
            SPREADSHEET_ID_FISICO
        )


        if df_fisico_grupo.empty:

            st.info(
                "Todavía no existen registros de "
                "acondicionamiento físico."
            )


        else:

            # =================================================
            # LIMPIAR DATOS
            # =================================================

            columnas_numericas_grupo = [
                "Semana",
                "Sesión",
                "Series planificadas",
                "Series reales",
                "Repeticiones planificadas",
                "Repeticiones reales",
                "Carga externa planificada",
                "Carga externa real",
                "RPE planificado",
                "RPE real",
                "Dedos",
                "Antebrazo / muñeca",
                "Tracción (espalda/bíceps)",
                "Empuje (pecho/tríceps)",
                "Hombro",
                "Core",
                "Piernas / cadera",
                "Puntaje interferencia"
            ]


            for columna in columnas_numericas_grupo:

                if columna in df_fisico_grupo.columns:

                    df_fisico_grupo[
                        columna
                    ] = pd.to_numeric(
                        df_fisico_grupo[
                            columna
                        ],
                        errors="coerce"
                    )


            df_fisico_grupo = (
                df_fisico_grupo
                .dropna(
                    subset=[
                        "Semana",
                        "Sesión",
                        "Alumno",
                        "Ejercicio"
                    ]
                )
                .copy()
            )


            df_fisico_grupo[
                "Alumno"
            ] = (
                df_fisico_grupo[
                    "Alumno"
                ]
                .astype(str)
                .str.strip()
            )


            # =================================================
            # ASIGNAR BLOQUE
            # =================================================

            df_fisico_grupo[
                "Bloque"
            ] = (
                df_fisico_grupo[
                    "Semana"
                ]
                .apply(
                    lambda semana:
                        obtener_bloque(
                            int(semana)
                        )[0]
                )
            )


            # =================================================
            # SELECTOR DE BLOQUE
            # =================================================

            bloque_grupo_fisico = st.selectbox(
                "Bloque físico",
                [
                    1,
                    2,
                    3,
                    4
                ],
                key="bloque_grupo_fisico"
            )


            df_fisico_bloque = (
                df_fisico_grupo[
                    df_fisico_grupo[
                        "Bloque"
                    ]
                    ==
                    bloque_grupo_fisico
                ]
                .copy()
            )


            if df_fisico_bloque.empty:

                st.info(
                    "No existen registros físicos "
                    "para este bloque."
                )


            else:

                # =============================================
                # NOMBRE Y SEMANAS DEL BLOQUE
                # =============================================

                semanas_bloque = {
                    1: (1, 13),
                    2: (14, 26),
                    3: (27, 39),
                    4: (40, 52)
                }


                semana_inicio, semana_fin = (
                    semanas_bloque[
                        bloque_grupo_fisico
                    ]
                )


                _, nombre_bloque_grupo = (
                    obtener_bloque(
                        semana_inicio
                    )
                )


                st.caption(
                    f"Bloque {bloque_grupo_fisico} · "
                    f"{nombre_bloque_grupo} · "
                    f"Semanas {semana_inicio}–{semana_fin}"
                )


                # =============================================
                # ZONAS FÍSICAS
                # =============================================

                zonas_grupo_fisico = [
                    "Dedos",
                    "Antebrazo / muñeca",
                    "Tracción (espalda/bíceps)",
                    "Empuje (pecho/tríceps)",
                    "Hombro",
                    "Core",
                    "Piernas / cadera"
                ]


                # =============================================
                # CARGA TOTAL POR REGISTRO
                # =============================================

                df_fisico_bloque[
                    "Carga física total"
                ] = (
                    df_fisico_bloque[
                        zonas_grupo_fisico
                    ]
                    .fillna(0)
                    .sum(
                        axis=1
                    )
                )


                # =============================================
                # SESIONES ÚNICAS DEL GRUPO
                # =============================================

                sesiones_unicas_grupo = (
                    df_fisico_bloque[
                        [
                            "Alumno",
                            "Semana",
                            "Sesión"
                        ]
                    ]
                    .drop_duplicates()
                )


                total_sesiones_grupo = len(
                    sesiones_unicas_grupo
                )


                total_alumnos_grupo = (
                    df_fisico_bloque[
                        "Alumno"
                    ]
                    .nunique()
                )


                carga_total_grupo = (
                    df_fisico_bloque[
                        "Carga física total"
                    ]
                    .sum()
                )


                rpe_medio_grupo = (
                    df_fisico_bloque[
                        "RPE real"
                    ]
                    .mean()
                )


                # =============================================
                # ALTA INTERFERENCIA DEL GRUPO
                # Se cuenta por sesión, no por ejercicio
                # =============================================

                sesiones_alta_interferencia = (
                    df_fisico_bloque[
                        df_fisico_bloque[
                            "Compatibilidad"
                        ]
                        ==
                        "ALTA INTERFERENCIA"
                    ][
                        [
                            "Alumno",
                            "Semana",
                            "Sesión"
                        ]
                    ]
                    .drop_duplicates()
                    .shape[0]
                )


                # =============================================
                # KPIs DEL GRUPO
                # =============================================

                st.subheader(
                    "Resumen del grupo"
                )


                col_g1, col_g2, col_g3, col_g4, col_g5 = (
                    st.columns(5)
                )


                col_g1.metric(
                    "Atletas",
                    total_alumnos_grupo
                )


                col_g2.metric(
                    "Sesiones físicas",
                    total_sesiones_grupo
                )


                col_g3.metric(
                    "Carga física",
                    f"{carga_total_grupo:.1f}"
                )


                col_g4.metric(
                    "RPE medio",
                    f"{rpe_medio_grupo:.1f}"
                )


                col_g5.metric(
                    "Alta interferencia",
                    sesiones_alta_interferencia
                )


                # =============================================
                # RESUMEN INDIVIDUAL
                # =============================================

                resumen_alumnos_fisico = []


                alumnos_fisico_grupo = sorted(
                    df_fisico_bloque[
                        "Alumno"
                    ]
                    .dropna()
                    .unique()
                    .tolist()
                )


                for alumno in alumnos_fisico_grupo:

                    df_alumno_grupo = (
                        df_fisico_bloque[
                            df_fisico_bloque[
                                "Alumno"
                            ]
                            ==
                            alumno
                        ]
                        .copy()
                    )


                    # -----------------------------------------
                    # SESIONES
                    # -----------------------------------------

                    sesiones_alumno = (
                        df_alumno_grupo[
                            [
                                "Semana",
                                "Sesión"
                            ]
                        ]
                        .drop_duplicates()
                        .shape[0]
                    )


                    semanas_alumno = (
                        df_alumno_grupo[
                            "Semana"
                        ]
                        .nunique()
                    )


                    ejercicios_alumno = (
                        df_alumno_grupo[
                            "Ejercicio"
                        ]
                        .nunique()
                    )


                    # -----------------------------------------
                    # CARGA
                    # -----------------------------------------

                    carga_alumno = (
                        df_alumno_grupo[
                            "Carga física total"
                        ]
                        .sum()
                    )


                    if semanas_alumno > 0:

                        carga_media_semanal = (
                            carga_alumno
                            /
                            semanas_alumno
                        )

                    else:

                        carga_media_semanal = 0


                    # -----------------------------------------
                    # RPE
                    # -----------------------------------------

                    rpe_alumno = (
                        df_alumno_grupo[
                            "RPE real"
                        ]
                        .mean()
                    )


                    # -----------------------------------------
                    # SERIES
                    # -----------------------------------------

                    series_plan_alumno = (
                        df_alumno_grupo[
                            "Series planificadas"
                        ]
                        .sum()
                    )


                    series_real_alumno = (
                        df_alumno_grupo[
                            "Series reales"
                        ]
                        .sum()
                    )


                    if series_plan_alumno > 0:

                        cumplimiento_series = (
                            series_real_alumno
                            /
                            series_plan_alumno
                            *
                            100
                        )

                    else:

                        cumplimiento_series = 0


                    # -----------------------------------------
                    # REPETICIONES
                    # -----------------------------------------

                    reps_plan_alumno = (
                        df_alumno_grupo[
                            "Repeticiones planificadas"
                        ]
                        .sum()
                    )


                    reps_real_alumno = (
                        df_alumno_grupo[
                            "Repeticiones reales"
                        ]
                        .sum()
                    )


                    if reps_plan_alumno > 0:

                        cumplimiento_reps = (
                            reps_real_alumno
                            /
                            reps_plan_alumno
                            *
                            100
                        )

                    else:

                        cumplimiento_reps = 0


                    # -----------------------------------------
                    # ZONA MÁS CARGADA
                    # -----------------------------------------

                    carga_zonas_alumno = (
                        df_alumno_grupo[
                            zonas_grupo_fisico
                        ]
                        .fillna(0)
                        .sum()
                    )


                    if carga_zonas_alumno.sum() > 0:

                        zona_dominante = (
                            carga_zonas_alumno
                            .idxmax()
                        )


                        carga_zona_dominante = (
                            carga_zonas_alumno
                            .max()
                        )

                    else:

                        zona_dominante = "-"
                        carga_zona_dominante = 0


                    # -----------------------------------------
                    # INTERFERENCIA
                    # -----------------------------------------

                    df_sesiones_alumno = (
                        df_alumno_grupo[
                            [
                                "Semana",
                                "Sesión",
                                "Compatibilidad",
                                "Puntaje interferencia"
                            ]
                        ]
                        .drop_duplicates(
                            subset=[
                                "Semana",
                                "Sesión"
                            ]
                        )
                    )


                    altas_alumno = int(
                        (
                            df_sesiones_alumno[
                                "Compatibilidad"
                            ]
                            ==
                            "ALTA INTERFERENCIA"
                        )
                        .sum()
                    )


                    revisar_alumno = int(
                        (
                            df_sesiones_alumno[
                                "Compatibilidad"
                            ]
                            ==
                            "REVISAR"
                        )
                        .sum()
                    )


                    interferencia_media = (
                        df_sesiones_alumno[
                            "Puntaje interferencia"
                        ]
                        .mean()
                    )


                    # -----------------------------------------
                    # GUARDAR RESUMEN
                    # -----------------------------------------

                    resumen_alumnos_fisico.append(
                        {
                            "Alumno":
                                alumno,

                            "Semanas":
                                int(
                                    semanas_alumno
                                ),

                            "Sesiones":
                                int(
                                    sesiones_alumno
                                ),

                            "Ejercicios":
                                int(
                                    ejercicios_alumno
                                ),

                            "Carga física":
                                round(
                                    carga_alumno,
                                    1
                                ),

                            "Carga semanal media":
                                round(
                                    carga_media_semanal,
                                    1
                                ),

                            "RPE medio":
                                round(
                                    rpe_alumno,
                                    1
                                ),

                            "Series %":
                                round(
                                    cumplimiento_series,
                                    1
                                ),

                            "Reps %":
                                round(
                                    cumplimiento_reps,
                                    1
                                ),

                            "Zona dominante":
                                zona_dominante,

                            "Carga zona dominante":
                                round(
                                    carga_zona_dominante,
                                    1
                                ),

                            "Revisar":
                                revisar_alumno,

                            "Alta interferencia":
                                altas_alumno,

                            "Interferencia media":
                                round(
                                    interferencia_media,
                                    1
                                )
                        }
                    )


                # =============================================
                # DATAFRAME FINAL
                # =============================================

                df_resumen_fisico_grupo = pd.DataFrame(
                    resumen_alumnos_fisico
                )


                if not df_resumen_fisico_grupo.empty:

                    df_resumen_fisico_grupo = (
                        df_resumen_fisico_grupo
                        .sort_values(
                            "Carga física",
                            ascending=False
                        )
                        .reset_index(
                            drop=True
                        )
                    )


                    # =========================================
                    # GRÁFICA CARGA POR ATLETA
                    # =========================================

                    st.subheader(
                        "Carga física por atleta"
                    )


                    grafica_carga_grupo = (
                        alt.Chart(
                            df_resumen_fisico_grupo
                        )
                        .mark_bar()
                        .encode(

                            x=alt.X(
                                "Carga física:Q",
                                title="Carga física"
                            ),

                            y=alt.Y(
                                "Alumno:N",
                                title="",
                                sort="-x"
                            ),

                            tooltip=[
                                alt.Tooltip(
                                    "Alumno:N",
                                    title="Alumno"
                                ),

                                alt.Tooltip(
                                    "Carga física:Q",
                                    title="Carga",
                                    format=".1f"
                                ),

                                alt.Tooltip(
                                    "Sesiones:Q",
                                    title="Sesiones"
                                ),

                                alt.Tooltip(
                                    "RPE medio:Q",
                                    title="RPE",
                                    format=".1f"
                                ),

                                alt.Tooltip(
                                    "Zona dominante:N",
                                    title="Zona dominante"
                                )
                            ]
                        )
                        .properties(
                            height=max(
                                300,
                                len(
                                    df_resumen_fisico_grupo
                                )
                                *
                                35
                            )
                        )
                    )


                    st.altair_chart(
                        grafica_carga_grupo,
                        use_container_width=True
                    )


                    # =========================================
                    # RPE POR ATLETA
                    # =========================================

                    st.subheader(
                        "RPE físico medio"
                    )


                    grafica_rpe_grupo = (
                        alt.Chart(
                            df_resumen_fisico_grupo
                        )
                        .mark_bar()
                        .encode(

                            x=alt.X(
                                "RPE medio:Q",
                                title="RPE medio",
                                scale=alt.Scale(
                                    domain=[
                                        0,
                                        10
                                    ]
                                )
                            ),

                            y=alt.Y(
                                "Alumno:N",
                                title="",
                                sort="-x"
                            ),

                            tooltip=[
                                alt.Tooltip(
                                    "Alumno:N",
                                    title="Alumno"
                                ),

                                alt.Tooltip(
                                    "RPE medio:Q",
                                    title="RPE",
                                    format=".1f"
                                ),

                                alt.Tooltip(
                                    "Carga física:Q",
                                    title="Carga física",
                                    format=".1f"
                                )
                            ]
                        )
                        .properties(
                            height=max(
                                300,
                                len(
                                    df_resumen_fisico_grupo
                                )
                                *
                                35
                            )
                        )
                    )


                    st.altair_chart(
                        grafica_rpe_grupo,
                        use_container_width=True
                    )


                    # =========================================
                    # TABLA COMPLETA
                    # =========================================

                    st.subheader(
                        "Resumen por atleta"
                    )


                    st.dataframe(
                        df_resumen_fisico_grupo,
                        use_container_width=True,
                        hide_index=True
                    )


                else:

                    st.info(
                        "No hay atletas con datos suficientes "
                        "para generar el resumen."
                    )
                                    # =========================================================
                # PASO 6B — HEATMAP FÍSICO DEL GRUPO
                # =========================================================

                st.divider()

                st.header(
                    "Heatmap físico del grupo"
                )

                st.caption(
                    "Compara la carga semanal de todos los atletas. "
                    "Puedes visualizar la carga física total, el RPE "
                    "o una zona corporal específica."
                )


                # =========================================================
                # MÉTRICA A VISUALIZAR
                # =========================================================

                opciones_heatmap_fisico = [
                    "Carga física",
                    "RPE físico",
                    "Dedos",
                    "Antebrazo / muñeca",
                    "Tracción (espalda/bíceps)",
                    "Empuje (pecho/tríceps)",
                    "Hombro",
                    "Core",
                    "Piernas / cadera"
                ]


                metrica_heatmap_fisico = st.selectbox(
                    "Métrica del heatmap",
                    opciones_heatmap_fisico,
                    key="metrica_heatmap_fisico"
                )


                # =========================================================
                # DEFINIR COLUMNA Y TIPO DE CÁLCULO
                # =========================================================

                if metrica_heatmap_fisico == "Carga física":

                    columna_heatmap = (
                        "Carga física total"
                    )

                    funcion_heatmap = "sum"

                    titulo_valor_heatmap = (
                        "Carga física"
                    )


                elif metrica_heatmap_fisico == "RPE físico":

                    columna_heatmap = (
                        "RPE real"
                    )

                    funcion_heatmap = "mean"

                    titulo_valor_heatmap = (
                        "RPE medio"
                    )


                else:

                    columna_heatmap = (
                        metrica_heatmap_fisico
                    )

                    funcion_heatmap = "sum"

                    titulo_valor_heatmap = (
                        f"Carga · "
                        f"{metrica_heatmap_fisico}"
                    )


                # =========================================================
                # AGRUPAR POR ALUMNO + SEMANA
                # =========================================================

                df_heatmap_fisico = (
                    df_fisico_bloque
                    .groupby(
                        [
                            "Alumno",
                            "Semana"
                        ],
                        as_index=False
                    )
                    .agg(
                        Valor=(
                            columna_heatmap,
                            funcion_heatmap
                        )
                    )
                )


                df_heatmap_fisico[
                    "Semana"
                ] = (
                    pd.to_numeric(
                        df_heatmap_fisico[
                            "Semana"
                        ],
                        errors="coerce"
                    )
                )


                df_heatmap_fisico[
                    "Valor"
                ] = (
                    pd.to_numeric(
                        df_heatmap_fisico[
                            "Valor"
                        ],
                        errors="coerce"
                    )
                )


                df_heatmap_fisico = (
                    df_heatmap_fisico
                    .dropna(
                        subset=[
                            "Alumno",
                            "Semana"
                        ]
                    )
                )


                df_heatmap_fisico[
                    "Semana"
                ] = (
                    df_heatmap_fisico[
                        "Semana"
                    ]
                    .astype(int)
                )


                # =========================================================
                # TODAS LAS SEMANAS DEL BLOQUE
                # =========================================================

                semanas_heatmap = list(
                    range(
                        semana_inicio,
                        semana_fin + 1
                    )
                )


                alumnos_heatmap = sorted(
                    df_fisico_bloque[
                        "Alumno"
                    ]
                    .dropna()
                    .astype(str)
                    .str.strip()
                    .unique()
                    .tolist()
                )


                # =========================================================
                # CREAR CUADRÍCULA COMPLETA
                #
                # Esto permite mostrar también semanas donde un atleta
                # todavía no tiene registros.
                # =========================================================

                cuadrilla_heatmap = (
                    pd.MultiIndex
                    .from_product(
                        [
                            alumnos_heatmap,
                            semanas_heatmap
                        ],
                        names=[
                            "Alumno",
                            "Semana"
                        ]
                    )
                    .to_frame(
                        index=False
                    )
                )


                df_heatmap_completo = (
                    cuadrilla_heatmap
                    .merge(
                        df_heatmap_fisico,
                        on=[
                            "Alumno",
                            "Semana"
                        ],
                        how="left"
                    )
                )


                # =========================================================
                # TEXTO DENTRO DE LAS CELDAS
                # =========================================================

                df_heatmap_completo[
                    "Etiqueta"
                ] = (
                    df_heatmap_completo[
                        "Valor"
                    ]
                    .apply(
                        lambda valor:
                            ""
                            if pd.isna(valor)
                            else f"{valor:.1f}"
                    )
                )


                df_heatmap_completo[
                    "Estado"
                ] = (
                    df_heatmap_completo[
                        "Valor"
                    ]
                    .apply(
                        lambda valor:
                            "Sin registro"
                            if pd.isna(valor)
                            else "Con registro"
                    )
                )


                # =========================================================
                # ORDENAR ATLETAS SEGÚN LA MÉTRICA
                # =========================================================

                if metrica_heatmap_fisico == "RPE físico":

                    ranking_heatmap = (
                        df_heatmap_fisico
                        .groupby(
                            "Alumno"
                        )[
                            "Valor"
                        ]
                        .mean()
                        .sort_values(
                            ascending=False
                        )
                        .index
                        .tolist()
                    )


                else:

                    ranking_heatmap = (
                        df_heatmap_fisico
                        .groupby(
                            "Alumno"
                        )[
                            "Valor"
                        ]
                        .sum()
                        .sort_values(
                            ascending=False
                        )
                        .index
                        .tolist()
                    )


                # =========================================================
                # HEATMAP
                # =========================================================

                st.subheader(
                    f"{metrica_heatmap_fisico} por semana"
                )


                base_heatmap = (
                    alt.Chart(
                        df_heatmap_completo
                    )
                    .encode(

                        x=alt.X(
                            "Semana:O",
                            title="Semana",
                            sort=semanas_heatmap
                        ),

                        y=alt.Y(
                            "Alumno:N",
                            title="Atleta",
                            sort=ranking_heatmap
                        )
                    )
                )


                # =========================================================
                # ESCALA RPE 0–10
                # =========================================================

                if metrica_heatmap_fisico == "RPE físico":

                    rect_heatmap = (
                        base_heatmap
                        .mark_rect()
                        .encode(

                            color=alt.Color(
                                "Valor:Q",
                                title="RPE",
                                scale=alt.Scale(
                                    domain=[
                                        0,
                                        10
                                    ]
                                )
                            ),

                            tooltip=[
                                alt.Tooltip(
                                    "Alumno:N",
                                    title="Atleta"
                                ),

                                alt.Tooltip(
                                    "Semana:O",
                                    title="Semana"
                                ),

                                alt.Tooltip(
                                    "Valor:Q",
                                    title="RPE medio",
                                    format=".1f"
                                ),

                                alt.Tooltip(
                                    "Estado:N",
                                    title="Estado"
                                )
                            ]
                        )
                    )


                else:

                    rect_heatmap = (
                        base_heatmap
                        .mark_rect()
                        .encode(

                            color=alt.Color(
                                "Valor:Q",
                                title=(
                                    titulo_valor_heatmap
                                )
                            ),

                            tooltip=[
                                alt.Tooltip(
                                    "Alumno:N",
                                    title="Atleta"
                                ),

                                alt.Tooltip(
                                    "Semana:O",
                                    title="Semana"
                                ),

                                alt.Tooltip(
                                    "Valor:Q",
                                    title=(
                                        titulo_valor_heatmap
                                    ),
                                    format=".1f"
                                ),

                                alt.Tooltip(
                                    "Estado:N",
                                    title="Estado"
                                )
                            ]
                        )
                    )


                # =========================================================
                # NÚMERO DENTRO DE CADA CELDA
                # =========================================================

                texto_heatmap = (
                    base_heatmap
                    .mark_text(
                        fontSize=11
                    )
                    .encode(
                        text=alt.Text(
                            "Etiqueta:N"
                        )
                    )
                )


                grafica_heatmap_fisico = (
                    rect_heatmap
                    +
                    texto_heatmap
                ).properties(
                    height=max(
                        300,
                        len(
                            alumnos_heatmap
                        )
                        *
                        45
                    )
                )


                st.altair_chart(
                    grafica_heatmap_fisico,
                    use_container_width=True
                )


                st.caption(
                    "Las celdas vacías representan semanas "
                    "sin registros físicos para ese atleta."
                )


                # =========================================================
                # RESUMEN DE LA MÉTRICA
                # =========================================================

                if not df_heatmap_fisico.empty:

                    if metrica_heatmap_fisico == "RPE físico":

                        resumen_heatmap_atletas = (
                            df_heatmap_fisico
                            .groupby(
                                "Alumno",
                                as_index=False
                            )
                            .agg(
                                {
                                    "Valor":
                                        "mean",

                                    "Semana":
                                        "nunique"
                                }
                            )
                            .rename(
                                columns={
                                    "Valor":
                                        "RPE medio",

                                    "Semana":
                                        "Semanas registradas"
                                }
                            )
                        )


                        resumen_heatmap_atletas[
                            "RPE medio"
                        ] = (
                            resumen_heatmap_atletas[
                                "RPE medio"
                            ]
                            .round(1)
                        )


                        resumen_heatmap_atletas = (
                            resumen_heatmap_atletas
                            .sort_values(
                                "RPE medio",
                                ascending=False
                            )
                        )


                    else:

                        resumen_heatmap_atletas = (
                            df_heatmap_fisico
                            .groupby(
                                "Alumno",
                                as_index=False
                            )
                            .agg(
                                {
                                    "Valor":
                                        "sum",

                                    "Semana":
                                        "nunique"
                                }
                            )
                            .rename(
                                columns={
                                    "Valor":
                                        titulo_valor_heatmap,

                                    "Semana":
                                        "Semanas registradas"
                                }
                            )
                        )


                        resumen_heatmap_atletas[
                            titulo_valor_heatmap
                        ] = (
                            resumen_heatmap_atletas[
                                titulo_valor_heatmap
                            ]
                            .round(1)
                        )


                        resumen_heatmap_atletas = (
                            resumen_heatmap_atletas
                            .sort_values(
                                titulo_valor_heatmap,
                                ascending=False
                            )
                        )


                    st.subheader(
                        "Resumen del periodo"
                    )


                    st.dataframe(
                        resumen_heatmap_atletas,
                        use_container_width=True,
                        hide_index=True
                    )


                # =========================================================
                # MATRIZ NUMÉRICA
                # =========================================================

                st.subheader(
                    "Matriz semanal"
                )


                matriz_heatmap = (
                    df_heatmap_fisico
                    .pivot(
                        index="Alumno",
                        columns="Semana",
                        values="Valor"
                    )
                )


                matriz_heatmap = (
                    matriz_heatmap
                    .reindex(
                        index=ranking_heatmap,
                        columns=semanas_heatmap
                    )
                    .round(1)
                )


                st.dataframe(
                    matriz_heatmap,
                    use_container_width=True
                )
                    


    except Exception as error:

        st.error(
            "No se pudo cargar el dashboard físico del grupo."
        )

        st.code(
            str(error)
        )

# =========================================================
# ALERTAS
# =========================================================

elif pagina == "Alertas":

    st.title(
        "Alertas y recomendaciones"
    )

    df_seguimiento = (
        leer_hoja(
            "Seguimiento por bloque"
        )
    )

    bloque_alertas = (
        st.selectbox(
            "Bloque",
            [
                1,
                2,
                3,
                4
            ],
            index=None,
            placeholder="Selecciona un bloque...",
            key="bloque_alertas"
        )
    )

    if bloque_alertas is None:

        st.info(
            "Selecciona un bloque para consultar las alertas."
        )

        st.stop()

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
    ] = (
        pd.to_numeric(
            df_alertas[
                "Semana"
            ],
            errors="coerce"
        )
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
        .tail(
            1
        )
    )

    for _, fila in df_alertas.iterrows():

        alumno_alerta = (
            limpiar_texto(
                fila.get(
                    "Alumno"
                )
            )
        )

        nivel = (
            limpiar_texto(
                fila.get(
                    "Nivel"
                )
            )
        )

        with st.expander(
            f"{alumno_alerta} · {nivel}"
        ):

            col1, col2, col3 = (
                st.columns(
                    3
                )
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
