import sqlite3
import os
from datetime import datetime, timedelta
import math

# Ruta absoluta para no fallar
BASE_DATOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'historial.db')

def viajar_en_el_tiempo():
    print("⏳ Encendiendo la Máquina del Tiempo (Backfilling Histórico)...")
    
    conexion = sqlite3.connect(BASE_DATOS)
    conexion.row_factory = sqlite3.Row
    # Activar WAL para que no interfiera con tu main.py si está corriendo
    conexion.execute("PRAGMA journal_mode=WAL;") 
    cursor = conexion.cursor()

    # 1. CARGAR TODO A LA RAM PARA MÁXIMA VELOCIDAD
    print("📦 Cargando historial en memoria...")
    cursor.execute("SELECT track_id, played_at FROM reproducciones ORDER BY played_at ASC")
    reproducciones = cursor.fetchall()

    if not reproducciones:
        print("❌ No hay reproducciones en la base de datos.")
        return

    cursor.execute("SELECT track_id, año_lanzamiento FROM metadatos_cache WHERE año_lanzamiento IS NOT NULL")
    mapa_años = {row['track_id']: row['año_lanzamiento'] for row in cursor.fetchall()}

    cursor.execute("SELECT sensibilidad_base FROM perfil_usuario WHERE user_id = 1")
    user_config = cursor.fetchone()
    FACTOR_SENSIBILIDAD = user_config['sensibilidad_base'] if user_config else 1.0

    # 2. ORGANIZAR DATOS
    # historial = { 'track_id': [fecha1, fecha2, ...] }
    historial = {}
    for r in reproducciones:
        tid = r['track_id']
        if tid not in historial:
            historial[tid] = []
        try:
            # Parseamos la fecha (ignorando si hay milisegundos raros)
            dt = datetime.strptime(r['played_at'].replace('T', ' ')[:19], "%Y-%m-%d %H:%M:%S")
            historial[tid].append(dt)
        except: pass

    # 3. DEFINIR EL BUCLE TEMPORAL
    primera_fecha = datetime.strptime(reproducciones[0]['played_at'].replace('T', ' ')[:19], "%Y-%m-%d %H:%M:%S").date()
    fecha_hoy = datetime.now().date()
    dias_totales = (fecha_hoy - primera_fecha).days + 1

    print(f"🚀 Viajando desde {primera_fecha} hasta {fecha_hoy} ({dias_totales} días detectados)...")

    # Limpiamos las tablas temporales por si ejecutamos esto varias veces
    cursor.execute("DELETE FROM historial_fatiga_diario")
    cursor.execute("DELETE FROM snapshots_diarios")
    conexion.commit()

    # 4. EL MOTOR DEL TIEMPO (Iterar día a día)
    datos_historial_diario = []
    datos_snapshots = []

    dia_actual = primera_fecha
    año_actual = datetime.now().year

    while dia_actual <= fecha_hoy:
        dt_actual = datetime.combine(dia_actual, datetime.max.time()) # Final de ese día
        fecha_str = dia_actual.isoformat()
        
        puntos_dia = []
        
        for track_id, fechas_escucha in historial.items():
            # Solo miramos las escuchas que ocurrieron ANTES o DURANTE este día histórico
            fechas_validas = [f for f in fechas_escucha if f <= dt_actual]
            if not fechas_validas:
                continue # Esta canción aún no se había descubierto en este día

            # Matemáticas de fatiga (Versión optimizada para Backfill)
            artista = track_id.split(' - ')[1] if ' - ' in track_id else "Desconocido"
            
            # Factor edad
            año_cancion = mapa_años.get(track_id)
            penalizacion_edad = max(0, año_actual - año_cancion) * 0.2 if año_cancion else 0.0

            puntos_fatiga = 0.0
            fecha_anterior = None

            for f in fechas_validas:
                dias_pasados = (dt_actual - f).days
                daño_base = (5.0 + penalizacion_edad + (math.log(len(fechas_validas) + 1) * 2.0)) * FACTOR_SENSIBILIDAD
                
                # Densidad (Binge listening)
                if fecha_anterior:
                    minutos_diff = (f - fecha_anterior).total_seconds() / 60.0
                    if minutos_diff < 120:
                        daño_base *= (1.0 + (120 - minutos_diff) / 120)

                # Curva de olvido hasta el día simulado
                puntos_fatiga += daño_base * math.exp(-0.05 * dias_pasados)
                fecha_anterior = f

            # Cicatriz
            puntos_fatiga += min(len(fechas_validas) * 0.2, 25.0)

            if puntos_fatiga > 0.5:
                datos_historial_diario.append((fecha_str, track_id, round(puntos_fatiga, 2)))
                puntos_dia.append(puntos_fatiga)

        # Generar Snapshot global del día
        if puntos_dia:
            media = round(sum(puntos_dia) / len(puntos_dia), 2)
            datos_snapshots.append((fecha_str, media, len(puntos_dia)))

        # Avanzamos un día en el tiempo
        dia_actual += timedelta(days=1)
        
        # Para que veas que está trabajando y no se ha colgado
        if (dia_actual - primera_fecha).days % 30 == 0:
            print(f"   -> Procesado hasta el mes: {dia_actual.strftime('%Y-%m')}")

    # 5. GUARDAR TODO EL HISTÓRICO DE GOLPE
    print("💾 Guardando millones de datos temporales en la base de datos...")
    cursor.executemany('''
        INSERT INTO historial_fatiga_diario (fecha, track_id, puntos_fatiga)
        VALUES (?, ?, ?)
    ''', datos_historial_diario)

    cursor.executemany('''
        INSERT INTO snapshots_diarios (fecha, fatiga_media, canciones_activas)
        VALUES (?, ?, ?)
    ''', datos_snapshots)

    conexion.commit()
    conexion.close()
    
    print(f"🎉 ¡VIAJE COMPLETADO! Se han generado {len(datos_historial_diario)} puntos de datos históricos.")

if __name__ == "__main__":
    viajar_en_el_tiempo()