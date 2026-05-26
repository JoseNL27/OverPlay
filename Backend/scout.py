import sqlite3
import os
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
                
                # --- [AQUÍ VA TU MAGIA DE LIMPIEZA DE CARACTERES] ---
                # Explotas el nombre, separas principal y colaboradores, etc.
                # Al final generas tu track_id único compuesto:
                # track_id = track_name_limpio + " - " + artista_principal
                track_id = raw_track_id # Cambia esto por tu track_id compuesto limpio de siempre
                
                # 4. Inyectamos en la tabla 'reproducciones' vinculando al user_id actual
                # Usamos INSERT OR IGNORE para que si el tema ya existía con ese timestamp, no se duplique
                cursor.execute('''
                    INSERT OR IGNORE INTO reproducciones (user_id, track_id, played_at)
                    VALUES (?, ?, ?)
                ''', (user_id, track_id, played_at))
                
                if cursor.rowcount > 0:
                    NUEVOS_TEMAS_CONTADOR += 1

                # 5. Enriquecemos la tabla global 'canciones' si el tema es nuevo en el sistema
                # (Aquí meterías tu INSERT OR REPLACE INTO canciones que me pasaste antes)
                # ...
            
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