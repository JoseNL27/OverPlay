import sqlite3
import os

def obtener_conexion():
    """
    Devuelve una conexión a la BD con configuración optimizada para alta concurrencia.
    """
    ruta_bd = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'historial.db')
    
    # row_factory=sqlite3.Row permite acceder a las columnas por nombre (ej: row['id'])
    conexion = sqlite3.connect(ruta_bd, timeout=30.0)
    conexion.row_factory = sqlite3.Row
    
    # WAL (Write-Ahead Logging) permite lectura concurrente mientras se escribe
    conexion.execute("PRAGMA journal_mode=WAL;")
    # Cache compartido entre procesos
    conexion.execute("PRAGMA cache_size=-2000;")
    # Preserva datos aunque el programa crashee
    conexion.execute("PRAGMA synchronous=NORMAL;")
    
    return conexion