import sqlite3
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# --- CONFIGURACIÓN ---
# Usamos las mismas credenciales que en tu main.py
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id = "d73395f3767b466fa12fba7968692f6d",
    client_secret = "b797c410cdcf45eeb7fe21c02068af81",
    redirect_uri = "http://127.0.0.1:8888",
    scope="playlist-read-private",
))

def analizar_mi_playlist(playlist_url):
    conexion = sqlite3.connect('historial.db')
    cursor = conexion.cursor()
    
    # 1. Extraer ID de la playlist desde la URL
    playlist_id = playlist_url.split('/')[-1].split('?')[0]
    
    # 2. Obtener canciones de la playlist
    resultados = sp.playlist_items(playlist_id)
    tracks_playlist = []
    
    for item in resultados['items']:
        track = item['track']
        # Usamos nuestro ID Sintético (Nombre - Artista) para cruzar datos
        id_sintetico = f"{track['name']} - {track['artists'][0]['name']}"
        tracks_playlist.append(id_sintetico)

    # 3. Consultar fatiga en la DB
    rojas, amarillas, verdes = 0, 0, 0
    puntos_totales = 0
    
    print(f"\n--- Análisis de Playlist ---")
    for tid in tracks_playlist:
        cursor.execute("SELECT puntos_fatiga FROM fatiga_canciones WHERE track_id = ?", (tid,))
        resultado = cursor.fetchone()
        
        puntos = resultado[0] if resultado else 0
        puntos_totales += puntos
        
        if puntos >= 60: rojas += 1
        elif puntos >= 30: amarillas += 1
        else: verdes += 1

    # 4. Mostrar informe
    total = len(tracks_playlist)
    promedio = puntos_totales / total
    print(f"Canciones analizadas: {total}")
    print(f"🔴 Rojas: {rojas} | 🟡 Amarillas: {amarillas} | 🟢 Verdes: {verdes}")
    print(f"Índice de Fatiga Medio: {promedio:.2f}")
    
    if promedio > 50:
        print("⚠️ VERDICTO: ¡Playlist muy quemada! Busca algo nuevo.")
    else:
        print("✅ VERDICTO: La música está fresca, ¡disfrútala!")

    conexion.close()

# Prueba con una de tus playlists
analizar_mi_playlist("https://open.spotify.com/playlist/2VRDccv1JHO6kj1QkCASmG")