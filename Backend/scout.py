#from Backend import prescout
import sqlite3
import os
import requests
import re
from datetime import datetime
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from auth import obtener_sp_para_usuario
from db import obtener_conexion


# Importa aquí tus funciones de limpieza de caracteres si las tienes en otro archivo, ej:
# from limpiador import limpiar_nombre_track, separar_artistas

def ejecutar_batida_captura():
    print(f"\n[🦇] [{datetime.now().strftime('%H:%M:%S')}] Iniciando batida de reconocimiento multiusuario...")
    artistas_consultados = {}
    
    # 1. Conectamos a la DB y nos traemos a todos los usuarios registrados
    # Como estás en PC, asegúrate de apuntar bien a la ruta si es necesario
    # 🎯 1. BLINDAJE DE RUTA: Buscamos la DB donde realmente está el script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
   # print(f"📂 Conectando a la base de datos en: {DB_PATH}") # Para que lo veas con tus propios ojos
    
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    try:
        cursor.execute("SELECT user_id, refresh_token FROM usuarios")
        usuarios = cursor.fetchall()
    except sqlite3.OperationalError as e:
        print(f"❌ Error al leer la tabla usuarios: {e}")
        conexion.close()
        return

    if not usuarios:
        print("⚠️ No hay usuarios registrados en la base de datos para escanear.")
        conexion.close()
        return

    print(f"👥 Se han encontrado {len(usuarios)} usuarios en la DB.")

    # 2. Bucle Maestro: Procesamos a cada usuario de forma independiente
    for usuario in usuarios:
        user_id = usuario['user_id']
        refresh_token = usuario['refresh_token']
        sp = obtener_sp_para_usuario(user_id)
        print(f"\n👤 Escaneando historial reciente de: {user_id}...")

        try:
            # 🔄 Refrescamos el token de Spotify para este usuario concreto
            res = requests.post("https://accounts.spotify.com/api/token", data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": SPOTIFY_CLIENT_ID,
                "client_secret": SPOTIFY_CLIENT_SECRET
            })
            
            tokens = res.json()
            access_token = tokens.get("access_token")
            
            if not access_token:
                print(f"❌ No se pudo refrescar el token para {user_id}. Saltando usuario...")
                continue

            # 🛰️ Petición directa a las últimas 50 reproducciones de este usuario
            headers = {"Authorization": f"Bearer {access_token}"}
            # Usamos el endpoint oficial de recently-played
            sp_res = requests.get("https://api.spotify.com/v1/me/player/recently-played?limit=50", headers=headers)
            
            if sp_res.status_code != 200:
                print(f"❌ Error API Spotify ({sp_res.status_code}) para {user_id}. Saltando...")
                continue
                
            historial = sp_res.json()
            items = historial.get('items', [])
            
            print(f"📥 Capturados {len(items)} temas potenciales para {user_id}.")

            NUEVOS_TEMAS_CONTADOR = 0

            # 3. Tu lógica de limpieza e inyección (Adaptada)
            for item in items:
                track = item['track']
                played_at = item['played_at'] # Formato ISO de Spotify
                raw_track_id = track['id']
                
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
                # 4. Inyectamos en la tabla 'reproducciones' vinculando al user_id actual
                # Usamos INSERT OR IGNORE para que si el tema ya existía con ese timestamp, no se duplique
                cursor.execute('''
                    INSERT OR IGNORE INTO reproducciones (user_id, track_id, played_at)
                    VALUES (?, ?, ?)
                ''', (user_id, track_id, played_at))
                
                if cursor.rowcount > 0:
                    NUEVOS_TEMAS_CONTADOR += 1

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
            
            print(f"✅ Guardado fino: {NUEVOS_TEMAS_CONTADOR} reproducciones nuevas indexadas para {user_id}.")

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