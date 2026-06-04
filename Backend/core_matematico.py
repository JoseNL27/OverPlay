import math
from collections import Counter
from datetime import timedelta

def calcular_metricas_core(fechas_reproduccion, fecha_objetivo, meta_cancion, volumen_artista, config_usuario):
    """
    =========================================================
    OVERPLAY V6 RAW: THE EMOTION ENGINE
    =========================================================
    Pilar 1: Volatilidad (ADN y Popularidad)
    Pilar 2: Fases de Vida (Luna de Miel vs Saturación)
    Pilar 3: Hábitat Natural (Contexto Horario)
    Pilar 4: Himnos vs Cicatrices (Resiliencia)
    Métrica Estrella: OverRate 🔥
    """
    fechas_validas = sorted([f for f in fechas_reproduccion if f <= fecha_objetivo])
    if not fechas_validas:
        return {"fatiga": 0.0, "lambda": 0.05, "pico": 0.0, "OverRate": 0.0, "etiquetas": []}
        
    total_repros = len(fechas_validas)
    dias_existencia = max(1, (fecha_objetivo - fechas_validas[0]).days)
    
    # ---------------------------------------------------------
    # 🧬 PILAR 1: EL ADN DE LA CANCIÓN (Volatilidad y Géneros)
    # ---------------------------------------------------------
    pop = meta_cancion.get('pop') or 50
    
    # Volatilidad: Música viral (Pop 90+) sube rápido y se olvida rápido. Nicho (Pop 30) es resistente.
    volatilidad = pop / 50.0 
    
   # generos_cancion = str(meta_cancion.get('generos') or '').lower()
   # gen_rapidos = [g.strip().lower() for g in config_usuario.get('generos_rapidos', '').split(',')]
   # gen_refugio = [g.strip().lower() for g in config_usuario.get('generos_refugio', '').split(',')]
    
    modificador_genero = 1.0
    #if any(g in generos_cancion for g in gen_rapidos if g):
   #     modificador_genero = 1.20 # +20% de daño base por ser consumo rápido
    #elif any(g in generos_cancion for g in gen_refugio if g):
    #    modificador_genero = 0.80 # -20% de daño base, es tu refugio

    # Tasa de amnesia base ajustada por volatilidad y el slider del usuario
    tasa_amnesia_usr = config_usuario.get('tiempo_recuperacion', 1.0)
    lambda_base = 0.03 * volatilidad * tasa_amnesia_usr

    # ---------------------------------------------------------
    # 🕒 PILAR 3: EL HÁBITAT NATURAL (Contexto)
    # ---------------------------------------------------------
    # Dividimos el día en 4 franjas (0: Madrugada, 1: Mañana, 2: Tarde, 3: Noche)
    franjas = [f.hour // 6 for f in fechas_validas] 
    habitat_natural = Counter(franjas).most_common(1)[0][0] if franjas else -1

    # ---------------------------------------------------------
    # ☢️ PREPARACIÓN DE VARIABLES GLOBALES
    # ---------------------------------------------------------
    puntos_fatiga = 0.0
    fecha_anterior = None
    repros_historicas = 0
    dias_consecutivos = 0
    
    sensibilidad_usr = config_usuario.get('sensibilidad_fatiga', 1.0)
    tolerancia_atracon = config_usuario.get('tolerancia_atracon', 1.0)

    # Radiación del Artista y Colaboradores. 
    # Si llevas 2 horas escuchando a Bad Bunny, cualquier tema suyo entra con daño extra.
    bonus_radiacion = 1.0 + (volumen_artista * 0.03)

    # ---------------------------------------------------------
    # 🔄 EL BUCLE CRONOLÓGICO (Simulación de la Realidad)
    # ---------------------------------------------------------
    for f in fechas_validas:
        repros_historicas += 1
        
        # 1. Aplicar Decaimiento Fisiológico (Enfriamiento natural)
        if fecha_anterior:
            dias_hueco = (f - fecha_anterior).total_seconds() / 86400.0
            puntos_fatiga *= math.exp(-lambda_base * dias_hueco)
            
            # Chequeo de Hábito (Días consecutivos)
            if 0 < dias_hueco <= 1.5 and f.date() != fecha_anterior.date():
                dias_consecutivos += 1
            elif dias_hueco > 1.5:
                dias_consecutivos = 0 # Se rompe la racha tóxica
        
        # 2. Calcular Daño Base del impacto (Depende del ADN y tu sensibilidad)
        daño_impacto = 5.0 * math.sqrt(max(0.1, volatilidad)) * modificador_genero * sensibilidad_usr
        
        # 3. PILAR 2: FASES DE VIDA (Densidad y Atracones)
        multiplicador_atracon = 1.0
        
        if repros_historicas <= 10:
            # LUNA DE MIEL: Cero penalización por atracón. Te la estás gozando.
            multiplicador_atracon = 1.0
        else:
            # SATURACIÓN: Ya te la sabes. El atracón duele.
            if fecha_anterior:
                horas_diff = (f - fecha_anterior).total_seconds() / 3600.0
                if horas_diff < 2:
                    multiplicador_atracon = 2.0 / max(0.1, tolerancia_atracon)
                elif horas_diff < 6:
                    multiplicador_atracon = 1.3 / max(0.1, tolerancia_atracon)
            
            # HÁBITO TÓXICO: Si llevas más de 5 días seguidos escuchándola, te fatiga un 20% extra.
            if dias_consecutivos >= 5:
                multiplicador_atracon *= 1.2
                
        # 4. Impacto del Contexto Horario
        franja_actual = f.hour // 6
        if franja_actual != habitat_natural:
            # Escucharla fuera de su hábitat genera "fricción" cognitiva.
            daño_impacto *= 1.15
            
        # Sumar el impacto real a la batería mental
        puntos_fatiga += daño_impacto * multiplicador_atracon * bonus_radiacion
        fecha_anterior = f

    # Enfriamiento final hasta el día de la consulta (fecha_objetivo)
    if fecha_anterior:
        dias_finales = (fecha_objetivo - fecha_anterior).total_seconds() / 86400.0
        puntos_fatiga *= math.exp(-lambda_base * dias_finales)

    # ---------------------------------------------------------
    # 🛡️ PILAR 4: HIMNOS VS CICATRICES (El final del viaje)
    # ---------------------------------------------------------
    es_himno = dias_existencia > 180 and total_repros > 30 and puntos_fatiga < 50
    es_quemada = dias_existencia < 30 and total_repros > 50
    
    suelo_fatiga = 0.0
    if es_quemada:
        # CICATRIZ: La quemaste demasiado rápido. Nunca volverá a estar a 0.
        suelo_fatiga = total_repros * 0.4 
    
    if es_himno:
        # ESCUDO: Es un clásico para ti. Resiste la fatiga y se olvida el daño rapidísimo.
        puntos_fatiga *= 0.6
        lambda_base *= 1.5 

    # Aplicamos el suelo (Cicatriz) si lo hay
    puntos_fatiga = max(puntos_fatiga, suelo_fatiga)
    nuevo_pico = max(meta_cancion.get('pico_previo', 0.0), puntos_fatiga)

    # ---------------------------------------------------------
    # 📈 OVERRATE (La Métrica Definitiva)
    # ---------------------------------------------------------
    # Combina tu nivel de fatiga cerebral actual con tu obsesión reciente (últimos 7 días).
    # Es un número que puede pasar de 100 si estás reventando la canción.
    escuchas_7d = sum(1 for f in fechas_validas if (fecha_objetivo - f).days <= 7)
    
    overrate_bruto = (puntos_fatiga * 0.4) + (escuchas_7d * 8 * volatilidad)
    OverRate = round(overrate_bruto, 1)

    # ---------------------------------------------------------
    # 🏷️ ETIQUETAS PSICOLÓGICAS (Para el Frontend)
    # ---------------------------------------------------------
    etiquetas = []
    if es_himno: etiquetas.append("Himno Atemporal 👑")
    elif es_quemada: etiquetas.append("Quemada ☢️")
    
    if total_repros <= 10: etiquetas.append("Luna de Miel 💖")
    elif dias_consecutivos >= 5: etiquetas.append("Hábito Tóxico 🐍")
    
    if OverRate > 100: etiquetas.append("OverRated 🔥")

    return {
        "fatiga": round(puntos_fatiga, 2),
        "lambda": round(lambda_base, 4),
        "pico": round(nuevo_pico, 2),
        "OverRate": OverRate,
        "etiquetas": etiquetas
    }