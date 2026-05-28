import spotipy
import requests
import sqlite3
from db import obtener_conexion  # o donde tengas esto
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET  # o donde estén

def obtener_sp_para_usuario(user_id: str) -> spotipy.Spotify:
    conexion = obtener_conexion()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    try:
        cursor.execute("SELECT refresh_token FROM usuarios WHERE user_id = ?", (user_id,))
        usuario_db = cursor.fetchone()
        if not usuario_db or not usuario_db['refresh_token']:
            raise Exception(f"Sin refresh_token para user_id={user_id}")

        res = requests.post("https://accounts.spotify.com/api/token", data={
            "grant_type": "refresh_token",
            "refresh_token": usuario_db['refresh_token'],
            "client_id": SPOTIFY_CLIENT_ID,
            "client_secret": SPOTIFY_CLIENT_SECRET
        })

        access_token = res.json().get("access_token")
        if not access_token:
            raise Exception("No se pudo refrescar el token de Spotify")

        return spotipy.Spotify(auth=access_token)

    finally:
        conexion.close()