# OverPlay 🎧📊 
**The Emotion Engine for Spotify**

OverPlay no es solo otra aplicación de estadísticas de Spotify. Es un motor de análisis psicológico musical diseñado para rastrear la **fatiga auditiva**, las rachas tóxicas y el ciclo de vida de tus canciones favoritas. A través de un algoritmo matemático propio, OverPlay entiende cuándo una canción es una obsesión temporal, cuándo se ha convertido en una cicatriz imborrable y cuándo ha ascendido a la categoría de Himno.

## 🚀 Características Principales

* **Multiusuario & Autenticación Segura:** Soporte completo para múltiples testers con sesiones aisladas mediante inyección de dependencias (`ContextoUsuario`) y gestión de cookies.
* **Cold Start Inteligente:** Al iniciar sesión por primera vez, un algoritmo escanea tu historial reciente para construir un perfil base de tolerancias y géneros refugio.
* **Radar de Saturación Dinámico:** Un dashboard visual que clasifica tu biblioteca en estados: *Fresh*, *Warning* y *Burnout*.
* **Gestión de Base de Datos Transaccional:** Uso avanzado de Context Managers (`db_session`) en SQLite para garantizar operaciones atómicas, previniendo fugas de memoria y bloqueos.
* **Delta Logging (Checkpoints):** Sistema de almacenamiento optimizado que solo registra cambios significativos en la fatiga de las canciones, manteniendo la base de datos ultra ligera.
* **Soporte Multi-dispositivo (Ngrok Ready):** Arquitectura de red preparada para testeo móvil en vivo mediante túneles HTTPS.

## 🧠 El Motor Matemático (Core)

El corazón de OverPlay reside en su `core_matematico.py`, que simula el desgaste psicológico utilizando 4 pilares:

1. **ADN y Volatilidad:** La música viral genera impacto rápido pero decae velozmente. La música de nicho es más resistente.
2. **Hábitat Natural:** Penalización por "fricción cognitiva" si escuchas canciones fuera de tu franja horaria habitual (ej. música de club un martes por la mañana).
3. **Fases de Vida (El Bucle):** Multiplicadores dinámicos que diferencian entre la *Luna de Miel* (inmunidad al atracón) y el *Hábito Tóxico* (penalización severa por reproducir el mismo track durante 5 días consecutivos).
4. **Métrica Estrella (OverRate 🔥):** Un valor que cruza la fatiga histórica con la densidad de escuchas de los últimos 7 días. Puede superar los 100 puntos si la saturación es crítica.

## 🛠️ Stack Tecnológico

* **Backend:** Python 3, FastAPI, Uvicorn.
* **Base de Datos:** SQLite (optimizada con `INSERT OR REPLACE` y PK compuestas).
* **Autenticación:** OAuth2 vía Spotipy (Spotify Web API).
* **Frontend:** HTML/CSS/JS Vanilla, Chart.js para visualización de datos.

## ⚙️ Instalación y Configuración

### 1. Clonar el repositorio e instalar dependencias
```bash
git clone [https://github.com/tu-usuario/overplay.git](https://github.com/tu-usuario/overplay.git)
cd overplay
pip install -r requirements.txt