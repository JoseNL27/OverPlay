import os
import secrets
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI
from engine import mapear_top_artistas_cold_start, procesar_cold_start, mapear_top_tracks_cold_start, procesar_fatiga_canciones
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException, Response, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import random
import spotipy
import requests
from datetime import datetime, timedelta
from spotipy.oauth2 import SpotifyOAuth
class ConfigUsuario(BaseModel):
    factor_sensibilidad: float
    tolerancia_atracon: float
    tasa_amnesia: float
    ano_nostalgia: int
    generos_rapidos: str
    generos_refugio: str

# --- CONFIGURACIÓN DE SPOTIFY ---
CLIENT_ID = SPOTIFY_CLIENT_ID
CLIENT_SECRET = SPOTIFY_CLIENT_SECRET
REDIRECT_URI = SPOTIFY_REDIRECT_URI

#BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Ruta al token en la carpeta raíz (un nivel por encima de backend)
#TOKEN_PATH = os.path.join(os.path.dirname(BASE_DIR), "spotify_token.cache")

# Inicializamos Spotify con el nuevo permiso y la ruta CLAVADA al token
#sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
#    client_id=CLIENT_ID,
 #   client_secret=CLIENT_SECRET,
  #  redirect_uri=REDIRECT_URI,
   # scope="user-read-recently-played playlist-read-private", 
    #open_browser=False,
    #cache_path=TOKEN_PATH # <--- EL FIX ESTÁ AQUÍ
#))

app = FastAPI()

# --- CONFIGURACIÓN DE RUTAS FRONTEND ---
# Calculamos dónde está la carpeta 'app' en relación a este archivo 'api.py'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(BASE_DIR, "../app")

# Permitimos que la API sirva el CSS y el JS
app.mount("/static", StaticFiles(directory=APP_DIR, html=False), name="static")

@app.get("/")
def cargar_interfaz():
    # Le decimos a la API dónde encontrar el index.html exactamente
    ruta_index = os.path.join(APP_DIR, "index.html")
    with open(ruta_index, "r", encoding="utf-8") as archivo:
        return HTMLResponse(content=archivo.read())
# ---------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def obtener_conexion():
    # Usamos BASE_DIR que ya tenías definido arriba
    ruta_bd = os.path.join(BASE_DIR, 'historial.db')
    conexion = sqlite3.connect(ruta_bd, check_same_thread=False)
    conexion.row_factory = sqlite3.Row 
    # Activar el modo WAL para evitar el error "Database is Locked"
    conexion.execute("PRAGMA journal_mode=WAL;")
    return conexion

# --- RUTAS DE LA API ---

@app.get("/login")
def login_spotify():
    # Mandamos al tester a la página oficial de Spotify a dar permiso
    scope = "user-read-recently-played user-top-read"
    url = f"https://accounts.spotify.com/authorize?response_type=code&client_id={CLIENT_ID}&scope={scope}&redirect_uri={REDIRECT_URI}"
    return RedirectResponse(url)

# ==========================================
# 🛑 CERRAR SESIÓN Y DESTRUIR COOKIE
# ==========================================
@app.get("/logout")
def cerrar_sesion():
    # 1. Preparamos el billete de vuelta a la página principal
    response = RedirectResponse(url="/")
    
    # 2. Aniquilamos el sello de seguridad
    response.delete_cookie(key="session_user")
    
    return response

