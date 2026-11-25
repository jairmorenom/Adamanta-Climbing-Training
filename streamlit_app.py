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
# BASE DE DATOS ACONDICIONAMIENTO FÍSICO
# =========================================================

SPREADSHEET_ID_FISICO = (
    "1b08hMJJafom4jtrpF0yRxWMcohpR_AjhMpv9XCzmd4k"
)

HOJAS_FISICO = {
    "ejercicios": "Ejercicios",
    "reglas": "Reglas",
    "sesion": "Sesión",
    "como_usar": "Cómo usar"
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
def leer_hoja(
    nombre_hoja,
    spreadsheet_id=SPREADSHEET_ID,
    header=0
):

    nombre_codificado = urllib.parse.quote(
        nombre_hoja
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
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
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
        float(round(volumen_planificado, 1)),
        int(volumen_real),
        float(round(rpe_planificado, 1)),
        int(rpe_real),
        float(round(carga_planificada, 1)),
        float(round(carga_real, 1))
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
                float(fila[0])
            )

            sesion_existente = int(
                float(fila[1])
            )

        except (
            ValueError,
            TypeError
        ):

            continue

        alumno_existente = (
            str(fila[2])
            .strip()
            .lower()
        )

        if (
            semana_existente == int(semana)
            and sesion_existente == int(sesion)
            and alumno_existente
            == str(alumno).strip().lower()
        ):

            fila_encontrada = numero_fila
            break

    if fila_encontrada:

        sheets_update(
            (
                "'Historial semanal'!"
                f"A{fila_encontrada}:J{fila_encontrada}"
            ),
            [nueva_fila]
        )

        return "actualizado"

    sheets_append(
        "'Historial semanal'!A:J",
        [nueva_fila]
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
            "Mantener volumen y monitorear intensidad"
        )

    if -2 < dif_rpe <= -1:

        return (
            "Considerar aumentar ligeramente "
            "la dificultad"
        )

    return "Mantener planificación actual"


# =========================================================
# COACH INSIGHTS
# =========================================================

def generar_coach_insights(resumen):

    insights = []

    if resumen.empty:
        return insights

    resumen = (
        resumen
        .sort_values("Semana")
        .copy()
    )

    ultimas = resumen.tail(3).copy()
    ultima = resumen.iloc[-1]

    # =====================================================
    # CUMPLIMIENTO GENERAL
    # =====================================================

    volumen_plan_total = (
        resumen["Volumen planificado"].sum()
    )

    volumen_real_total = (
        resumen["Volumen real"].sum()
    )

    carga_plan_total = (
        resumen["Carga planificada"].sum()
    )

    carga_real_total = (
        resumen["Carga real"].sum()
    )

    volumen_pct_total = (
        volumen_real_total
        / volumen_plan_total
        * 100
        if volumen_plan_total > 0
        else 0
    )

    carga_pct_total = (
        carga_real_total
        / carga_plan_total
        * 100
        if carga_plan_total > 0
        else 0
    )

    rpe_plan_total = (
        resumen["RPE planificado"].mean()
    )

    rpe_real_total = (
        resumen["RPE real"].mean()
    )

    dif_rpe_total = (
        rpe_real_total
        -
        rpe_plan_total
    )

    # =====================================================
    # BUENA ADHERENCIA
    # =====================================================

    if (
        90 <= volumen_pct_total <= 110
        and 90 <= carga_pct_total <= 110
        and abs(dif_rpe_total) < 1
    ):

        insights.append({
            "nivel": "POSITIVO",
            "titulo": "Buena adherencia al plan",
            "mensaje": (
                f"El atleta acumula {volumen_pct_total:.1f}% "
                f"del volumen y {carga_pct_total:.1f}% de la carga "
                "planificada, con un RPE cercano al objetivo."
            ),
            "accion": (
                "Mantener la planificación actual mientras "
                "la calidad de ejecución siga siendo buena."
            )
        })

    # =====================================================
    # RPE RECIENTE
    # =====================================================

    if len(ultimas) >= 2:

        rpe_alto = (
            ultimas["Dif. RPE"]
            >= 1
        )

        if rpe_alto.tail(2).all():

            insights.append({
                "nivel": "ATENCION",
                "titulo": "RPE por encima del plan",
                "mensaje": (
                    "Las últimas 2 semanas registradas presentan "
                    "un RPE medio superior al plan."
                ),
                "accion": (
                    "Evitar aumentar volumen o intensidad hasta "
                    "comprobar si el RPE vuelve al rango previsto."
                )
            })

    if len(ultimas) >= 3:

        if (
            ultimas["Dif. RPE"]
            >= 1
        ).all():

            insights.append({
                "nivel": "ALERTA",
                "titulo": "RPE elevado durante 3 semanas",
                "mensaje": (
                    "El esfuerzo percibido se ha mantenido por encima "
                    "de lo planificado durante las últimas 3 semanas."
                ),
                "accion": (
                    "Revisar la carga de la siguiente semana y considerar "
                    "reducir temporalmente volumen o intensidad."
                )
            })

    # =====================================================
    # ADAPTACIÓN POSITIVA
    # =====================================================

    if len(ultimas) >= 3:

        primera = ultimas.iloc[0]
        reciente = ultimas.iloc[-1]

        aumento_volumen = (
            reciente["Volumen real"]
            >
            primera["Volumen real"] * 1.05
        )

        rpe_estable = (
            reciente["RPE real"]
            <=
            primera["RPE real"] + 0.5
        )

        if aumento_volumen and rpe_estable:

            insights.append({
                "nivel": "POSITIVO",
                "titulo": "Posible adaptación positiva",
                "mensaje": (
                    "El volumen real ha aumentado en las últimas semanas "
                    "sin un aumento proporcional del RPE."
                ),
                "accion": (
                    "Mantener la progresión prevista. Si la técnica y la "
                    "recuperación son buenas, puede continuar el incremento "
                    "gradual planificado."
                )
            })

    # =====================================================
    # MENOS VOLUMEN + MAYOR RPE
    # =====================================================

    if len(ultimas) >= 2:

        anterior = ultimas.iloc[-2]
        reciente = ultimas.iloc[-1]

        volumen_baja = (
            reciente["Volumen real"]
            <
            anterior["Volumen real"] * 0.90
        )

        rpe_sube = (
            reciente["RPE real"]
            >
            anterior["RPE real"] + 0.5
        )

        if volumen_baja and rpe_sube:

            insights.append({
                "nivel": "ALERTA",
                "titulo": "Menor volumen con mayor esfuerzo",
                "mensaje": (
                    "La última semana produjo menos volumen que la anterior, "
                    "pero con un RPE mayor."
                ),
                "accion": (
                    "No progresar la carga todavía. Revisar recuperación, "
                    "dificultad de los ejercicios y calidad técnica."
                )
            })

    # =====================================================
    # CAMBIO DE CARGA
    # =====================================================

    if len(ultimas) >= 3:

        carga_inicio = (
            ultimas.iloc[0]["Carga real"]
        )

        carga_final = (
            ultimas.iloc[-1]["Carga real"]
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
                    "nivel": "ATENCION",
                    "titulo": "Aumento rápido de carga",
                    "mensaje": (
                        f"La carga real aumentó aproximadamente "
                        f"{cambio_carga:.1f}% entre la primera y la última "
                        "de las 3 semanas recientes."
                    ),
                    "accion": (
                        "Confirmar que el aumento estaba previsto antes de "
                        "seguir progresando la siguiente semana."
                    )
                })

            elif cambio_carga < -20:

                insights.append({
                    "nivel": "ATENCION",
                    "titulo": "Caída marcada de carga",
                    "mensaje": (
                        f"La carga real disminuyó aproximadamente "
                        f"{abs(cambio_carga):.1f}% durante las últimas "
                        "3 semanas."
                    ),
                    "accion": (
                        "Revisar si corresponde a una descarga programada, "
                        "ausencias o menor cumplimiento del entrenamiento."
                    )
                })

    # =====================================================
    # ÚLTIMA SEMANA
    # =====================================================

    volumen_ultima = (
        ultima["Volumen %"]
    )

    carga_ultima = (
        ultima["Carga %"]
    )

    dif_rpe_ultima = (
        ultima["Dif. RPE"]
    )

    if (
        volumen_ultima < 80
        and dif_rpe_ultima < 1
    ):

        insights.append({
            "nivel": "ATENCION",
            "titulo": "Volumen por debajo del objetivo",
            "mensaje": (
                f"La última semana alcanzó solamente "
                f"{volumen_ultima:.1f}% del volumen planificado."
            ),
            "accion": (
                "Identificar si hubo ausencias o ejercicios incompletos. "
                "Si el RPE y la técnica fueron adecuados, recuperar volumen "
                "de forma progresiva."
            )
        })

    if (
        carga_ultima > 120
        or volumen_ultima > 120
    ):

        insights.append({
            "nivel": "ALERTA",
            "titulo": "La última semana superó el plan",
            "mensaje": (
                f"Volumen: {volumen_ultima:.1f}% · "
                f"Carga: {carga_ultima:.1f}% del objetivo."
            ),
            "accion": (
                "Evitar seguir aumentando la siguiente sesión sin revisar "
                "si el exceso de carga fue intencional."
            )
        })

    # =====================================================
    # SIN SEÑALES RELEVANTES
    # =====================================================

    if not insights:

        insights.append({
            "nivel": "ESTABLE",
            "titulo": "Respuesta estable",
            "mensaje": (
                "No se detectan desviaciones importantes respecto "
                "a la planificación con los datos disponibles."
            ),
            "accion": (
                "Mantener el plan y continuar registrando volumen, "
                "RPE y carga."
            )
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

    rangos = {
        1: (1, 13),
        2: (14, 26),
        3: (27, 39),
        4: (40, 52)
    }

    inicio, fin = rangos[bloque]

    df_bloque = df[
        (df["Semana"] >= inicio)
        &
        (df["Semana"] <= fin)
    ].copy()

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
        df_bloque["Alumno"]
        .astype(str)
        .str.strip()
        .str.title()
    )

    semana_actual = int(
        df_bloque[
            "Semana"
        ].max()
    )

    resumen = (
        df_bloque
        .groupby(
            "Alumno",
            as_index=False
        )
        .agg({
            "Volumen planificado": "sum",
            "Volumen real": "sum",
            "RPE planificado": "mean",
            "RPE real": "mean",
            "Carga planificada": "sum",
            "Carga real": "sum"
        })
    )

    seguimiento_existente = (
        sheets_get(
            "'Seguimiento por bloque'!A:K"
        )
    )

    for _, fila in resumen.iterrows():

        alumno = fila["Alumno"]

        if fila["Volumen planificado"] > 0:

            volumen_pct = (
                fila["Volumen real"]
                /
                fila["Volumen planificado"]
                * 100
            )

        else:

            volumen_pct = 0

        if fila["Carga planificada"] > 0:

            carga_pct = (
                fila["Carga real"]
                /
                fila["Carga planificada"]
                * 100
            )

        else:

            carga_pct = 0

        rpe_plan = float(
            fila["RPE planificado"]
        )

        rpe_real = float(
            fila["RPE real"]
        )

        dif_rpe = (
            rpe_real
            -
            rpe_plan
        )

        nivel = clasificar_estado(
            volumen_pct,
            carga_pct,
            dif_rpe
        )

        estado = generar_estado(
            volumen_pct,
            carga_pct,
            dif_rpe
        )

        recomendacion = generar_recomendacion(
            volumen_pct,
            carga_pct,
            dif_rpe
        )

        nueva_fila = [
            int(bloque),
            semana_actual,
            alumno,
            round(volumen_pct, 1),
            round(rpe_plan, 1),
            round(rpe_real, 1),
            round(dif_rpe, 1),
            round(carga_pct, 1),
            nivel,
            estado,
            recomendacion
        ]

        fila_encontrada = None

        for numero_fila, existente in enumerate(
            seguimiento_existente[1:],
            start=2
        ):

            if len(existente) < 3:
                continue

            try:

                bloque_existente = int(
                    float(existente[0])
                )

                semana_existente = int(
                    float(existente[1])
                )

            except (
                ValueError,
                TypeError
            ):

                continue

            alumno_existente = (
                str(existente[2])
                .strip()
                .lower()
            )

            if (
                bloque_existente == int(bloque)
                and semana_existente == semana_actual
                and alumno_existente
                == alumno.strip().lower()
            ):

                fila_encontrada = numero_fila
                break

        if fila_encontrada:

            sheets_update(
                (
                    "'Seguimiento por bloque'!"
                    f"A{fila_encontrada}:K{fila_encontrada}"
                ),
                [nueva_fila]
            )

        else:

            sheets_append(
                "'Seguimiento por bloque'!A:K",
                [nueva_fila]
            )

            seguimiento_existente.append(
                nueva_fila
            )

# =========================================================
# CARGAR BASE DE ACONDICIONAMIENTO FÍSICO
# =========================================================

try:

    df_ejercicios_fisico = leer_hoja(
        HOJAS_FISICO["ejercicios"],
        SPREADSHEET_ID_FISICO
    )

    df_reglas_fisico = leer_hoja(
        HOJAS_FISICO["reglas"],
        SPREADSHEET_ID_FISICO,
        header=None
    )

    BASE_FISICO_CONECTADA = True


except Exception as e:

    df_ejercicios_fisico = pd.DataFrame()
    df_reglas_fisico = pd.DataFrame()

    BASE_FISICO_CONECTADA = False

    ERROR_BASE_FISICO = str(e)
    
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
        str(error)
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
        "Acondicionamiento físico",
        "Registrar sesión",
        "Seguimiento",
        "Vista grupo",
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
        df_distribucion["Semana"],
        errors="coerce"
    )
)


