import math

def calcular_metricas_core(fechas_reproduccion, fecha_objetivo, meta_cancion, volumen_artista, factor_sensibilidad=1.0):
    """
    Motor matemático aislado. Calcula fatiga, lambda y burn_rate en un punto exacto del tiempo.
    """
    # 1. Filtramos reproducciones del futuro (Vital para la máquina del tiempo)
    fechas_validas = sorted([f for f in fechas_reproduccion if f <= fecha_objetivo])
    if not fechas_validas:
        return 0.0, 0.05, 0.0, 0.0 # fatiga, lambda, pico, burn_rate
        
    total = len(fechas_validas)
    dias_desde_descubrimiento = max(1, (fecha_objetivo - fechas_validas[0]).days)
    
   # 2. EXTRACCIÓN DE METADATOS (Blindada contra NULLs)
    # Si el valor es None, forzamos el valor por defecto
    pop = meta_cancion.get('pop')
    if pop is None: pop = 50
    
    año_cancion = meta_cancion.get('año')
    # Si no hay año, lo dejamos como None para que no penalice por edad
    
    pico_previo = meta_cancion.get('pico_previo')
    if pico_previo is None: pico_previo = 0.0
    
    generos = str(meta_cancion.get('generos') or '').lower()
    
    # -----------------------------
    # 🧬 MULTIPLICADORES NUEVOS
    # -----------------------------
    # GÉNEROS: Urbano quema más rápido, acústico relaja.
    multi_genero = 1.0
    if any(g in generos for g in ['reggaeton', 'trap', 'urbano', 'dembow']):
        multi_genero = 1.15 
    elif any(g in generos for g in ['lo-fi', 'classical', 'ambient', 'jazz']):
        multi_genero = 0.85
        
    # EDAD (Fecha de salida): Los clásicos aguantan mejor el paso del tiempo
    penalizacion_edad = 0.0
    if año_cancion:
        # En 2026, una canción de 2016 tiene 10 años de antigüedad.
        antiguedad = max(0, fecha_objetivo.year - año_cancion)
        # Sube el suelo de fatiga un poco por ser vieja, pero la hace más resistente a atracones
        penalizacion_edad = min(antiguedad * 0.15, 10.0) 

    # RADIACIÓN GLOBAL DEL ARTISTA
    multiplicador_radiacion = 1.0 + (volumen_artista * 0.01)
    multiplicador_reignicion = 1.0 + (pico_previo * 0.0015)

    lambda_base = 0.05 + ((pop - 50) * 0.0005)

    # -----------------------------
    # 🔥 BUCLE DE DAÑO ACUMULATIVO
    # -----------------------------
    puntos_fatiga = 0.0
    fecha_anterior = None

    for f in fechas_validas:
        dias_pasados = (fecha_objetivo - f).days
        daño_base = (5.0 + penalizacion_edad + (math.log(total + 1) * 2.0)) * factor_sensibilidad
        
        multiplicador_atracon = 1.0
        if fecha_anterior:
            horas_diff = (f - fecha_anterior).total_seconds() / 3600
            if horas_diff < 3: multiplicador_atracon += (3 - horas_diff) * 0.4
            elif horas_diff < 24: multiplicador_atracon += (24 - horas_diff) * 0.02

        daño_final = daño_base * multiplicador_atracon * multiplicador_radiacion * multiplicador_reignicion * multi_genero
        puntos_fatiga += daño_final * math.exp(-lambda_base * dias_pasados)
        fecha_anterior = f

    # -----------------------------
    # 🚀 BURN RATE (La nueva métrica)
    # -----------------------------
    # Puntos generados por día de media. Si es mayor a 3, estás obsesionado.
    burn_rate = puntos_fatiga / dias_desde_descubrimiento
    
    # Si te has quemado muy rápido (Burn Rate Alto), el cerebro lo olvida más rápido (sube el lambda)
    penalizacion_burn = min(burn_rate * 0.005, 0.05)
    
    # Cicatriz y suelo
    puntos_fatiga += max(min(total * 0.2, 25.0), pico_previo * 0.15)
    
    # SCORE FINAL Y LAMBDA
    escuchas_recientes = sum(1 for f in fechas_validas if (fecha_objetivo - f).days <= 14)
    score = (escuchas_recientes * 0.6) - (puntos_fatiga * 0.4)
    
    if score > 0: lambda_final = min(0.15, lambda_base + penalizacion_burn + score * 0.01)
    else: lambda_final = max(0.01, lambda_base + penalizacion_burn + score * 0.005)
    
    nuevo_pico = max(pico_previo, puntos_fatiga)

    return round(puntos_fatiga, 2), round(lambda_final, 4), round(nuevo_pico, 2), round(burn_rate, 2)
