import csv
import sqlite3

# --- CONFIGURACIÓN ---
archivo_csv = 'historial_spotify_completo.csv'  # <--- PON EL NOMBRE DE TU CSV AQUÍ
base_datos = 'historial.db'

# Conectamos a la base de datos
conexion = sqlite3.connect(base_datos)
cursor = conexion.cursor()

# Contadores para ver el resultado
canciones_importadas = 0
canciones_ignoradas = 0

print("Empezando la importación del historial...")

# Abrimos el CSV usando la librería nativa de Python
with open(archivo_csv, mode='r', encoding='utf-8') as archivo:
    # Si tu CSV usa punto y coma, cambia delimiter=',' por delimiter=';'
    lector = csv.DictReader(archivo, delimiter=',')
    
    for fila in lector:
        track_name = fila['master_metadata_track_name']
        artist_name = fila['master_metadata_album_artist_name']
        played_at = fila['ts']
        
        # 1. Filtro de basura: A veces los podcasts o archivos locales no tienen nombre
        if not track_name or not artist_name:
            continue
            
        # 2. Filtro de Skips instantáneos: Si duró menos de 30 segundos (30000 ms), no la contamos
        ms_played = int(fila['ms_played']) if fila['ms_played'].isdigit() else 0
        if ms_played < 30000:
            canciones_ignoradas += 1
            continue

        # 3. Creamos nuestro propio "Track ID" universal e indestructible
        track_id_sintetico = f"{track_name} - {artist_name}"

        # 4. Insertamos en la base de datos (ignorando si la fecha/hora ya existe)
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO reproducciones (played_at, track_id, track_name, artist_name)
                VALUES (?, ?, ?, ?)
            ''', (played_at, track_id_sintetico, track_name, artist_name))
            
            if cursor.rowcount == 1:
                canciones_importadas += 1
        except Exception as e:
            print(f"Error en la fila {played_at}: {e}")

conexion.commit()
conexion.close()

print(f"\n--- RESUMEN DE IMPORTACIÓN ---")
print(f"✅ Canciones añadidas a la BD: {canciones_importadas}")
print(f"👻 Skips rápidos ignorados (<30s): {canciones_ignoradas}")
print(f"------------------------------")