@app.get("/callback")
def callback_spotify(code: str):
    print("🛸 Código recibido de Spotify, iniciando intercambio de tokens...")
    
    # 1. Usamos tus variables del config.py para el intercambio
    res = requests.post("https://accounts.spotify.com/api/token", data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI,  # <-- Tu variable global
        "client_id": SPOTIFY_CLIENT_ID,        # <-- Tu variable global
        "client_secret": SPOTIFY_CLIENT_SECRET # <-- Tu variable global
    })
    tokens = res.json()
    
    # 🚨 CHIVATO DE ERRORES: Si Spotify nos rechaza, nos lo dice por consola
    if "error" in tokens:
        print(f"❌ RECHAZO DE SPOTIFY: {tokens.get('error_description', tokens['error'])}")
        print(f"👉 Revisa que SPOTIFY_REDIRECT_URI en tu config.py sea EXACTO al del Dashboard.")
        return RedirectResponse(url="/")

    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    
    # 2. Le preguntamos a Spotify quién eres
    user_res = requests.get("https://api.spotify.com/v1/me", headers={
        "Authorization": f"Bearer {access_token}"
    })
    user_data = user_res.json()
    spotify_user_id = user_data.get("id")
    display_name = user_data.get("display_name", spotify_user_id)

    sp = spotipy.Spotify(auth=access_token)
   
   # ==========================================
        # 🧠 COLD START INTELIGENTE (A.I.A.)
        # ==========================================
        # Comprobamos si ya le hemos hecho el escáner a este usuario antes
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM perfiles_usuario WHERE user_id = ?", (spotify_user_id,))
    if not cursor.fetchone():
        print(f"[🛰️] Usuario nuevo ({spotify_user_id}). Iniciando escáner de Cold Start...")
            
        try:
            # 1. Le pedimos los datos a Spotify (La Matriz)
            matriz = mapear_top_artistas_cold_start(sp)
                
            # 2. El motor procesa la psicología del usuario
            resultados_artistas, estilo, sensibilidad = procesar_cold_start(matriz)
                
            # Definimos la recuperación base según el estilo (puedes ajustar estos días)
            recuperacion = 30 if estilo == "Fiel" else 15
                
            # 3. Guardamos su Perfil Global
            cursor.execute("""
                    INSERT INTO perfiles_usuario (user_id, sensibilidad_fatiga, tiempo_recuperacion, estilo_escucha)
                    VALUES (?, ?, ?, ?)
                """, (spotify_user_id, sensibilidad, recuperacion, estilo))
                
            # 4. Guardamos el O.V.R. base de sus artistas top
            for artista, datos in resultados_artistas.items():
                    cursor.execute("""
                        INSERT INTO fatiga_artistas (user_id, artista, clasificacion, ovr_base)
                        VALUES (?, ?, ?, ?)
                    """, (spotify_user_id, artista, datos["clasificacion"], datos["ovr_inicial"]))

            # ========================================================
                # 🎵 🚀 NUEVA LÓGICA: COLD START DE CANCIONES (fatiga_actual)
                # ========================================================
            print(f"[🎵] Escaneando tracks de {spotify_user_id}...")
                
                # 1. Traemos la matriz de canciones que ya has programado
            matriz_canciones = mapear_top_tracks_cold_start(sp)
                
                # 2. Procesamos el OVR inicial de cada track
            resultados_canciones = procesar_fatiga_canciones(matriz_canciones)
                
                # Timestamp actual para dejar registro limpio de cuándo se calculó
            ahora_str = datetime.now().isoformat()

                # 3. Inyectamos en la tabla fatiga_actual
            for track_id, datos in resultados_canciones.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO fatiga_actual 
                    (user_id, track_id, lambda, puntos_fatiga, overrate, pico_historico, etiquetas, fecha_pico, ultima_actualizacion)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    spotify_user_id, 
                    track_id, 
                    0.0,              # lambda inicial por defecto
                    0.0,              # puntos_fatiga inicial por defecto
                    datos["overrate"], # 🔥 ¡Tu OVR inicial de la canción!
                    datos["overrate"], # El pico histórico inicial coincide con su arranque
                    datos["etiqueta"], # 'Bucle Reciente', 'Quemada Histórica', etc.
                    ahora_str,        # fecha_pico
                    ahora_str         # ultima_actualizacion
                ))

            conexion.commit()
            print(f"✅ Perfil creado con éxito -> Estilo: {estilo} | Multiplicador: {sensibilidad}x")
                
        except Exception as e:
                print(f"❌ Error durante el Cold Start: {e}")
                conexion.rollback() # Si algo peta, deshacemos para que no se quede a medias

    # 3. 💾 GUARDADO EN DB
    if spotify_user_id:
        try:
            
            cursor.execute('''
                INSERT OR REPLACE INTO usuarios (user_id, nombre, refresh_token, rol) 
                VALUES (?, ?, ?, ?)
            ''', (spotify_user_id, display_name, refresh_token, 'admin'))
            
            conexion.commit()
            conexion.close()
            print(f"   ✅ OPERADOR REGISTRADO EN DB: {display_name} (ID: {spotify_user_id})")
        except Exception as e:
            print(f"   ❌ Error crítico al escribir en SQLite: {e}")
    else:
        print("   ❌ No se pudo rescatar el ID de usuario.")

    # 4. 🛡️ SELLO DE SESIÓN
    response = RedirectResponse(url="/")
    response.set_cookie(
        key="session_user", 
        value=spotify_user_id, 
        httponly=True, 
        samesite="lax"
    )
    conexion.close()
    return response

# ==========================================
# 🕵️‍♂️ EL CHIVATO DE SESIÓN (Frontera Frontend/Backend)
# ==========================================
@app.get("/api/me")
def obtener_usuario_actual(request: Request):
    # 1. Intentamos leer la cookie blindada
    user_id = request.cookies.get("session_user")
    
    # 2. Si no hay cookie, cerramos la puerta de golpe (Error 401)
    if not user_id:
        raise HTTPException(status_code=401, detail="No hay sesión activa")
        
    # 3. Si hay cookie, buscamos su nombre en la base de datos
    try:
        conexion = sqlite3.connect("historial.db")
        cursor = conexion.cursor()
        
        cursor.execute("SELECT nombre FROM usuarios WHERE user_id = ?", (user_id,))
        fila = cursor.fetchone()
        conexion.close()
        
        # 4. Devolvemos el JSON limpio para que el JavaScript lo pinte en el Perfil
        if fila:
            return {"user_id": user_id, "nombre": fila[0]}
        else:
            # Por si borraste la DB pero la cookie se quedó guardada en el navegador
            raise HTTPException(status_code=401, detail="Usuario no existe en DB")
            
    except Exception as e:
        print(f"Error en /api/me: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/debug/cancion/{track_id}")
def debug_cancion(track_id: str):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    informe = {"track_id": track_id}
    
    # 1. Datos del motor de Fatiga (V2: fatiga_actual)
    cursor.execute("SELECT lambda_actual, puntos_fatiga, ultima_modificacion FROM fatiga_actual WHERE track_id = ?", (track_id,))
    fila_fatiga = cursor.fetchone()
    if fila_fatiga:
        informe["fatiga"] = dict(fila_fatiga)
    else:
        informe["fatiga"] = "No registrada en el motor de fatiga"

    # 2. Historial de Reproducciones y Popularidad
    cursor.execute('''
        SELECT COUNT(*) as total_escuchas, 
               MIN(played_at) as primera_escucha, 
               MAX(played_at) as ultima_escucha
        FROM reproducciones WHERE track_id = ?
    ''', (track_id,))
    fila_rep = cursor.fetchone()
    if fila_rep and fila_rep['total_escuchas'] > 0:
        informe["historial"] = dict(fila_rep)
    else:
        informe["historial"] = "No hay reproducciones registradas"

    # 3. La Caja Fuerte (Feedback Manual)
    cursor.execute("SELECT puntos_extra, lambda_multiplicador FROM feedback_usuario WHERE track_id = ?", (track_id,))
    fila_fb = cursor.fetchone()
    if fila_fb:
        informe["feedback"] = dict(fila_fb)
    else:
        informe["feedback"] = "Sin interacciones manuales (Neutro)"

    conexion.close()

    # --- IMPRESIÓN BONITA EN LA CONSOLA DE TERMUX ---
    print("\n" + "═"*50)
    print(f"🕵️‍♂️ RADIOGRAFÍA MODO DEBUG: {track_id}")
    print("═"*50)
    print(f"🔥 FATIGA:   {informe.get('fatiga')}")
    print(f"📈 HISTORIAL: {informe.get('historial')}")
    print(f"👍 FEEDBACK:  {informe.get('feedback')}")
    print("═"*50 + "\n")

    return informe

