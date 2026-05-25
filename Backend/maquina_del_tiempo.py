import sqlite3
import os
import math
from datetime import datetime, timedelta
from core_matematico import calcular_metricas_core

# --- CONFIGURACIÓN ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'historial.db')

def ejecutar_maquina_tiempo():
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    print("⏳ Iniciando viaje temporal... Cargando configuración de usuario...")
    
    # 1. Cargamos TU configuración inyectada
    cursor.execute("SELECT * FROM configuracion_usuario WHERE id = 1")
    config_usuario = dict(cursor.fetchone())

    # 2. Limpiamos el historial antiguo para no duplicar
    print("🧹 Purgando historial diario antiguo...")
    cursor.execute("DELETE FROM historial_diario")
    
    # 3. Cargamos TODAS las reproducciones de una vez (RAM Optimization)
    print("📦 Cargando 2 millones de registros en memoria (esto puede tardar un poco)...")
    cursor.execute("SELECT track_id, played_at FROM reproducciones ORDER BY played_at ASC")
    todas_repros = cursor.fetchall()

    # 4. Cargamos catálogo de metadatos
    cursor.execute("SELECT * FROM canciones")
    catalogo = {r['track_id']: dict(r) for r in cursor.fetchall()}

    # 5. Estructuramos los datos por track_id
    historial_por_track = {}
    print("🧠 Procesando líneas temporales...")
    for r in todas_repros:
        tid = r['track_id']
        fecha = datetime.strptime(r['played_at'].replace('T', ' ')[:19], "%Y-%m-%d %H:%M:%S")
        if tid not in historial_por_track: historial_por_track[tid] = []
        historial_por_track[tid].append(fecha)

    # Determinamos el rango de días del viaje
    fecha_min = datetime.strptime(todas_repros[0]['played_at'][:10], "%Y-%m-%d")
    fecha_max = datetime.now()
    total_dias = (fecha_max - fecha_min).days

    print(f"🚀 Viajando {total_dias} días por el tiempo...")

   # 6. EL VIAJE: Recalculamos día por día con Time-Skip Inteligente
    batch_snapshot = []
    
    for i, (tid, fechas) in enumerate(historial_por_track.items()):
        meta = catalogo.get(tid, {})
        meta_empaquetada = {
            'año': meta.get('año_lanzamiento'),
            'pop': meta.get('popularidad', 50),
            'generos': meta.get('generos', ''),
            'pico_previo': 0.0
        }

        dias_activos_lista = sorted(list(set([f.date() for f in fechas])))
        set_dias_activos = set(dias_activos_lista)
        
        if not dias_activos_lista:
            continue
            
        dia_actual = dias_activos_lista[0]
        fecha_fin = datetime.now().date()
        
        pico_local = 0.0
        ult_fatiga = 100.0 # Empezamos alto para que procese el primer día sí o sí
        
        while dia_actual <= fecha_fin:
            # 🚀 TIME-SKIP LOGIC: Si hoy no la escuchaste y la fatiga ya es casi 0, saltamos al futuro
            if dia_actual not in set_dias_activos and ult_fatiga <= 0.1:
                futuros = [d for d in dias_activos_lista if d > dia_actual]
                if futuros:
                    dia_actual = futuros[0] # Saltamos directo al próximo día activo
                else:
                    break # Ya no hay más escuchas y está a 0. Terminamos con este track.
                continue # Reiniciamos el bucle en la nueva fecha

            # Calculamos la fatiga de este día exacto (haya sonado o no)
            fecha_dt = datetime.combine(dia_actual, datetime.max.time())
            res = calcular_metricas_core(fechas, fecha_dt, meta_empaquetada, 1.0, config_usuario)
            
            fatiga = res['fatiga']
            pico_local = max(pico_local, fatiga)
            meta_empaquetada['pico_previo'] = pico_local
            
            # Guardamos la curva de caída en la DB
            if fatiga > 0.1:
                batch_snapshot.append((dia_actual.strftime("%Y-%m-%d"), tid, fatiga))
                
            ult_fatiga = fatiga
            dia_actual += timedelta(days=1)

        if i % 100 == 0:
            print(f"  [Progreso] {i}/{len(historial_por_track)} canciones procesadas...")
            if len(batch_snapshot) > 5000:
                cursor.executemany("INSERT INTO historial_diario (fecha, track_id, puntos_fatiga) VALUES (?, ?, ?)", batch_snapshot)
                batch_snapshot = []
                conexion.commit()
    # Último volcado
    if batch_snapshot:
        cursor.executemany("INSERT INTO historial_diario (fecha, track_id, puntos_fatiga) VALUES (?, ?, ?)", batch_snapshot)
    
    conexion.commit()
    conexion.close()
    print("🏁 Viaje completado. El historial ha sido reescrito con éxito.")

if __name__ == "__main__":
    ejecutar_maquina_tiempo()