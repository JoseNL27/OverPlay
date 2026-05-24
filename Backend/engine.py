from datetime import datetime

def procesar_fatiga_canciones(matriz_canciones):
    """
    Analiza las tendencias de las canciones y calcula su overrate inicial (OVR).
    Devuelve un diccionario listo para ser insertado en fatiga_actual.
    """
    resultados_canciones = {}
    P_FUERA = 25

    for track_id, posiciones in matriz_canciones.items():
        p_short = posiciones.get('short') or P_FUERA
        p_medium = posiciones.get('medium') or P_FUERA
        p_long = posiciones.get('long') or P_FUERA

        # FÓRMULA: Tendencia = P_short - P_long
        tendencia = p_short - p_long

        # ☢️ CASO A: Temazo histórico quemado (Estaba en el Top Long y ya no está en Short)
        if tendencia >= 15 and p_long <= 5:
            ovr_inicial = 80.0  # Fatiga altísima inicial
            etiqueta = "Quenada Histórica"

        # 📉 CASO B: Obsesión en bucle (Puesto alto en Short, no existía en Long)
        elif tendencia <= -15 and p_short <= 5:
            ovr_inicial = 20.0  # OVR inicial bajo, pero con predisposición a subir rápido
            etiqueta = "Bucle Reciente"

        # 📈 CASO C: Clásico personal (Estable en los tres rangos)
        elif abs(tendencia) <= 12 and p_long < P_FUERA:
            ovr_inicial = 5.0   # Casi inmune a la fatiga inicial
            etiqueta = "Inmune Inicial"
            
        else:
            # Canciones de rotación normal o término medio
            ovr_inicial = 35.0
            etiqueta = "Rotación Estándar"

        resultados_canciones[track_id] = {
            "overrate": ovr_inicial,
            "etiqueta": etiqueta
        }

    return resultados_canciones

def mapear_top_tracks_cold_start(sp):
    rangos = ['short_term', 'medium_term', 'long_term']
    matriz_canciones = {} # Estructura: { "Nombre Artista": { "short": X, "medium": Y, "long": Z } }

    for rango in rangos:
        try:
            # Pedimos los 20 tracks top en este rango específico
            results = sp.current_user_top_tracks(time_range=rango, limit=20)
            
            for index, item in enumerate(results.get('items', [])):
                track_name = item.get('name')
                posicion = index + 1 # Puesto 1 al 20
                
                if track_name not in matriz_canciones:
                    matriz_canciones[track_name] = {'short': None, 'medium': None, 'long': None}
                
                # Mapeamos de forma limpia según el rango
                if rango == 'short_term':
                    matriz_canciones[track_name]['short'] = posicion
                elif rango == 'medium_term':
                    matriz_canciones[track_name]['medium'] = posicion
                elif rango == 'long_term':
                    matriz_canciones[track_name]['long'] = posicion
                    
        except Exception as e:
            print(f"⚠️ Error capturando rango {rango}: {e}")
            
    return matriz_canciones


def mapear_top_artistas_cold_start(sp):
    """
    Escanea los tres rangos de tiempo de Spotify para cruzar las posiciones
    y devolver la matriz de comportamiento del usuario.
    """
    rangos = ['short_term', 'medium_term', 'long_term']
    matriz_artistas = {} # Estructura: { "Nombre Artista": { "short": X, "medium": Y, "long": Z } }

    for rango in rangos:
        try:
            # Pedimos los 20 artistas top en este rango específico
            results = sp.current_user_top_artists(time_range=rango, limit=20)
            
            for index, item in enumerate(results.get('items', [])):
                nombre_artista = item.get('name')
                posicion = index + 1 # Puesto 1 al 20
                
                if nombre_artista not in matriz_artistas:
                    matriz_artistas[nombre_artista] = {'short': None, 'medium': None, 'long': None}
                
                # Mapeamos de forma limpia según el rango
                if rango == 'short_term':
                    matriz_artistas[nombre_artista]['short'] = posicion
                elif rango == 'medium_term':
                    matriz_artistas[nombre_artista]['medium'] = posicion
                elif rango == 'long_term':
                    matriz_artistas[nombre_artista]['long'] = posicion
                    
        except Exception as e:
            print(f"⚠️ Error capturando rango {rango}: {e}")
            
    return matriz_artistas

def procesar_cold_start(matriz_artistas):
    """
    Toma las posiciones de Spotify y aplica el A.I.A.
    Devuelve los OVR iniciales por artista y el perfil global del tester.
    """
    resultados_artistas = {}
    
    # Contadores para definir el perfil psicológico del usuario
    perfil_global = {"anclas": 0, "obsesiones": 0, "fatigados": 0}

    # Constante para cuando un artista NO aparece en un top (fuera del top 20)
    P_FUERA = 25 

    for artista, posiciones in matriz_artistas.items():
        # Extraemos posiciones (si es None, le damos el valor de penalización P_FUERA)
        p_short = posiciones.get('short') or P_FUERA
        p_medium = posiciones.get('medium') or P_FUERA
        p_long = posiciones.get('long') or P_FUERA

        # 🧮 LA FÓRMULA MAESTRA
        tendencia = p_short - p_long

        # ----------------------------------------------------
        # ☢️ CASO 3: Fatiga Sistémica (Tendencia muy positiva)
        # ----------------------------------------------------
        if tendencia >= 15 and p_long <= 5:
            clase = "Fatiga Sistémica"
            ovr_base = 75.0  # Empieza quemadísimo
            perfil_global["fatigados"] += 1

        # ----------------------------------------------------
        # 📉 CASO 2: Obsesión Reciente (Tendencia muy negativa)
        # ----------------------------------------------------
        elif tendencia <= -15 and p_short <= 5:
            clase = "Obsesión Reciente"
            ovr_base = 15.0  # OVR inicial bajo, pero el core_matematico lo hará subir rápido
            perfil_global["obsesiones"] += 1

        # ----------------------------------------------------
        # 📈 CASO 1: Artista Ancla (Estable en el tiempo)
        # ----------------------------------------------------
        elif abs(tendencia) <= 12 and p_long < P_FUERA:
            clase = "Artista Ancla"
            ovr_base = 10.0  # Inmunidad sutil
            perfil_global["anclas"] += 1
            
        else:
            # Artistas transitorios o de relleno
            clase = "Transitorio"
            ovr_base = 30.0

        # Guardamos el dictamen final para este artista
        resultados_artistas[artista] = {
            "clasificacion": clase,
            "tendencia": tendencia,
            "ovr_inicial": ovr_base
        }

    # Lógica de inferencia global (¿Es un quemador o un fiel?)
    estilo_escucha = "Fiel"
    sensibilidad_fatiga = 1.0 # Multiplicador estándar
    
    if perfil_global["fatigados"] > perfil_global["anclas"]:
        estilo_escucha = "Intenso"
        sensibilidad_fatiga = 1.4 # Se quema un 40% más rápido de lo normal

    elif perfil_global["anclas"] > perfil_global["fatigados"]:
        estilo_escucha = "Fiel"
        sensibilidad_fatiga = 0.8 # Tiene un 20% más de tolerancia a la repetición

    return resultados_artistas, estilo_escucha, sensibilidad_fatiga