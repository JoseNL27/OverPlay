import sqlite3
from datetime import datetime
import math
import os
from core_matematico import calcular_metricas_core
from db import obtener_conexion


def calcular_fatiga_diaria():
    print("🚀 Iniciando Motor Overplay Diario...")
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    # --- 🎛️ CARGAR PREFERENCIAS DE CADA USUARIO ---
    try:
        cursor.execute("SELECT user_id FROM perfiles_usuario")
        usuarios = cursor.fetchall()
    except sqlite3.OperationalError as e:
        print(f"❌ Error al leer la tabla usuarios: {e}")
        conexion.close()
        return
    
    if not usuarios:
        print("⚠️ No hay usuarios registrados en la base de datos para escanear.")
        conexion.close()
        return
    
    for usuario in usuarios:
        user_id = usuario['user_id']
        cursor.execute("SELECT sensibilidad_fatiga, tiempo_recuperacion, estilo_escucha FROM perfiles_usuario WHERE user_id = ?", (user_id,))
        config_usuario = cursor.fetchone()
    
    # Si por algún casual no estuviera, le pasamos un diccionario de emergencia
    config_usuario = dict(config_usuario) if config_usuario else {
        'sensibilidad_fatiga': 1.0,
        'tiempo_recuperacion': 1.0,
        'estilo_escucha': 'Normal'
    }

    ahora = datetime.now()
    fecha_hoy_str = ahora.strftime("%Y-%m-%d")

    # 1. Traer todos los metadatos de golpe (Nuevas tablas V2)
    cursor.execute("SELECT track_id, año_lanzamiento, popularidad, artista, colaboradores, generos FROM canciones")
    catalogo = {r['track_id']: dict(r) for r in cursor.fetchall()}
    
    cursor.execute("SELECT track_id, pico_historico, fecha_pico FROM fatiga_actual")
    picos_previos = {r['track_id']: dict(r) for r in cursor.fetchall()}

    # 2. Agrupar historial y calcular volumen de artistas en la RAM
    cursor.execute("SELECT track_id, played_at FROM reproducciones")
    historial = {}
    radiacion_artista = {}
    
    for r in cursor.fetchall():
        tid = r['track_id']
        try:
            fecha = datetime.strptime(r['played_at'].replace('T', ' ')[:19], "%Y-%m-%d %H:%M:%S")
            if tid not in historial: historial[tid] = []
            historial[tid].append(fecha)
            
            # Radiación
            meta = catalogo.get(tid, {})
            dias = (ahora - fecha).days
            peso = math.exp(-0.02 * dias)
            
            if meta.get('colaboradores'):
                colabs = [c.strip() for c in meta['colaboradores'].split(',') if c.strip()]
                for i, c in enumerate(colabs):
                    radiacion_artista[c] = radiacion_artista.get(c, 0) + (peso * (1.0 if i == 0 else 0.6))
            else:
                art = meta.get('artista') or "Desconocido"
                radiacion_artista[art] = radiacion_artista.get(art, 0) + peso
        except: continue

    # 3. PROCESAMIENTO (Llamada al core)
    datos_actualizar = []
    snapshot = []
    
    for tid, fechas in historial.items():
        meta = catalogo.get(tid, {})
        viejo_pico = picos_previos.get(tid, {})
        
        meta_empaquetada = {
            'año': meta.get('año_lanzamiento'),
            'pop': meta.get('popularidad', 50),
            'generos': meta.get('generos', ''),
            'pico_previo': viejo_pico.get('pico_historico', 0.0)
        }
        
        artista_prin = meta.get('artista') or "Desconocido"
        volumen = radiacion_artista.get(artista_prin, 0)
        
       # MAGIA DRY: Llamamos a la función central V6 pasándole tu configuración
        resultados = calcular_metricas_core(fechas, ahora, meta_empaquetada, volumen, config_usuario)
        
        fatiga = resultados["fatiga"]
        lam = resultados["lambda"]
        pico_nuevo = resultados["pico"]
        overrate = resultados["OverRate"]
        etiquetas_str = ",".join(resultados["etiquetas"]) 
        
        nueva_fecha_pico = fecha_hoy_str if fatiga >= pico_nuevo else viejo_pico.get('fecha_pico')
        
        # 🚀 FIX: Ordenamos la tupla EXACTAMENTE como lo espera la nueva tabla (track_id va el primero)
        datos_actualizar.append((
            tid, 
            lam, 
            fatiga, 
            pico_nuevo, 
            nueva_fecha_pico, 
            overrate, 
            etiquetas_str, 
            ahora.strftime("%Y-%m-%d %H:%M:%S")
        ))
        
        if fatiga > 0.5:
            snapshot.append((fecha_hoy_str, tid, fatiga))

    # 4. INYECCIÓN MASIVA EN LA BASE DE DATOS (V6 Edition)
    cursor.executemany('''
        INSERT OR REPLACE INTO fatiga_actual 
        (track_id, lambda, puntos_fatiga, pico_historico, fecha_pico, overrate, etiquetas, ultima_actualizacion)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', datos_actualizar)
    
    # Guardamos los snapshots del historial
    if snapshot:
        cursor.executemany('''
            INSERT OR IGNORE INTO historial_diario (fecha, track_id, puntos_fatiga)
            VALUES (?, ?, ?)
        ''', snapshot)

    conexion.commit()
    conexion.close()
    print(f"✅ Rutina diaria terminada. {len(datos_actualizar)} tracks procesados.")

if __name__ == "__main__":
    calcular_fatiga_diaria()