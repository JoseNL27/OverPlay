import sqlite3
import os

def ejecutar_escaner_profundo():
    ruta_bd = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'historial.db')
    conexion = sqlite3.connect(ruta_bd)
    cursor = conexion.cursor()

    print("\n🕵️‍♂️ INICIANDO ESCÁNER FORENSE DE LA MATRIX (V2)...\n")

    # ========================================================
    # 1. CLONES TEMPORALES (Bug de guardado múltiple)
    # ========================================================
    try:
        cursor.execute('''
            SELECT track_id, played_at, COUNT(*) as cantidad 
            FROM reproducciones 
            GROUP BY track_id, played_at 
            HAVING COUNT(*) > 1
            ORDER BY cantidad DESC
        ''')
        clones = cursor.fetchall()
        print(f"🛑 [NIVEL 1] REPRODUCCIONES CLONADAS EN EL MISMO MILISEGUNDO: {len(clones)} casos")
        for c in clones[:5]: print(f"   -> {c[0]} (Guardada {c[2]} veces en {c[1]})")
    except Exception as e: print("❌ Error:", e)
    print("-" * 60)

    # ========================================================
    # 2. EL MULTIVERSO (Mismo nombre, distinto ID guardado)
    # ========================================================
    try:
        cursor.execute('''
            SELECT LOWER(nombre), COUNT(track_id) as cantidad 
            FROM canciones 
            GROUP BY LOWER(nombre) 
            HAVING COUNT(track_id) > 1
            ORDER BY cantidad DESC
        ''')
        nombres_repetidos = cursor.fetchall()
        print(f"⚠️ [NIVEL 2] CANCIONES CON MISMO NOMBRE PERO DISTINTO ID: {len(nombres_repetidos)} casos")
        for n in nombres_repetidos[:5]: print(f"   -> '{n[0]}' está guardada bajo {n[1]} IDs distintos (Posibles feats/remixes separados).")
    except Exception as e: print("❌ Error:", e)
    print("-" * 60)

    # ========================================================
    # 3. FUSIONES ERRÓNEAS (Picos inhumanos de escuchas)
    # ========================================================
    # Si una canción tiene más de 40 escuchas el mismo día, huele a que 
    # el sistema fusionó varias canciones distintas en un solo track_id por error.
    try:
        cursor.execute('''
            SELECT track_id, DATE(played_at) as dia, COUNT(*) as repros
            FROM reproducciones
            GROUP BY track_id, dia
            HAVING repros > 40
            ORDER BY repros DESC
        ''')
        picos = cursor.fetchall()
        print(f"☣️ [NIVEL 3] FUSIONES TÓXICAS (Picos inhumanos en un solo día): {len(picos)} casos")
        for p in picos[:5]: print(f"   -> {p[0]} sonó {p[2]} veces el {p[1]}. ¿Real o fusión rota?")
    except Exception as e: print("❌ Error:", e)
    print("-" * 60)

    # ========================================================
    # 4. ORFANDAD (Reproducciones o fatiga apuntando a la nada)
    # ========================================================
    try:
        cursor.execute('''
            SELECT COUNT(*) FROM reproducciones r 
            LEFT JOIN canciones c ON r.track_id = c.track_id 
            WHERE c.track_id IS NULL
        ''')
        huerfanas_rep = cursor.fetchone()[0]

        cursor.execute('''
            SELECT COUNT(*) FROM fatiga_actual f 
            LEFT JOIN canciones c ON f.track_id = c.track_id 
            WHERE c.track_id IS NULL
        ''')
        huerfanas_fat = cursor.fetchone()[0]

        print(f"👻 [NIVEL 4] REGISTROS FANTASMA (Orfandad de datos):")
        print(f"   -> {huerfanas_rep} reproducciones apuntan a canciones que ya no existen.")
        print(f"   -> {huerfanas_fat} registros de fatiga apuntan a canciones borradas/pisadas.")
    except Exception as e: print("❌ Error:", e)
    print("-" * 60)

    # ========================================================
    # 5. METADATOS ROTOS (Nombres vacíos, artistas Null)
    # ========================================================
    try:
        cursor.execute('''
            SELECT track_id FROM canciones 
            WHERE nombre IS NULL OR nombre = '' 
               OR artista IS NULL OR artista = ''
               OR track_id NOT LIKE '% - %'
        ''')
        rotas = cursor.fetchall()
        print(f"🗑️ [NIVEL 5] CANCIONES CON METADATOS CORRUPTOS: {len(rotas)} casos")
        for r in rotas[:5]: print(f"   -> ID Roto: {r[0]}")
    except Exception as e: print("❌ Error:", e)
    print("\n✅ ESCÁNER FINALIZADO. Ningún dato ha sido modificado.")
    
    conexion.close()

if __name__ == "__main__":
    ejecutar_escaner_profundo()