# =========================================================
# ALUMNOS
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

    st.dataframe(
        pd.DataFrame({
            "Alumno": alumnos
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

    col1, col2 = st.columns(2)

    with col1:

        semana = st.selectbox(
            "Semana",
            list(range(1, 53)),
            index=None,
            placeholder="Selecciona una semana..."
        )

    with col2:

        sesion = st.selectbox(
            "Sesión",
            [1, 2, 3, 4],
            index=None,
            placeholder="Selecciona una sesión..."
        )

    if semana is None or sesion is None:

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
            df_distribucion["Semana"]
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

    df_lista = leer_hoja(
        HOJAS_EJERCICIOS[
            bloque
        ]
    )

    primera_columna = (
        df_lista.columns[0]
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
            coincidencia.index[0]
        )

        fila = (
            df_lista.loc[indice]
        )

        for columna in (
            df_lista.columns[1:6]
        ):

            nombre = limpiar_texto(
                fila[columna]
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

    if not ejercicios:

        for i in range(
            len(df_lista)
        ):

            valor = limpiar_texto(
                df_lista.iloc[i, 0]
            )

            if (
                valor.lower()
                ==
                tipo_sesion.lower()
            ):

                if (
                    i + 1
                    <
                    len(df_lista)
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

    st.divider()

    st.subheader(
        "Ejercicios"
    )

    cantidad = st.slider(
        "Cantidad de ejercicios",
        min_value=1,
        max_value=min(
            5,
            len(ejercicios)
        ),
        value=min(
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

            if columna in df_carga.columns:

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

        col1, col2, col3 = st.columns(3)

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
                    )
            }

            st.success(
                "Sesión lista para registrar."
            )

# =========================================================
# ACONDICIONAMIENTO FÍSICO
# =========================================================
elif pagina == "Acondicionamiento físico":

    st.title("Acondicionamiento físico")

    # =====================================================
    # ESTADO DE CONEXIÓN
    # =====================================================

    if not BASE_FISICO_CONECTADA:

        st.error(
            "No se pudo conectar con la base de "
            "acondicionamiento físico."
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
        len(df_ejercicios_fisico)
    )


    # =====================================================
    # INFORMACIÓN GENERAL
    # =====================================================

    total_ejercicios = len(
        df_ejercicios_fisico
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


    col1, col2, col3 = st.columns(3)


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


    # =====================================================
    # EXPLORADOR DE EJERCICIOS
    # =====================================================

    st.divider()

    st.subheader(
        "Base de ejercicios"
    )


    tipo_seleccionado = st.selectbox(
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


    if tipo_seleccionado is None:

        ejercicios_mostrar = (
            df_ejercicios_fisico.copy()
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


    # =====================================================
    # BUSCADOR
    # =====================================================

    buscar_ejercicio = st.text_input(
        "Buscar ejercicio",
        placeholder=(
            "Ej. dominadas, press, core..."
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


    # =====================================================
    # TABLA
    # =====================================================

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
        "Piernas / cadera"
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
        f"Mostrando {len(ejercicios_mostrar)} "
        f"de {total_ejercicios} ejercicios."
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

    col1, col2, col3 = st.columns(3)

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

        col1, col2 = st.columns(2)

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

    st.caption(
        "Compara la planificación con la ejecución real "
        "y analiza la evolución semanal del atleta."
    )

    # =====================================================
    # LEER HISTORIAL
    # =====================================================

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

        if columna in df_historial.columns:

            df_historial[columna] = pd.to_numeric(
                df_historial[columna],
                errors="coerce"
            )

    # =====================================================
    # SELECCIÓN DE BLOQUE
    # =====================================================

    bloque_analisis = st.selectbox(
        "Bloque",
        [1, 2, 3, 4],
        index=None,
        placeholder="Selecciona un bloque..."
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
        4: (40, 52)
    }

    inicio, fin = rangos[
        bloque_analisis
    ]

    df_bloque = (
        df_historial[
            (
                df_historial["Semana"]
                >= inicio
            )
            &
            (
                df_historial["Semana"]
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

    # =====================================================
    # SELECCIÓN DE ALUMNO
    # =====================================================

    alumno = st.selectbox(
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

    if alumno is None:

        st.info(
            "Selecciona un alumno para ver su seguimiento."
        )

        st.stop()

    # =====================================================
    # FILTRAR ALUMNO
    # =====================================================

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

    # =====================================================
    # RESUMEN SEMANAL
    # =====================================================

    resumen = (
        df_alumno
        .groupby(
            "Semana",
            as_index=False
        )
        .agg({
            "Volumen planificado": "sum",
            "Volumen real": "sum",
            "RPE planificado": "mean",
            "RPE real": "mean",
            "Carga planificada": "sum",
            "Carga real": "sum"
        })
        .sort_values(
            "Semana"
        )
    )

    # =====================================================
    # MÉTRICAS DERIVADAS
    # =====================================================

    resumen["Volumen %"] = (
        resumen["Volumen real"]
        /
        resumen["Volumen planificado"]
        *
        100
    )

    resumen["Carga %"] = (
        resumen["Carga real"]
        /
        resumen["Carga planificada"]
        *
        100
    )

    resumen["Dif. RPE"] = (
        resumen["RPE real"]
        -
        resumen["RPE planificado"]
    )

    # =====================================================
    # MÉTRICAS DEL BLOQUE
    # =====================================================

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

    if volumen_plan_total > 0:

        volumen_pct_total = (
            volumen_real_total
            /
            volumen_plan_total
            *
            100
        )

    else:

        volumen_pct_total = 0

    if carga_plan_total > 0:

        carga_pct_total = (
            carga_real_total
            /
            carga_plan_total
            *
            100
        )

    else:

        carga_pct_total = 0

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

    # =====================================================
    # ENCABEZADO
    # =====================================================

    st.divider()

    st.subheader(
        alumno
    )

    st.caption(
        f"Bloque {bloque_analisis} · "
        f"Semanas {inicio}–{fin} · "
        f"{sesiones_realizadas} sesiones registradas"
    )

    # =====================================================
    # KPIs PRINCIPALES
    # =====================================================

    col1, col2, col3, col4 = (
        st.columns(4)
    )

    with col1:

        st.metric(
            "Volumen cumplido",
            f"{volumen_pct_total:.1f}%",
            delta=(
                f"{volumen_pct_total - 100:+.1f}% "
                "vs plan"
            )
        )

    with col2:

        st.metric(
            "Carga cumplida",
            f"{carga_pct_total:.1f}%",
            delta=(
                f"{carga_pct_total - 100:+.1f}% "
                "vs plan"
            )
        )

    with col3:

        st.metric(
            "RPE medio",
            f"{rpe_real_total:.1f}",
            delta=(
                f"{dif_rpe_total:+.1f} "
                "vs plan"
            ),
            delta_color="inverse"
        )

    with col4:

        st.metric(
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

    # =====================================================
    # COACH INSIGHTS
    # =====================================================

    st.divider()

    st.subheader(
        "Coach Insights"
    )

    st.caption(
        "Interpretación automática de la respuesta del atleta "
        "respecto a la planificación."
    )

    insights = generar_coach_insights(
        resumen
    )

    for insight in insights:

        nivel = insight["nivel"]
        titulo = insight["titulo"]
        mensaje = insight["mensaje"]
        accion = insight["accion"]

        if nivel == "POSITIVO":

            with st.container(
                border=True
            ):

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

            with st.container(
                border=True
            ):

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

            with st.container(
                border=True
            ):

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

            with st.container(
                border=True
            ):

                st.markdown(
                    f"### 🔵 {titulo}"
                )

                st.write(
                    mensaje
                )

                st.info(
                    f"**Acción sugerida:** {accion}"
                )

    # =====================================================
    # ÚLTIMA SEMANA
    # =====================================================

    st.divider()

    st.subheader(
        "Última semana registrada"
    )

    col1, col2, col3 = (
        st.columns(3)
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

    # =====================================================
    # TABS
    # =====================================================

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

    # =====================================================
    # GRÁFICA VOLUMEN
    # =====================================================

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
                    )
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
            "El objetivo es observar si el volumen real "
            "se mantiene cerca de la planificación a lo largo "
            "del bloque."
        )

    # =====================================================
    # GRÁFICA CARGA
    # =====================================================

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
                    )
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
            "La carga combina el volumen realizado "
            "con el RPE reportado."
        )

    # =====================================================
    # GRÁFICA RPE
    # =====================================================

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
                    )
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
            "Una separación creciente entre RPE planificado "
            "y RPE real indica que la respuesta del atleta "
            "está cambiando respecto al plan."
        )

    # =====================================================
    # TABLA SEMANAL
    # =====================================================

    with tab_tabla:

        st.subheader(
            "Cumplimiento semanal"
        )

        tabla = resumen[
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
                "Carga %"
            ]
        ].copy()

        tabla["Volumen %"] = (
            tabla["Volumen %"].round(1)
        )

        tabla["Carga %"] = (
            tabla["Carga %"].round(1)
        )

        tabla["RPE planificado"] = (
            tabla["RPE planificado"].round(1)
        )

        tabla["RPE real"] = (
            tabla["RPE real"].round(1)
        )

        tabla["Dif. RPE"] = (
            tabla["Dif. RPE"].round(1)
        )

        st.dataframe(
            tabla,
            use_container_width=True,
            hide_index=True
        )
    # =====================================================
    # RELACIÓN VOLUMEN – RPE
    # =====================================================

    st.divider()

    st.subheader(
        "Relación Volumen – RPE"
    )

    st.caption(
        "Cada punto representa una semana registrada. "
        "La posición muestra cuánto volumen produjo el atleta "
        "para el nivel de esfuerzo percibido."
    )

    # =====================================================
    # DATOS PARA SCATTER
    # =====================================================

    scatter_data = resumen[
        [
            "Semana",
            "Volumen real",
            "RPE real",
            "Volumen %",
            "Carga %",
            "Dif. RPE"
        ]
    ].copy()

    scatter_data = scatter_data.dropna(
        subset=[
            "Semana",
            "Volumen real",
            "RPE real"
        ]
    )

    scatter_data["Semana texto"] = (
        "Semana "
        +
        scatter_data[
            "Semana"
        ]
        .astype(int)
        .astype(str)
    )

    # =====================================================
    # SCATTER
    # =====================================================

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
                )
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


    # =====================================================
    # INTERPRETACIÓN DE LA TENDENCIA
    # =====================================================

    if len(scatter_data) >= 2:

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

        # ---------------------------------------------
        # MÁS VOLUMEN + RPE ESTABLE / MENOR
        # ---------------------------------------------

        if (
            cambio_volumen > 0
            and cambio_rpe <= 0.5
        ):

            st.success(
                "✅ Posible adaptación positiva: "
                "el atleta está produciendo más volumen "
                "sin un aumento proporcional del RPE."
            )

            st.write(
                "Esto puede indicar una mejor tolerancia "
                "al estímulo. Si la técnica y la recuperación "
                "son buenas, la progresión puede mantenerse."
            )

        # ---------------------------------------------
        # MENOS VOLUMEN + MÁS RPE
        # ---------------------------------------------

        elif (
            cambio_volumen < 0
            and cambio_rpe > 0.5
        ):

            st.error(
                "🔴 Señal de atención: "
                "el atleta está produciendo menos volumen "
                "con mayor esfuerzo percibido."
            )

            st.write(
                "Conviene revisar recuperación, dificultad "
                "de las sesiones y calidad de ejecución antes "
                "de progresar la carga."
            )

        # ---------------------------------------------
        # MISMO VOLUMEN + MENOS RPE
        # ---------------------------------------------

        elif (
            abs(cambio_volumen)
            <=
            primera_semana_scatter[
                "Volumen real"
            ] * 0.10
            and cambio_rpe < -0.5
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

        # ---------------------------------------------
        # MÁS VOLUMEN + MÁS RPE
        # ---------------------------------------------

        elif (
            cambio_volumen > 0
            and cambio_rpe > 0.5
        ):

            st.warning(
                "🟠 La carga de trabajo está aumentando "
                "junto con el esfuerzo percibido."
            )

            st.write(
                "No necesariamente es negativo si estaba "
                "planificado. Conviene observar las próximas "
                "semanas antes de seguir aumentando."
            )

        # ---------------------------------------------
        # ESTABLE
        # ---------------------------------------------

        else:

            st.info(
                "🔵 Relación Volumen–RPE estable."
            )

            st.write(
                "No se observa un cambio suficientemente "
                "grande para inferir una tendencia clara."
            )

    else:

        st.info(
            "Se necesitan al menos 2 semanas registradas "
            "para interpretar la tendencia Volumen–RPE."
        )
            # =====================================================
    # PERFIL DE CARGA POR TIPO DE SESIÓN
    # =====================================================

    st.divider()

    st.subheader(
        "Perfil de carga por tipo de sesión"
    )

    st.caption(
        "Analiza qué tipos de entrenamiento están aportando "
        "más carga al bloque y cuánto se ejecutó respecto al plan."
    )


    # =====================================================
    # PREPARAR DATOS
    # =====================================================

    df_tipo = (
        df_alumno[
            [
                "Tipo de sesión",
                "Volumen planificado",
                "Volumen real",
                "RPE planificado",
                "RPE real",
                "Carga planificada",
                "Carga real"
            ]
        ]
        .copy()
    )

    df_tipo = df_tipo.dropna(
        subset=[
            "Tipo de sesión"
        ]
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


    # =====================================================
    # AGRUPAR POR TIPO DE SESIÓN
    # =====================================================

    perfil_tipo = (
        df_tipo
        .groupby(
            "Tipo de sesión",
            as_index=False
        )
        .agg({
            "Volumen planificado": "sum",
            "Volumen real": "sum",
            "RPE planificado": "mean",
            "RPE real": "mean",
            "Carga planificada": "sum",
            "Carga real": "sum"
        })
    )


    # =====================================================
    # MÉTRICAS DERIVADAS
    # =====================================================

    perfil_tipo["Volumen %"] = (
        perfil_tipo["Volumen real"]
        /
        perfil_tipo["Volumen planificado"]
        *
        100
    )

    perfil_tipo["Carga %"] = (
        perfil_tipo["Carga real"]
        /
        perfil_tipo["Carga planificada"]
        *
        100
    )

    perfil_tipo["Dif. RPE"] = (
        perfil_tipo["RPE real"]
        -
        perfil_tipo["RPE planificado"]
    )


    perfil_tipo = perfil_tipo.replace(
        [
            float("inf"),
            float("-inf")
        ],
        pd.NA
    )


    # =====================================================
    # PARTICIPACIÓN EN LA CARGA TOTAL
    # =====================================================

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


    # =====================================================
    # KPIs
    # =====================================================

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
                    x["Dif. RPE"].abs()
            )
            .sort_values(
                "Desviacion_abs",
                ascending=False
            )
            .iloc[0]
        )


        col1, col2, col3 = (
            st.columns(3)
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
                f"RPE {tipo_mayor_rpe['RPE real']:.1f}"
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


    # =====================================================
    # TABS
    # =====================================================

    tab_tipo_carga, tab_tipo_cumplimiento, tab_tipo_rpe = (
        st.tabs(
            [
                "Carga por tipo",
                "Cumplimiento",
                "RPE por tipo"
            ]
        )
    )


    # =====================================================
    # CARGA POR TIPO
    # =====================================================

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
                    )
                ]
            )
            .properties(
                height=max(
                    280,
                    len(
                        perfil_tipo
                    ) * 45
                )
            )
        )

        st.altair_chart(
            grafica_carga_tipo,
            use_container_width=True
        )

        st.caption(
            "Permite detectar qué tipos de sesión están "
            "aportando la mayor proporción de carga del bloque."
        )


    # =====================================================
    # CUMPLIMIENTO PLAN VS REAL
    # =====================================================

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
                    )
                ]
            )
            .properties(
                height=max(
                    280,
                    len(
                        perfil_tipo
                    ) * 55
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

        tabla_tipo = perfil_tipo[
            [
                "Tipo de sesión",
                "Volumen %",
                "Carga %",
                "RPE planificado",
                "RPE real",
                "Dif. RPE"
            ]
        ].copy()

        tabla_tipo[
            "Volumen %"
        ] = (
            tabla_tipo[
                "Volumen %"
            ]
            .round(1)
        )

        tabla_tipo[
            "Carga %"
        ] = (
            tabla_tipo[
                "Carga %"
            ]
            .round(1)
        )

        tabla_tipo[
            "RPE planificado"
        ] = (
            tabla_tipo[
                "RPE planificado"
            ]
            .round(1)
        )

        tabla_tipo[
            "RPE real"
        ] = (
            tabla_tipo[
                "RPE real"
            ]
            .round(1)
        )

        tabla_tipo[
            "Dif. RPE"
        ] = (
            tabla_tipo[
                "Dif. RPE"
            ]
            .round(1)
        )

        st.dataframe(
            tabla_tipo,
            use_container_width=True,
            hide_index=True
        )


    # =====================================================
    # RPE POR TIPO
    # =====================================================

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
                    )
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


    # =====================================================
    # INTERPRETACIÓN PARA EL COACH
    # =====================================================

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


        # ---------------------------------------------
        # DEMASIADO EXIGENTE
        # ---------------------------------------------

        if (
            carga_pct > 115
            and dif_rpe >= 1
        ):

            st.error(
                f"🔴 **{tipo}:** carga {carga_pct:.1f}% "
                f"y ΔRPE {dif_rpe:+.1f}. "
                "Este estímulo está siendo más exigente "
                "de lo previsto."
            )


        # ---------------------------------------------
        # POCO ESTÍMULO
        # ---------------------------------------------

        elif (
            carga_pct < 85
            and dif_rpe <= 0
        ):

            st.info(
                f"🔵 **{tipo}:** carga {carga_pct:.1f}% "
                f"y ΔRPE {dif_rpe:+.1f}. "
                "El estímulo ejecutado está por debajo "
                "de lo planificado."
            )


        # ---------------------------------------------
        # MENOS VOLUMEN PERO ALTO RPE
        # ---------------------------------------------

        elif (
            volumen_pct < 85
            and dif_rpe >= 1
        ):

            st.warning(
                f"🟠 **{tipo}:** solo se completó "
                f"{volumen_pct:.1f}% del volumen, pero el "
                f"RPE estuvo {dif_rpe:+.1f} sobre el plan. "
                "Conviene revisar la dificultad del estímulo."
            )


        # ---------------------------------------------
        # CORRECTO
        # ---------------------------------------------

        elif (
            90 <= carga_pct <= 110
            and abs(dif_rpe) < 1
        ):

            st.success(
                f"✅ **{tipo}:** respuesta acorde al plan "
                f"(Carga {carga_pct:.1f}% · "
                f"ΔRPE {dif_rpe:+.1f})."
            )


        # ---------------------------------------------
        # INTERMEDIO
        # ---------------------------------------------

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

    # =====================================================
    # LEER HISTORIAL
    # =====================================================

    df_grupo = leer_hoja(
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

        if columna in df_grupo.columns:

            df_grupo[columna] = pd.to_numeric(
                df_grupo[columna],
                errors="coerce"
            )

    # =====================================================
    # SELECCIONAR BLOQUE
    # =====================================================

    bloque_grupo = st.selectbox(
        "Bloque",
        [1, 2, 3, 4],
        index=None,
        placeholder="Selecciona un bloque...",
        key="bloque_grupo"
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
        4: (40, 52)
    }

    inicio, fin = rangos[
        bloque_grupo
    ]

    df_grupo = (
        df_grupo[
            (
                df_grupo["Semana"]
                >= inicio
            )
            &
            (
                df_grupo["Semana"]
                <= fin
            )
        ]
        .copy()
    )

    if df_grupo.empty:

        st.info(
            "No existen registros para este bloque."
        )

        st.stop()

    # =====================================================
    # LIMPIAR
    # =====================================================

    df_grupo = df_grupo.dropna(
        subset=[
            "Alumno",
            "Semana",
            "Volumen planificado",
            "Volumen real",
            "RPE planificado",
            "RPE real",
            "Carga planificada",
            "Carga real"
        ]
    )

    df_grupo["Alumno"] = (
        df_grupo["Alumno"]
        .astype(str)
        .str.strip()
    )

    # =====================================================
    # RESUMEN SEMANAL POR ATLETA
    # =====================================================

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
            "Volumen planificado": "sum",
            "Volumen real": "sum",
            "RPE planificado": "mean",
            "RPE real": "mean",
            "Carga planificada": "sum",
            "Carga real": "sum",
            "Sesión": "count"
        })
        .rename(
            columns={
                "Sesión": "Sesiones registradas"
            }
        )
    )

    # =====================================================
    # MÉTRICAS
    # =====================================================

    resumen_grupo["Volumen %"] = (
        resumen_grupo["Volumen real"]
        /
        resumen_grupo["Volumen planificado"]
        *
        100
    )

    resumen_grupo["Carga %"] = (
        resumen_grupo["Carga real"]
        /
        resumen_grupo["Carga planificada"]
        *
        100
    )
    # =====================================================
    # DIFERENCIA RPE
    # =====================================================

    resumen_grupo["RPE planificado"] = pd.to_numeric(
        resumen_grupo["RPE planificado"],
        errors="coerce"
    )

    resumen_grupo["RPE real"] = pd.to_numeric(
        resumen_grupo["RPE real"],
        errors="coerce"
    )

    resumen_grupo["Dif. RPE"] = (
        resumen_grupo["RPE real"]
        -
        resumen_grupo["RPE planificado"]
    )

    resumen_grupo["Dif. RPE"] = pd.to_numeric(
        resumen_grupo["Dif. RPE"],
        errors="coerce"
    )

    resumen_grupo = resumen_grupo.replace(
        [
            float("inf"),
            float("-inf")
        ],
        pd.NA
    )

    resumen_grupo = resumen_grupo.dropna(
        subset=[
            "Volumen %",
            "Carga %",
            "Dif. RPE"
        ]
    )

    # =====================================================
    # NIVEL DE ATENCIÓN
    # =====================================================

    resumen_grupo["Nivel"] = resumen_grupo.apply(
        lambda fila: clasificar_estado(
            fila["Volumen %"],
            fila["Carga %"],
            fila["Dif. RPE"]
        ),
        axis=1
    )

    mapa_nivel = {
        "OK": 0,
        "MONITOREAR": 1,
        "REVISAR": 2,
        "ALTA": 3
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
            "MONITOREAR": "MON",
            "REVISAR": "REV"
        })
    )

    # =====================================================
    # SEMANA MÁS RECIENTE
    # =====================================================

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

    # =====================================================
    # KPIs DEL GRUPO
    # =====================================================

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
        f"Semana más reciente: {semana_reciente}"
    )

    col1, col2, col3, col4 = (
        st.columns(4)
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

    # =====================================================
    # HEATMAP DEL GRUPO
    # =====================================================

    st.divider()

    st.subheader(
        "Heatmap del grupo"
    )

    metrica_heatmap = st.selectbox(
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

    if metrica_heatmap is None:

        st.info(
            "Selecciona una métrica para generar el heatmap."
        )

    else:

        # =================================================
        # COPIA DE DATOS PARA VISUALIZACIÓN
        # =================================================

        df_heatmap = resumen_grupo.copy()

        df_heatmap["Semana"] = pd.to_numeric(
            df_heatmap["Semana"],
            errors="coerce"
        )

        df_heatmap["Carga %"] = pd.to_numeric(
            df_heatmap["Carga %"],
            errors="coerce"
        )

        df_heatmap["Volumen %"] = pd.to_numeric(
            df_heatmap["Volumen %"],
            errors="coerce"
        )

        df_heatmap["Dif. RPE"] = pd.to_numeric(
            df_heatmap["Dif. RPE"],
            errors="coerce"
        )

        df_heatmap["RPE planificado"] = pd.to_numeric(
            df_heatmap["RPE planificado"],
            errors="coerce"
        )

        df_heatmap["RPE real"] = pd.to_numeric(
            df_heatmap["RPE real"],
            errors="coerce"
        )

        df_heatmap = df_heatmap.dropna(
            subset=[
                "Alumno",
                "Semana"
            ]
        )


        # =================================================
        # NIVEL DE ATENCIÓN
        # =================================================

        if metrica_heatmap == "Nivel de atención":

            df_chart = df_heatmap.dropna(
                subset=[
                    "Nivel"
                ]
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
                        )
                    ]
                )
                .properties(
                    height=max(
                        250,
                        atletas_registrados * 55
                    )
                )
            )


        # =================================================
        # CARGA
        # =================================================

        elif metrica_heatmap == "Carga %":

            df_chart = df_heatmap.dropna(
                subset=[
                    "Carga %"
                ]
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
                        )
                    ]
                )
                .properties(
                    height=max(
                        250,
                        atletas_registrados * 55
                    )
                )
            )


        # =================================================
        # VOLUMEN
        # =================================================

        elif metrica_heatmap == "Volumen %":

            df_chart = df_heatmap.dropna(
                subset=[
                    "Volumen %"
                ]
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
                        )
                    ]
                )
                .properties(
                    height=max(
                        250,
                        atletas_registrados * 55
                    )
                )
            )


        # =================================================
        # Δ RPE
        # =================================================
        # =================================================
        # Δ RPE
        # =================================================

        else:

            df_chart = df_heatmap[
                [
                    "Alumno",
                    "Semana",
                    "RPE planificado",
                    "RPE real",
                    "Dif. RPE",
                    "Carga %",
                    "Volumen %",
                    "Nivel"
                ]
            ].copy()

            # ---------------------------------------------
            # LIMPIEZA ESPECÍFICA
            # ---------------------------------------------

            df_chart["Dif. RPE"] = pd.to_numeric(
                df_chart["Dif. RPE"],
                errors="coerce"
            )

            df_chart["RPE planificado"] = pd.to_numeric(
                df_chart["RPE planificado"],
                errors="coerce"
            )

            df_chart["RPE real"] = pd.to_numeric(
                df_chart["RPE real"],
                errors="coerce"
            )

            df_chart = df_chart.dropna(
                subset=[
                    "Alumno",
                    "Semana",
                    "Dif. RPE"
                ]
            )

            # Forzar tipo numérico normal
            df_chart["Dif. RPE"] = (
                df_chart["Dif. RPE"]
                .astype(float)
            )

            # Convertir semana a categoría de texto
            # Esto evita problemas cuando solo hay una semana
            df_chart["Semana heatmap"] = (
                df_chart["Semana"]
                .astype(int)
                .astype(str)
            )

            # Texto que aparecerá dentro de cada celda
            df_chart["Δ RPE texto"] = (
                df_chart["Dif. RPE"]
                .map(
                    lambda x: f"{x:+.1f}"
                )
            )

            # ---------------------------------------------
            # HEATMAP BASE
            # ---------------------------------------------

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
                        )
                    ]
                )
                .properties(
                    height=max(
                        250,
                        atletas_registrados * 55
                    )
                )
            )

            # ---------------------------------------------
            # VALOR DENTRO DE LA CELDA
            # ---------------------------------------------

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

            # ---------------------------------------------
            # COMBINAR
            # ---------------------------------------------

            grafica_final = (
                heatmap_rpe
                +
                texto_rpe
            )


        # =================================================
        # MOSTRAR GRÁFICA
        # =================================================

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
    # =====================================================
    # PRIORIDADES DEL COACH
    # =====================================================

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

        nivel = fila["Nivel"]

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
        [1, 2, 3, 4],
        index=None,
        placeholder="Selecciona un bloque...",
        key="bloque_alertas"
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

        alumno_alerta = limpiar_texto(
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
            f"{alumno_alerta} · {nivel}"
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
