import spotipy
from spotipy.oauth2 import SpotifyOAuth
import sqlite3
import time
import os
import re
from datetime import datetime
from calcular_fatiga import calcular_fatiga_diaria
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI

def configurar_bd():
    ruta_bd = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'historial.db')
    conexion = sqlite3.connect(ruta_bd, timeout=30.0) 
    conexion.execute("PRAGMA journal_mode=WAL;")
    cursor = conexion.cursor()
    # Tabla de Usuarios (NUEVA)
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                user_id TEXT PRIMARY KEY,
                nombre TEXT,
                refresh_token TEXT,
                rol TEXT DEFAULT 'beta_tester',
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Catálogo Global (No lleva user_id porque las canciones son de todos)
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS canciones (
                track_id TEXT PRIMARY KEY,
                nombre TEXT,
                artista TEXT,
                colaboradores TEXT,
                imagen_url TEXT,
                artista_img TEXT,
                año_lanzamiento INTEGER,
                popularidad INTEGER,
                generos TEXT
            )
        ''')

        # Tabla de Reproducciones (Multi-tenant)
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS reproducciones (
                user_id TEXT,
                track_id TEXT,
                played_at TIMESTAMP,
                PRIMARY KEY (user_id, track_id, played_at)
            )
        ''')

        # Tabla de Fatiga / O.V.R. (Multi-tenant)
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS fatiga_actual (
                user_id TEXT,
                track_id TEXT,
                lambda REAL DEFAULT 0,
                puntos_fatiga REAL DEFAULT 0,
                overrate REAL DEFAULT 0,
                pico_historico REAL DEFAULT 0,
                etiquetas TEXT,
                fecha_pico TIMESTAMP,
                ultima_actualizacion TIMESTAMP,
                PRIMARY KEY (user_id, track_id)
            )
        ''')
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS configuracion_usuario (
                id TEXT,
                factor_sensibilidad REAL DEFAULT 0,
                tolerancia_atracon REAL DEFAULT 0,
                tasa_amnesia REAL DEFAULT 0,
                año_nostalgia REAL DEFAULT 0,
                generos_rapidos TEXT,
                generos_refugio TEXT,
                PRIMARY KEY (id)
            )
        ''')

    conexion.commit()
    return conexion

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="user-read-recently-played playlist-read-private", 
    open_browser=False,
    cache_path="spotify_token.cache" 
))

def capturar_historial(conexion):
    try:
        results = sp.current_user_recently_played(limit=50)
        cursor = conexion.cursor()
        nuevas_canciones = 0
        artistas_consultados = {}

        for item in results['items']:
            track = item.get('track')
            if not track or track.get('name', "Desconocido") == "Desconocido" or not track.get('artists'): 
                continue

            # --- LIMPIEZA DE METADATOS Y ARTISTAS (V3 Anti-Troleo Spotify) ---
            track_name_limpio = re.sub(r'(?i)(\s*\(with.*?\)|\s*\(feat\..*?\)|\s*\[feat\..*?\]| - remaster.*)', '', track['name']).strip()
            
            artistas_spotify = [a['name'] for a in track['artists']]
            artista_final = artistas_spotify[0] # El que escupe Spotify por defecto esta vez

            # 1. 🔍 RESOLUCIÓN DE CONFLICTOS (Caso Quevedo vs Saiko):
            # Si ya tenemos esta canción guardada, comprobamos quién es el "dueño" real en nuestra DB.
            cursor.execute("SELECT artista FROM canciones WHERE LOWER(nombre) = LOWER(?)", (track_name_limpio,))
            filas = cursor.fetchall()
            for fila in filas:
                artista_guardado = fila[0]
                # Si el artista que teníamos guardado está entre los de esta escucha, le devolvemos la corona
                if artista_guardado in artistas_spotify:
                    artista_final = artista_guardado
                    break

            # 2. ✂️ EXTIRPAR AL ARTISTA PRINCIPAL DE LOS COLABORADORES
            colabs_reales = [a for a in artistas_spotify if a != artista_final]
            colaboradores_str = ", ".join(colabs_reales)

            # Ya podemos generar un ID inmutable
            track_id = f"{track_name_limpio} - {artista_final}"
            played_at = item.get('played_at')
            print(track_id)

            # --- GUARDAR REPRODUCCIÓN ---
            cursor.execute('''
                INSERT OR IGNORE INTO reproducciones (played_at, track_id)
                VALUES (?, ?)
            ''', (played_at, track_id))
            
            if cursor.rowcount == 1:
                nuevas_canciones += 1

            # --- ENRIQUECER CATÁLOGO CENTRAL ---
            # 🚀 AÑADIMOS artista_img a la comprobación
            cursor.execute("SELECT año_lanzamiento, generos, artista_img FROM canciones WHERE track_id = ?", (track_id,))
            fila_meta = cursor.fetchone()

            # 🚀 Si falta el año, el género, O LA IMAGEN, forzamos a que llame a Spotify
            if not fila_meta or not fila_meta[0] or not fila_meta[1] or not fila_meta[2]:
                fecha_salida = track.get('album', {}).get('release_date', '')
                año = int(fecha_salida[:4]) if len(fecha_salida) >= 4 else None
                artist_id = track['artists'][0].get('id')
                
                # 1. 🖼️ Foto de la canción (Álbum)
                img_url = track['album']['images'][0]['url'] if track.get('album') and track['album'].get('images') else ""
                
                # 2. 🧬 Géneros y Foto del Artista
                generos_str = ""
                artista_img = ""
                
                if artist_id:
                    # Guardamos un diccionario en caché con la foto y el género para no saturar a Spotify
                    if artist_id not in artistas_consultados:
                        try:
                            datos_artista = sp.artist(artist_id)
                            gen_str = ", ".join(datos_artista.get('genres', []))
                            img_art = datos_artista['images'][0]['url'] if datos_artista.get('images') else ""
                            artistas_consultados[artist_id] = {"gen": gen_str, "img": img_art}
                        except Exception as e:
                            print(f"Error sacando datos del artista {artista_final}: {e}")
                            artistas_consultados[artist_id] = {"gen": "", "img": ""}
                    
                    generos_str = artistas_consultados[artist_id]["gen"]
                    artista_img = artistas_consultados[artist_id]["img"]

                # 3. 💾 Guardamos TODO (Añadimos imagen_url y artista_img)
                cursor.execute('''
                    INSERT OR REPLACE INTO canciones 
                    (track_id, nombre, artista, colaboradores, popularidad, año_lanzamiento, generos, imagen_url, artista_img)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (track_id, track_name_limpio, artista_final, colaboradores_str, track.get('popularity', 50), año, generos_str, img_url, artista_img))
                
        conexion.commit()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Captura completada: {nuevas_canciones} reproducciones nuevas.")

    except Exception as e:
        conexion.rollback()
        print(f"❌ Error durante la captura: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando Monitor Overplay v6.0 (RAW Data)...")
    conexion_bd = configurar_bd()
    ultima_fecha_entrenamiento = None
    
    while True:
        hora_actual = datetime.now()
        capturar_historial(conexion_bd)
        
        print("-> Sincronizando motor matemático...")
        calcular_fatiga_diaria()
        
        fecha_hoy = hora_actual.date()
        if ultima_fecha_entrenamiento != fecha_hoy:
            ultima_fecha_entrenamiento = fecha_hoy
            
        print(f"[{hora_actual.strftime('%H:%M:%S')}] Ciclo completo. Durmiendo...\n")
        time.sleep(7200)