@app.get("/top-quemadas")
def obtener_top_quemadas(limite: int = 15):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    # V2: Usamos fatiga_actual
    cursor.execute('''
        SELECT f.track_id, f.lambda_actual, f.puntos_fatiga, MAX(r.played_at) as verdadera_ultima_escucha 
        FROM fatiga_actual f
        JOIN reproducciones r ON f.track_id = r.track_id
        GROUP BY f.track_id
        ORDER BY f.puntos_fatiga DESC 
        LIMIT ?
    ''', (limite,))
    canciones = cursor.fetchall()
    conexion.close()
    
    resultado = []
    for c in canciones:
        resultado.append({
            "cancion": c['track_id'],
            "puntos": round(c['puntos_fatiga'], 2),
        })
    return {"top_quemadas": resultado}

# NUEVA RUTA 1: Obtener TODAS las playlists con su PORTADA
@app.get("/playlists")
def obtener_playlists():
    print("📡 Frontend pide playlists... Conectando con Spotify...", flush=True) 
    try:
        resultado = []
        playlists = sp.current_user_playlists(limit=50) 
        
        while playlists:
            for item in playlists['items']:
                if item is None: continue
                
                imagen = item['images'][0]['url'] if item.get('images') and len(item['images']) > 0 else "https://via.placeholder.com/150"
                
                resultado.append({
                    "id": item['id'], 
                    "nombre": item['name'],
                    "imagen": imagen,
                    "total_tracks": item['tracks']['total']
                })
                
            if playlists['next']:
                playlists = sp.next(playlists)
            else:
                break
                
        print(f"✅ ¡Éxito! {len(resultado)} playlists enviadas al frontend.", flush=True)
        return resultado 

    except Exception as e:
        print(f"❌ ERROR CRÍTICO AL SACAR PLAYLISTS: {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))
        
# NUEVA RUTA 2: Analizar playlist y traer PORTADAS DE CANCIONES
@app.get("/playlist/{playlist_id}") 
def analizar_playlist(playlist_id: str):
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        
        tracks_playlist = []
        resultados = sp.playlist_items(playlist_id, limit=100)
        
        while resultados:
            for item in resultados['items']:
                if item['track'] is None: continue
                t = item['track']
                track_name = t.get('name', 'Desconocido')
                artist_name = t['artists'][0]['name'] if t.get('artists') else 'Desconocido'
                imagen = t['album']['images'][0]['url'] if t.get('album') and t['album'].get('images') else "https://via.placeholder.com/150"
                
                tracks_playlist.append({
                    "id_sintetico": f"{track_name} - {artist_name}",
                    "nombre": track_name,
                    "artista": artist_name,
                    "imagen": imagen
                })
                
            if resultados['next']:
                resultados = sp.next(resultados)
            else:
                break

        analisis = []
        for track in tracks_playlist:
            # V2: fatiga_actual
            cursor.execute("SELECT puntos_fatiga FROM fatiga_actual WHERE track_id = ?", (track["id_sintetico"],))
            fila = cursor.fetchone()
            puntos = fila['puntos_fatiga'] if fila else 0.0
            
            analisis.append({
                "track_id": track["id_sintetico"], 
                "nombre": track["nombre"],
                "artista": track["artista"],
                "imagen": track["imagen"],
                "puntos_fatiga": round(puntos, 2) 
            })
            
        conexion.close()
        return analisis

    except Exception as e:
        print(f"❌ ERROR AL ANALIZAR PLAYLIST: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- NUEVO CÓDIGO PARA EL FEEDBACK ---
class FeedbackData(BaseModel):
    track_id: str
    accion: str

@app.post("/feedback")
def registrar_feedback(datos: FeedbackData):
    print(f"📩 FEEDBACK RECIBIDO: {datos.accion} para {datos.track_id}") 
    conexion = obtener_conexion()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()
    
    cursor.execute("INSERT OR IGNORE INTO feedback_usuario (track_id) VALUES (?)", (datos.track_id,))
    cursor.execute("SELECT puntos_extra, lambda_multiplicador FROM feedback_usuario WHERE track_id = ?", (datos.track_id,))
    fila_fb = cursor.fetchone()
    
    puntos_extra = fila_fb['puntos_extra']
    multiplicador = fila_fb['lambda_multiplicador']
    
    if datos.accion == "dislike":
        puntos_extra += 35.0
        multiplicador *= 0.5
    elif datos.accion == "like":
        puntos_extra -= 35.0
        multiplicador *= 2.0
        
    cursor.execute('''
        UPDATE feedback_usuario 
        SET puntos_extra = ?, lambda_multiplicador = ? 
        WHERE track_id = ?
    ''', (puntos_extra, multiplicador, datos.track_id))
    
    # V2: fatiga_actual
    cursor.execute("SELECT puntos_fatiga, lambda_actual FROM fatiga_actual WHERE track_id = ?", (datos.track_id,))
    fila_fatiga = cursor.fetchone()
    
    puntos_finales = 0.0
    if fila_fatiga:
        if datos.accion == "dislike":
            puntos_finales = min(100.0, fila_fatiga['puntos_fatiga'] + 35.0)
            nuevo_lambda = max(0.01, fila_fatiga['lambda_actual'] * 0.5)
        else:
            puntos_finales = max(0.0, fila_fatiga['puntos_fatiga'] - 35.0)
            nuevo_lambda = min(0.15, fila_fatiga['lambda_actual'] * 2.0)
            
        cursor.execute('''
            UPDATE fatiga_actual 
            SET puntos_fatiga = ?, lambda_actual = ? 
            WHERE track_id = ?
        ''', (puntos_finales, nuevo_lambda, datos.track_id))

    conexion.commit()
    conexion.close()
    
    return {"status": "ok", "nuevos_puntos": round(puntos_finales, 2)}


@app.get("/cancion/detalle/{track_id:path}")
def detalle_cancion(track_id: str):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        # 1. METADATOS BÁSICOS
        cursor.execute("SELECT nombre, artista, colaboradores, imagen_url, ano_lanzamiento, popularidad FROM canciones WHERE track_id = ?", (track_id,))
        meta_row = cursor.fetchone()
        if not meta_row:
            return {"error": "Canción no encontrada"}

        meta = {
            "nombre": meta_row[0],
            "artista": meta_row[1],
            "colaboradores": meta_row[2] if meta_row[2] else "",
            "imagen_url": meta_row[3],
            "ano_lanzamiento": meta_row[4] if meta_row[4] else "Desconocido",
            "popularidad": meta_row[5] if meta_row[5] else 0
        }

        # 2. STATS BÁSICAS Y PICO
        cursor.execute("SELECT MIN(played_at), COUNT(*) FROM reproducciones WHERE track_id = ?", (track_id,))
        stats_row = cursor.fetchone()
        dia_descubrimiento = stats_row[0][:10] if stats_row and stats_row[0] else "Desconocido"
        total_escuchas = stats_row[1] or 0

        cursor.execute("SELECT overrate, pico_historico, fecha_pico FROM fatiga_actual WHERE track_id = ?", (track_id,))
        fat_row = cursor.fetchone()
        or_actual = round(fat_row[0], 1) if fat_row else 0
        pico_trauma = round(fat_row[1], 1) if fat_row else 0
        fecha_pico = fat_row[2] if fat_row else "N/A"

        # 3. 🧠 EL MOTOR DE RACHAS Y GAPS (Tu código dinámico)
        cursor.execute("SELECT played_at FROM reproducciones WHERE track_id = ? ORDER BY played_at ASC", (track_id,))
        filas_repro = cursor.fetchall()
        
        fechas_unicas = sorted(list(set([r[0][:10] for r in filas_repro])))
        fechas_dt = [datetime.strptime(f, "%Y-%m-%d") for f in fechas_unicas]
        
        max_gap = 0
        gap_contexto = "-"
        max_racha = 0
        racha_contexto = "-"

        if len(fechas_dt) >= 1:
            max_racha = 1
            racha_contexto = fechas_dt[0].strftime("%d/%m")
            
            if len(fechas_dt) > 1:
                # Gaps
                for i in range(len(fechas_dt) - 1):
                    diff = (fechas_dt[i+1] - fechas_dt[i]).days
                    if diff > max_gap:
                        max_gap = diff
                        gap_contexto = f"{fechas_dt[i].strftime('%d/%m')} ➔ {fechas_dt[i+1].strftime('%d/%m')}"
                
                # Rachas
                racha_temp = 1
                inicio_temp = fechas_dt[0]
                for i in range(1, len(fechas_dt)):
                    if (fechas_dt[i] - fechas_dt[i-1]).days == 1:
                        racha_temp += 1
                    else:
                        if racha_temp >= max_racha:
                            max_racha = racha_temp
                            racha_contexto = f"{inicio_temp.strftime('%d/%m')} ➔ {fechas_dt[i-1].strftime('%d/%m')}"
                        racha_temp = 1
                        inicio_temp = fechas_dt[i]
                
                if racha_temp >= max_racha:
                    max_racha = racha_temp
                    racha_contexto = f"{inicio_temp.strftime('%d/%m')} ➔ {fechas_dt[-1].strftime('%d/%m')}"

        # 4. GRÁFICOS (Barras y Líneas)
        # --- Gráfico de Repros (Con relleno de días a 0) ---
        cursor.execute('''
            SELECT DATE(played_at) as dia, COUNT(*) 
            FROM reproducciones 
            WHERE track_id = ? 
            GROUP BY dia ORDER BY dia ASC
        ''', (track_id,))
        plays_raw = dict(cursor.fetchall())
        
        grafica_repros = []
        if plays_raw:
            primera_fecha = datetime.strptime(min(plays_raw.keys()), "%Y-%m-%d")
            ultima_fecha = datetime.strptime(max(plays_raw.keys()), "%Y-%m-%d")
            
            fecha_actual = primera_fecha
            while fecha_actual <= ultima_fecha:
                dia_str = fecha_actual.strftime("%Y-%m-%d")
                grafica_repros.append({"x": dia_str, "y": plays_raw.get(dia_str, 0)})
                fecha_actual += timedelta(days=1)

        # --- Gráfico de OverRate ---
        cursor.execute("SELECT fecha, puntos_fatiga FROM historial_diario WHERE track_id = ? ORDER BY fecha ASC", (track_id,))
        grafica_or = [{"x": r[0], "y": r[1]} for r in cursor.fetchall()]

        return {
            "meta": meta,
            "stats": {
                "total_escuchas": total_escuchas,
                "descubrimiento": dia_descubrimiento,
                "or_actual": or_actual,
                "pico_trauma": pico_trauma,
                "fecha_pico": fecha_pico,
                "max_racha_dias": max_racha,
                "racha_contexto": racha_contexto,
                "max_gap_dias": max_gap,
                "gap_contexto": gap_contexto
            },
            "grafica_repros": grafica_repros,
            "grafica_or": grafica_or
        }
    except Exception as e:
        print(f"Error en detalle V2: {e}")
        return {"error": "Fallo interno"}
    finally:
        conexion.close()
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        # 1. METADATOS BÁSICOS
        cursor.execute("SELECT nombre, artista, colaboradores, imagen_url, ano_lanzamiento, popularidad FROM canciones WHERE track_id = ?", (track_id,))
        meta_row = cursor.fetchone()
        if not meta_row:
            return {"error": "Canción no encontrada"}

        meta = {
            "nombre": meta_row[0],
            "artista": meta_row[1],
            "colaboradores": meta_row[2] if meta_row[2] else "",
            "imagen_url": meta_row[3],
            "ano_lanzamiento": meta_row[4] if meta_row[4] else "Desconocido",
            "popularidad": meta_row[5] if meta_row[5] else 0
        }

        # 2. ESTADÍSTICAS PURAS (Info)
        cursor.execute("SELECT MIN(played_at), COUNT(*) FROM reproducciones WHERE track_id = ?", (track_id,))
        stats_row = cursor.fetchone()
        dia_descubrimiento = stats_row[0].split()[0] if stats_row[0] else "Desconocido"
        total_escuchas = stats_row[1] or 0

        # Gráfico de Barras: Reproducciones por día (últimos 7 días activos)
        cursor.execute('''
            SELECT DATE(played_at) as dia, COUNT(*) 
            FROM reproducciones 
            WHERE track_id = ? 
            GROUP BY dia ORDER BY dia ASC LIMIT 14
        ''', (track_id,))
        grafica_repros = [{"x": r[0], "y": r[1]} for r in cursor.fetchall()]

        # 3. ESTADÍSTICAS DE FATIGA (Overrating)
        cursor.execute("SELECT overrate, max_racha_dias, max_gap_dias, pico_trauma, fecha_pico FROM fatiga_actual WHERE track_id = ?", (track_id,))
        fat_row = cursor.fetchone()
        
        stats_fatiga = {
            "total_escuchas": total_escuchas,
            "descubrimiento": dia_descubrimiento,
            "or_actual": round(fat_row[0], 1) if fat_row else 0,
            "max_racha_dias": fat_row[1] if fat_row else 0,
            "max_gap_dias": fat_row[2] if fat_row else 0,
            "pico_trauma": round(fat_row[3], 1) if fat_row else 0,
            "fecha_pico": fat_row[4] if fat_row else "N/A"
        }

        # Gráfico de Líneas: Evolución del OR
        cursor.execute("SELECT fecha, puntos_fatiga FROM historial_diario WHERE track_id = ? ORDER BY fecha ASC", (track_id,))
        grafica_or = [{"x": r[0], "y": r[1]} for r in cursor.fetchall()]

        return {"meta": meta, "stats": stats_fatiga, "grafica_repros": grafica_repros, "grafica_or": grafica_or}
    except Exception as e:
        print(f"Error en detalle: {e}")
        return {"error": "Fallo interno"}
    finally:
        conexion.close()

@app.get("/widgets/canciones")
def obtener_canciones_stats():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        # 🚀 EN RACHA (OverRate alto, escuchadas en los últimos 7 días)
        cursor.execute('''
            SELECT c.nombre, c.artista, c.imagen_url, f.overrate
            FROM canciones c JOIN fatiga_actual f ON c.track_id = f.track_id
            WHERE f.ultima_actualizacion >= date('now', '-7 days')
            ORDER BY f.overrate DESC LIMIT 10
        ''')
        racha = [{"nombre": r[0], "artista": r[1], "img": r[2], "score": round(r[3],1)} for r in cursor.fetchall()]

        # ☢️ QUEMADAS (Máxima fatiga total)
        cursor.execute('''
            SELECT c.nombre, c.artista, c.imagen_url, f.puntos_fatiga
            FROM canciones c JOIN fatiga_actual f ON c.track_id = f.track_id
            ORDER BY f.puntos_fatiga DESC LIMIT 10
        ''')
        quemadas = [{"nombre": r[0], "artista": r[1], "img": r[2], "score": round(r[3],1)} for r in cursor.fetchall()]

        # 🧊 OLVIDADAS (Pico histórico alto, pero fatiga actual casi 0 y llevan tiempo sin sonar)
        cursor.execute('''
            SELECT c.nombre, c.artista, c.imagen_url, f.pico_historico
            FROM canciones c JOIN fatiga_actual f ON c.track_id = f.track_id
            WHERE f.pico_historico > 20 AND f.puntos_fatiga < 10 AND f.ultima_actualizacion < date('now', '-30 days')
            ORDER BY f.pico_historico DESC LIMIT 10
        ''')
        olvidadas = [{"nombre": r[0], "artista": r[1], "img": r[2], "score": round(r[3],1)} for r in cursor.fetchall()]

        # 🕒 RECIENTES (Últimas 10 canciones únicas escuchadas)
        # Usamos GROUP BY para no repetir si te has puesto la misma 3 veces seguidas
        cursor.execute('''
            SELECT c.nombre, c.artista, c.imagen_url, COALESCE(f.overrate, f.puntos_fatiga, 0)
            FROM reproducciones r
            JOIN canciones c ON r.track_id = c.track_id
            LEFT JOIN fatiga_actual f ON c.track_id = f.track_id
            GROUP BY c.track_id
            ORDER BY MAX(r.played_at) DESC
            LIMIT 10
        ''')
        recientes = [{"nombre": r[0], "artista": r[1], "img": r[2], "score": round(r[3],1)} for r in cursor.fetchall()]

        # 🚀 MODIFICAMOS EL RETURN para incluir las recientes:
        return {"racha": racha, "quemadas": quemadas, "olvidadas": olvidadas, "recientes": recientes}

    finally:
        conexion.close()
        
@app.get("/dashboard")
def obtener_dashboard(request: Request): # 👈 Añadimos 'request' para leer las cookies
    # 1. Verificar sesión a través de la cookie segura
    user_id = request.cookies.get("session_user")
    if not user_id:
        raise HTTPException(status_code=401, detail="No autorizado")

    conexion = obtener_conexion()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    # 2. Inicializar el cliente 'sp' dinámicamente usando el refresh_token del usuario
    try:
        cursor.execute("SELECT refresh_token FROM usuarios WHERE user_id = ?", (user_id,))
        usuario_db = cursor.fetchone()
        if not usuario_db or not usuario_db['refresh_token']:
            raise HTTPException(status_code=401, detail="Sesión inválida en DB")
        
        # 🔄 REFRESO MANUAL DIRECTO (Anti-sp_oauth)
        import requests
        from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET # Asegúrate de que tus variables se llaman así
        
        res = requests.post("https://accounts.spotify.com/api/token", data={
            "grant_type": "refresh_token",
            "refresh_token": usuario_db['refresh_token'],
            "client_id": SPOTIFY_CLIENT_ID,
            "client_secret": SPOTIFY_CLIENT_SECRET
        })
        
        tokens_nuevos = res.json()
        nuevo_access_token = tokens_nuevos.get("access_token")
        
        if not nuevo_access_token:
            raise HTTPException(status_code=401, detail="No se pudo refrescar el token de Spotify")
            
        # Inicializamos sp con el token fresco del usuario actual
        sp = spotipy.Spotify(auth=nuevo_access_token)
        
    except Exception as e:
        print(f"❌ Error autenticando sp en dashboard: {e}")
        conexion.close()
        raise HTTPException(status_code=500, detail="Error de autenticación con Spotify")

    dashboard = {"en_racha": [], "quemadas": [], "subiendo": [], "olvidadas": []}

    # --- OBTENER IDS ---
    try:
        # Corregido a lambda (tu columna base de fatiga_actual)
        cursor.execute("SELECT track_id FROM fatiga_actual WHERE user_id = ? ORDER BY lambda DESC LIMIT 4", (user_id,))
        ids_racha = [row['track_id'] for row in cursor.fetchall()]
    except: ids_racha = []

    try:
        cursor.execute("SELECT track_id FROM fatiga_actual WHERE user_id = ? ORDER BY puntos_fatiga DESC LIMIT 4", (user_id,))
        ids_quemadas = [row['track_id'] for row in cursor.fetchall()]
    except: ids_quemadas = []

    try:
        cursor.execute('''
            SELECT track_id FROM reproducciones 
            WHERE user_id = ? AND played_at >= date('now', '-7 days')
            GROUP BY track_id 
            ORDER BY COUNT(*) DESC LIMIT 4
        ''', (user_id,))
        ids_subiendo = [row['track_id'] for row in cursor.fetchall()]
    except: ids_subiendo = []

    try:
        cursor.execute('''
            SELECT track_id FROM fatiga_actual
            WHERE user_id = ? AND pico_historico > 50
            ORDER BY RANDOM() LIMIT 4
        ''', (user_id,))
        ids_olvidadas = [row['track_id'] for row in cursor.fetchall()]
    except: ids_olvidadas = []

    todos_los_temas = list(set(ids_racha + ids_quemadas + ids_subiendo + ids_olvidadas))
    
    # --- CONSULTAR CACHÉ LOCAL ---
    mapa_canciones = {}
    if todos_los_temas:
        placeholders = ', '.join(['?'] * len(todos_los_temas))
        cursor.execute(f"SELECT * FROM canciones WHERE track_id IN ({placeholders})", todos_los_temas)
        for row in cursor.fetchall():
            mapa_canciones[row['track_id']] = {
                "track_id": row['track_id'], 
                "nombre": row['nombre'],
                "artista": row['artista'],
                "imagen": row['imagen_url']
            }

    # --- LO QUE NO ESTÉ EN CACHÉ, SE BUSCA EN SPOTIFY ---
    temas_faltantes = [t for t in todos_los_temas if t not in mapa_canciones]
    
    if temas_faltantes:
        print(f"🔍 Buscando {len(temas_faltantes)} temas faltantes en Spotify para poblar caché...")
        for tema in temas_faltantes:
            try:
                # El id inmutable suele ser "Nombre - Artista", buscamos limpio
                res = sp.search(q=tema, type="track", limit=1)
                if res['tracks']['items']:
                    t = res['tracks']['items'][0]
                    nombre = t['name']
                    artista = t['artists'][0]['name']
                    img = t['album']['images'][0]['url'] if t['album']['images'] else ""
                    fecha_salida = t.get('album', {}).get('release_date', '')
                    año = int(fecha_salida[:4]) if len(fecha_salida) >= 4 else None
                    popularidad = t.get('popularity', 50)
                    album_name = t.get('album', {}).get('name', 'Single')
                else:
                    partes = tema.split(' - ')
                    nombre = partes[0] if len(partes) > 0 else tema
                    artista = partes[1] if len(partes) > 1 else "Unknown"
                    img = ""
                    año = None
                    popularidad = 50
                    album_name = "Single"

                mapa_canciones[tema] = {
                    "track_id": tema,
                    "nombre": nombre, 
                    "artista": artista, 
                    "imagen": img
                }
                
                # 🔧 ADAPTACIÓN ANTI-TROLY: Insertamos respetando las 10 columnas reales de tu DB
                cursor.execute('''
                    INSERT OR REPLACE INTO canciones 
                    (track_id, nombre, artista, colaboradores, imagen_url, artista_img, album, ano_lanzamiento, popularidad, generos)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (tema, nombre, artista, "", img, "", album_name, año, popularidad, ""))
                
            except Exception as e:
                print(f"❌ Error en caché de '{tema}': {e}")
        
        conexion.commit()

    # --- CONSTRUIR RESPUESTA ---
    for tid in ids_racha:
        if tid in mapa_canciones: dashboard["en_racha"].append(mapa_canciones[tid])
    for tid in ids_quemadas:
        if tid in mapa_canciones: dashboard["quemadas"].append(mapa_canciones[tid])
    for tid in ids_subiendo:
        if tid in mapa_canciones: dashboard["subiendo"].append(mapa_canciones[tid])
    for tid in ids_olvidadas:
        if tid in mapa_canciones: dashboard["olvidadas"].append(mapa_canciones[tid])

    # --- ÍNDICE DE SATURACIÓN SEMANAL ---
    dashboard["fatiga_semanal"] = 0.0
    dashboard["estado_semanal"] = "FRESH"
    
    try:
        cursor.execute('''
            SELECT AVG(IFNULL(f.puntos_fatiga, 0)) as media_fatiga
            FROM (
                SELECT DISTINCT track_id 
                FROM reproducciones 
                WHERE user_id = ? AND played_at >= date('now', '-7 days')
            ) r
            LEFT JOIN fatiga_actual f ON r.track_id = f.track_id AND f.user_id = ?
        ''', (user_id, user_id))
        fila = cursor.fetchone()
        media = fila['media_fatiga'] if fila and fila['media_fatiga'] else 0.0
        
        dashboard["fatiga_semanal"] = round(media, 1)
        
        if media < 30: dashboard["estado_semanal"] = "ÓPTIMO"
        elif media < 65: dashboard["estado_semanal"] = "PRECAUCIÓN"
        else: dashboard["estado_semanal"] = "SATURADO"
        
    except Exception as e:
        print(f"❌ Error calculando fatiga semanal: {e}")
        
    conexion.close()
    return dashboard

@app.get("/radar")
def obtener_radar_filtrado(rango: str = "MAX"):
    conexion = sqlite3.connect("historial.db")
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()
    
    filtro = ""
    if rango == "1S": filtro = "-7 days"
    elif rango == "1M": filtro = "-1 month"
    elif rango == "1A": filtro = "-1 year"
    
    try:
        if filtro:
            # V2: fatiga_actual
            cursor.execute(f'''
                SELECT 
                    SUM(CASE WHEN f.puntos_fatiga < 30 THEN 1 ELSE 0 END) as fresh,
                    SUM(CASE WHEN f.puntos_fatiga >= 30 AND f.puntos_fatiga < 65 THEN 1 ELSE 0 END) as warning,
                    SUM(CASE WHEN f.puntos_fatiga >= 65 THEN 1 ELSE 0 END) as burnout
                FROM fatiga_actual f
                INNER JOIN (
                    SELECT DISTINCT track_id FROM reproducciones WHERE played_at >= date('now', '{filtro}')
                ) r ON f.track_id = r.track_id
            ''')
        else:
            cursor.execute('''
                SELECT 
                    SUM(CASE WHEN puntos_fatiga < 30 THEN 1 ELSE 0 END) as fresh,
                    SUM(CASE WHEN puntos_fatiga >= 30 AND puntos_fatiga < 65 THEN 1 ELSE 0 END) as warning,
                    SUM(CASE WHEN puntos_fatiga >= 65 THEN 1 ELSE 0 END) as burnout
                FROM fatiga_actual
            ''')
            
        eco_fila = cursor.fetchone()
        datos = {
            "fresh": eco_fila['fresh'] if eco_fila['fresh'] else 0,
            "warning": eco_fila['warning'] if eco_fila['warning'] else 0,
            "burnout": eco_fila['burnout'] if eco_fila['burnout'] else 0
        }
    except Exception as e:
        print(f"❌ Error en radar dinámico: {e}")
        datos = {"fresh": 0, "warning": 0, "burnout": 0}
    finally:
        conexion.close()
        
    return datos

@app.get("/joya")
def obtener_joya_del_dia():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    try:
        # Buscamos la joya
        cursor.execute('''
            SELECT r.track_id, m.nombre, m.artista, m.imagen_url, IFNULL(f.puntos_fatiga, 0) as fatiga
            FROM (
                SELECT track_id, COUNT(*) as total_repros, MAX(played_at) as ultima_vez
                FROM reproducciones
                GROUP BY track_id
            ) r
            LEFT JOIN canciones m ON r.track_id = m.track_id
            LEFT JOIN fatiga_actual f ON r.track_id = f.track_id
            WHERE fatiga < 20 
            AND r.total_repros >= 5
            AND r.ultima_vez <= date('now', '-14 days')
            ORDER BY r.total_repros DESC
            LIMIT 1
        ''')
        
        joya = cursor.fetchone()
        
        if joya:
            j_dict = dict(joya)
            # Si no tiene nombre, es que no está en la tabla canciones. ¡A buscarla a Spotify!
            if not j_dict.get('nombre'):
                print(f"🔍 Joya indocumentada detectada ({j_dict['track_id']}). Preguntando a Spotify...")
                res = sp.search(q=j_dict['track_id'], type="track", limit=1)
                
                if res['tracks']['items']:
                    t = res['tracks']['items'][0]
                    nombre, artista = t['name'], t['artists'][0]['name']
                    img = t['album']['images'][0]['url'] if t['album']['images'] else "https://via.placeholder.com/640"
                    
                    # La guardamos para siempre
                    cursor.execute('''
                        INSERT OR REPLACE INTO canciones (track_id, nombre, artista, imagen_url)
                        VALUES (?, ?, ?, ?)
                    ''', (j_dict['track_id'], nombre, artista, img))
                    conexion.commit()
                    
                    # Actualizamos el diccionario para el frontend
                    j_dict['nombre'] = nombre
                    j_dict['artista'] = artista
                    j_dict['imagen_url'] = img
            
            # Mapeamos 'imagen_url' a 'imagen' por si el frontend de JS lo espera así
            j_dict['imagen'] = j_dict.get('imagen_url')
            return j_dict
        else:
            return {"error": "no_hay_joya"}
            
    except Exception as e:
        print(f"❌ Error buscando la joya: {e}")
        return {"error": "crasheo"}
    finally:
        conexion.close()

# =========================================================
# ⚙️ PANEL DE CONTROL (Configuración del Usuario 1)
# =========================================================

@app.get("/config")
def obtener_configuracion():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT * FROM configuracion_usuario WHERE id = 1")
        fila = cursor.fetchone()
        if fila:
            return dict(fila)
        return {"error": "Configuración no encontrada"}
    finally:
        conexion.close()

@app.post("/config")
def guardar_configuracion(config: ConfigUsuario):
    print("⚙️ Recibiendo nuevos ajustes del Frontend...")
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute('''
            UPDATE configuracion_usuario 
            SET factor_sensibilidad = ?,
                tolerancia_atracon = ?,
                tasa_amnesia = ?,
                ano_nostalgia = ?,
                generos_rapidos = ?,
                generos_refugio = ?
            WHERE id = 1
        ''', (
            config.factor_sensibilidad, 
            config.tolerancia_atracon, 
            config.tasa_amnesia, 
            config.ano_nostalgia, 
            config.generos_rapidos, 
            config.generos_refugio
        ))
        conexion.commit()
        return {"status": "ok", "mensaje": "Ajustes guardados a fuego 🔥"}
    except Exception as e:
        print(f"❌ Error al guardar config: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conexion.close()

@app.get("/generos_db")
def obtener_generos_db():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        # Sacamos todos los géneros que no estén vacíos
        cursor.execute("SELECT generos FROM canciones WHERE generos IS NOT NULL AND generos != ''")
        filas = cursor.fetchall()
        
        todos_los_generos = set()
        for fila in filas:
            # Los géneros vienen separados por comas: "trap, reggaeton, pop"
            lista = [g.strip().lower() for g in fila[0].split(',') if g.strip()]
            todos_los_generos.update(lista)
            
        return {"generos": sorted(list(todos_los_generos))}
    except Exception as e:
        print(f"❌ Error al sacar géneros: {e}")
        return {"generos": []}
    finally:
        conexion.close()

@app.get("/widgets/artistas")
def obtener_artistas_stats():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        # 🔥 ARTISTAS QUEMADOS
        cursor.execute('''
            SELECT c.artista, SUM(f.overrate) as total_overrate, MAX(c.artista_img) as img
            FROM canciones c
            JOIN fatiga_actual f ON c.track_id = f.track_id
            GROUP BY c.artista
            ORDER BY total_overrate DESC
            LIMIT 5
        ''')
        quemados = [{"nombre": r[0], "score": round(r[1], 1), "img": r[2] if r[2] else ""} for r in cursor.fetchall()]

        # 🧊 ARTISTAS FRÍOS
        cursor.execute('''
            SELECT c.artista, SUM(f.puntos_fatiga) as total_fatiga, MAX(c.artista_img) as img
            FROM canciones c
            JOIN fatiga_actual f ON c.track_id = f.track_id
            GROUP BY c.artista
            HAVING COUNT(c.track_id) >= 3 
            ORDER BY total_fatiga ASC
            LIMIT 5
        ''')
        frios = [{"nombre": r[0], "score": round(r[1], 1), "img": r[2] if r[2] else ""} for r in cursor.fetchall()]

        return {"quemados": quemados, "frios": frios}
    except Exception as e:
        print(f"❌ Error en widgets de artistas: {e}")
        return {"quemados": [], "frios": []}
    finally:
        conexion.close()

@app.get("/buscar")
def buscar_canciones(q: str = ""):
    # Si la búsqueda tiene menos de 2 letras, no hacemos sufrir a la base de datos
    if not q or len(q) < 2:
        return {"resultados": []}
        
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        # Los % son comodines de SQL (busca cualquier cosa que contenga el texto)
        query = f"%{q.lower()}%"
        
        cursor.execute('''
            SELECT c.track_id, c.nombre, c.artista, c.imagen_url, COALESCE(f.overrate, f.puntos_fatiga, 0) as score
            FROM canciones c
            LEFT JOIN fatiga_actual f ON c.track_id = f.track_id
            WHERE LOWER(c.nombre) LIKE ? OR LOWER(c.artista) LIKE ?
            ORDER BY score DESC
            LIMIT 25
        ''', (query, query))
        
        resultados = [{"track_id": r[0], "nombre": r[1], "artista": r[2], "img": r[3], "score": round(r[4],1)} for r in cursor.fetchall()]
        return {"resultados": resultados}
    except Exception as e:
        print(f"❌ Error en búsqueda: {e}")
        return {"resultados": []}
    finally:
        conexion.close()