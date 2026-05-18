import math
import random
from collections import Counter

# =========================================================
# OVERPLAY V5 — EMOTION ENGINE
# =========================================================

def calcular_metricas_core(
    fechas_reproduccion,
    fecha_objetivo,
    meta_cancion,
    volumen_artista,
    factor_sensibilidad=1.0
):
    """
    OVERPLAY V5: EMOTION ENGINE

    Devuelve:
    - fatiga
    - lambda
    - pico_historico
    - burn_rate
    - metrics_emocionales
    """

    # =========================================================
    # VALIDACIÓN INICIAL
    # =========================================================

    fechas_validas = sorted([
        f for f in fechas_reproduccion
        if f <= fecha_objetivo
    ])

    if not fechas_validas:
        return {
            "fatiga": 0.0,
            "lambda": 0.05,
            "pico": 0.0,
            "burn_rate": 0.0,
            "emocional": {}
        }

    # =========================================================
    # METADATOS
    # =========================================================

    total = len(fechas_validas)

    dias_existencia = max(
        1,
        (fecha_objetivo - fechas_validas[0]).days
    )

    pop = meta_cancion.get("pop") or 50
    año = meta_cancion.get("año")
    pico_previo = meta_cancion.get("pico_previo") or 0.0

    generos = str(
        meta_cancion.get("generos") or ""
    ).lower()

    # =========================================================
    # MULTIPLICADORES BASE
    # =========================================================

    multi_genero = 1.0

    if any(g in generos for g in [
        "reggaeton", "trap", "urbano", "dembow"
    ]):
        multi_genero = 1.15

    elif any(g in generos for g in [
        "ambient", "lo-fi", "jazz", "classical"
    ]):
        multi_genero = 0.82

    # =========================================================
    # ANTIGÜEDAD
    # =========================================================

    resistencia_nostalgia = 1.0

    if año:
        antiguedad = max(0, fecha_objetivo.year - año)

        # Las canciones antiguas aguantan mejor
        resistencia_nostalgia = min(
            1.35,
            1 + (antiguedad * 0.015)
        )

    # =========================================================
    # RADIACIÓN GLOBAL (NUEVA VERSIÓN)
    # =========================================================

    multiplicador_radiacion = 1 + (
        math.log(volumen_artista + 1) * 0.08
    )

    multiplicador_reignicion = 1 + (
        pico_previo * 0.0015
    )

    # =========================================================
    # LAMBDA BASE
    # =========================================================

    lambda_base = 0.04 + (
        (pop - 50) * 0.0004
    )

    # =========================================================
    # FATIGA ACUMULADA
    # =========================================================

    puntos_fatiga = 0.0

    fecha_anterior = None

    binge_total = 0

    sesiones_nocturnas = 0

    dias_con_escuchas = Counter()

    gaps = []

    for f in fechas_validas:

        dias_pasados = (
            fecha_objetivo - f
        ).days

        dias_con_escuchas[f.date()] += 1

        # =====================================================
        # NOCTURNIDAD
        # =====================================================

        if 0 <= f.hour <= 5:
            sesiones_nocturnas += 1

        # =====================================================
        # DAÑO BASE
        # =====================================================

        daño_base = (
            4.5 +
            (math.log(total + 1) * 2.2)
        )

        daño_base *= factor_sensibilidad

        # =====================================================
        # ATRACONES
        # =====================================================

        multiplicador_atracon = 1.0

        if fecha_anterior:

            horas_diff = (
                (f - fecha_anterior)
                .total_seconds() / 3600
            )

            gap_dias = (
                f - fecha_anterior
            ).days

            gaps.append(gap_dias)

            # BINGE
            if horas_diff < 2:
                multiplicador_atracon += 1.2
                binge_total += 1

            elif horas_diff < 6:
                multiplicador_atracon += 0.6
                binge_total += 1

            elif horas_diff < 24:
                multiplicador_atracon += 0.15

        # =====================================================
        # VARIABILIDAD HUMANA
        # =====================================================

        ruido_emocional = random.uniform(
            0.95,
            1.08
        )

        # =====================================================
        # FATIGA FINAL
        # =====================================================

        daño_final = (
            daño_base *
            multiplicador_atracon *
            multiplicador_radiacion *
            multiplicador_reignicion *
            multi_genero *
            ruido_emocional
        )

        # =====================================================
        # DECAIMIENTO
        # =====================================================

        puntos_fatiga += (
            daño_final *
            math.exp(
                -lambda_base * dias_pasados
            )
        )

        fecha_anterior = f

    # =========================================================
    # CICATRIZ HISTÓRICA
    # =========================================================

    puntos_fatiga += max(
        min(total * 0.15, 18),
        pico_previo * 0.12
    )

    # =========================================================
    # BURN RATE
    # =========================================================

    burn_rate = (
        puntos_fatiga / dias_existencia
    )

    # =========================================================
    # OBSESIÓN
    # =========================================================

    escuchas_7d = sum(
        1 for f in fechas_validas
        if (fecha_objetivo - f).days <= 7
    )

    dias_activos_7d = len(set([
        f.date()
        for f in fechas_validas
        if (fecha_objetivo - f).days <= 7
    ]))

    indice_obsesion = (
        (escuchas_7d ** 2)
        / (dias_activos_7d + 1)
    )

    # =========================================================
    # NOSTALGIA
    # =========================================================

    gap_medio = (
        sum(gaps) / len(gaps)
        if gaps else 0
    )

    supervivencia = min(
        dias_existencia / 365,
        5
    )

    indice_nostalgia = (
        math.log(total + 1) *
        max(gap_medio, 1) *
        supervivencia *
        resistencia_nostalgia
    ) / 10

    # =========================================================
    # REFUGIO EMOCIONAL
    # =========================================================

    ratio_nocturno = (
        sesiones_nocturnas / total
    )

    cancion_refugio = ratio_nocturno >= 0.6

    # =========================================================
    # TRAUMA MUSICAL
    # =========================================================

    abandono_reciente = False

    ultima_escucha = fechas_validas[-1]

    if (
        (fecha_objetivo - ultima_escucha).days > 30
        and burn_rate > 3
    ):
        abandono_reciente = True

    trauma_score = (
        burn_rate *
        (puntos_fatiga / 50)
    )

    # =========================================================
    # RECUPERACIÓN ESTIMADA
    # =========================================================

    lambda_recuperacion = max(
        0.02,
        lambda_base + (burn_rate * 0.003)
    )

    dias_recuperacion = (
        math.log(
            max(puntos_fatiga, 1)
        ) / lambda_recuperacion
    )

    dias_recuperacion = int(
        min(
            max(dias_recuperacion, 1),
            180
        )
    )

    # =========================================================
    # AJUSTE DINÁMICO DE LAMBDA
    # =========================================================

    score_reciente = (
        escuchas_7d * 0.7
    ) - (
        puntos_fatiga * 0.3
    )

    penalizacion_burn = min(
        burn_rate * 0.005,
        0.04
    )

    if score_reciente > 0:
        lambda_final = min(
            0.16,
            lambda_base +
            penalizacion_burn +
            (score_reciente * 0.008)
        )

    else:
        lambda_final = max(
            0.01,
            lambda_base +
            penalizacion_burn +
            (score_reciente * 0.004)
        )

    # =========================================================
    # AFINIDAD
    # =========================================================

    afinidad = (
        indice_nostalgia * 0.4 +
        supervivencia * 4 +
        (1 - min(
            burn_rate / 10,
            1
        )) * 15
    )

    afinidad = round(
        min(100, max(0, afinidad)),
        2
    )

    # =========================================================
    # ÍNDICE FINAL
    # =========================================================

    riesgo_burnout = (
        puntos_fatiga *
        (1 - (afinidad / 100))
    )

    # =========================================================
    # NUEVO PICO
    # =========================================================

    nuevo_pico = max(
        pico_previo,
        puntos_fatiga
    )

    # =========================================================
    # CLASIFICACIONES HUMANAS
    # =========================================================

    etiquetas = []

    if indice_obsesion > 35:
        etiquetas.append("obsesion")

    if indice_nostalgia > 12:
        etiquetas.append("nostalgia")

    if cancion_refugio:
        etiquetas.append("refugio")

    if trauma_score > 8:
        etiquetas.append("trauma")

    if dias_existencia > 700 and burn_rate < 1:
        etiquetas.append("main_character")

    # =========================================================
    # OUTPUT
    # =========================================================

    return {

        "fatiga": round(puntos_fatiga, 2),

        "lambda": round(lambda_final, 4),

        "pico": round(nuevo_pico, 2),

        "burn_rate": round(burn_rate, 2),

        "afinidad": afinidad,

        "riesgo_burnout": round(
            riesgo_burnout,
            2
        ),

        "dias_recuperacion": dias_recuperacion,

        "emocional": {

            "obsesion": round(
                indice_obsesion,
                2
            ),

            "nostalgia": round(
                indice_nostalgia,
                2
            ),

            "trauma": round(
                trauma_score,
                2
            ),

            "ratio_nocturno": round(
                ratio_nocturno,
                2
            ),

            "etiquetas": etiquetas,

            "abandono_reciente": abandono_reciente
        }
    }
