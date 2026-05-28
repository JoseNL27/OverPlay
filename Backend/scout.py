import sqlite3
import os
import re
import requests
from datetime import datetime
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
# Importa aquí tus funciones de limpieza de caracteres si las tienes en otro archivo, ej:
# from limpiador import limpiar_nombre_track, separar_artistas

def ejecutar_batida_captura():
    print(f"\n[🦇] [{datetime.now().strftime('%H:%M:%S')}] Iniciando batida de reconocimiento multiusuario...")
    
    # 1. Conectamos a la DB y nos traemos a todos los usuarios registrados
    # Como estás en PC, asegúrate de apuntar bien a la ruta si es necesario
    # 🎯 1. BLINDAJE DE RUTA: Buscamos la DB donde realmente está el script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "historial.db")
    
    print(f"📂 Conectando a la base de datos en: {DB_PATH}") # Para que lo veas con tus propios ojos
    
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row
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
                album TEXT,
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
                user_id TEXT,
                factor_sensibilidad REAL DEFAULT 0,
                tolerancia_atracon REAL DEFAULT 0,
                tasa_amnesia REAL DEFAULT 0,
                año_nostalgia REAL DEFAULT 0,
                generos_rapidos TEXT,
                generos_refugio TEXT,
                sensibilidad_fatiga REAL DEFAULT 1.0,  -- Multiplicador para las canciones
                tiempo_recuperacion INTEGER DEFAULT 30, -- Días medios para el Modo Amnistía
                estilo_escucha TEXT DEFAULT 'Fiel'      -- 'Intenso' o 'Fiel'
            )
        ''')

    conexion.commit()
    return conexion

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def capturar_historial(conexion):
    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT user_id, refresh_token FROM usuarios")
        usuarios = cursor.fetchall()

        for usuario in usuarios:
            user_id = usuario[0]
            refresh_token = usuario[1]
            if not refresh_token:
                continue

            res = requests.post("https://accounts.spotify.com/api/token", data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": SPOTIFY_CLIENT_ID,
                "client_secret": SPOTIFY_CLIENT_SECRET
            })
            tokens = res.json()
            nuevo_token = tokens.get("access_token")
            if not nuevo_token:
                print(f"⚠️ No se pudo refrescar token para {user_id}")
                continue

            sp = spotipy.Spotify(auth=nuevo_token)
            results = sp.current_user_recently_played(limit=50)
            
            nuevas_canciones = 0
            artistas_consultados = {}
            print(f"🔍 Escaneando a {user_id}...")

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
                    INSERT OR IGNORE INTO reproducciones (user_id, played_at, track_id)
                    VALUES (?, ?, ?)
                ''', (user_id, played_at, track_id))
                
                if cursor.rowcount == 1:
                    nuevas_canciones += 1

                # --- ENRIQUECER CATÁLOGO CENTRAL ---
                # 🚀 AÑADIMOS artista_img a la comprobación
                cursor.execute("SELECT año_lanzamiento, generos, artista_img, album FROM canciones WHERE track_id = ?", (track_id,))
                fila_meta = cursor.fetchone()

                # 🚀 Si falta el año, el género, O LA IMAGEN, forzamos a que llame a Spotify
                if not fila_meta or not fila_meta[0] or not fila_meta[1] or not fila_meta[2]:
                    fecha_salida = track.get('album', {}).get('release_date', '')
                    año = int(fecha_salida[:4]) if len(fecha_salida) >= 4 else None
                    artist_id = track['artists'][0].get('id')
                    
                    # 1. 🖼️ Foto de la canción (Álbum) y Nombre del Álbum Limpio 🏆
                    img_url = track['album']['images'][0]['url'] if track.get('album') and track['album'].get('images') else ""
                    
                    # 🎯 CORRECCIÓN AQUÍ: Sacamos el NOMBRE del álbum como texto, no el objeto entero
                    album_name = track.get('album', {}).get('name', 'Single')
                    
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

                    # 3. 💾 GUARDADO BLINDADO (10 columnas = 10 signos '?' = 10 variables)
                    cursor.execute('''
                        INSERT OR REPLACE INTO canciones 
                        (track_id, nombre, artista, colaboradores, album, popularidad, año_lanzamiento, generos, imagen_url, artista_img)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        track_id, 
                        track_name_limpio, 
                        artista_final, 
                        colaboradores_str, 
                        album_name,              # 📂 ¡El nombre del álbum ya entra aquí clavado!
                        track.get('popularity', 50), 
                        año, 
                        generos_str, 
                        img_url, 
                        artista_img
                    ))
                
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Captura completada para {user_id}: {nuevas_canciones} reproducciones nuevas.")
        conexion.commit()

        except Exception as e:
            print(f"❌ Error crítico procesando a {user_id}: {e}")
            continue # Si un usuario falla, que el bucle siga con el siguiente tester

    # Guardamos todos los cambios en la DB tras procesar a todos los usuarios
    conexion.commit()
    conexion.close()
    print("\n[🏁] Batida completa. Base de datos actualizada.")

# Esto te permite probar el script a mano en la consola ejecutando 'python scout.py'
if __name__ == "__main__":
    ejecutar_batida_captura()