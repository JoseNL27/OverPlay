## 24/05
    * Añadidas las rutas de la API: /logout y api/me
    * Se le da funcionalidad al login o logout de OverPlay.
    * Funcion async function verificarSesion() en app.js para controlar los logins a través del /me.
    * Añadido el COLD START INTELIGENTE en /callback, capturando los datos del endpoint de spotify /v1/me/top/artists para generar patrones de escucha de nuevos usuarios. Estos datos se guardan en la tabla perfiles_usuario y van ligados a cada user_id. Asimismo, se crea la tabla fatiga_artistas en la que se guarda el estado "Transitorio", "Artista Ancla" y el multiplicador de fatiga de cada artista de los devueltos por el endpoint antes mencionado.
    * Asimismo, se añade el calculo de O.V.R. de los top_tracks (mapear_top_tracks_cold_start) de nuevos usuarios, usando una lógica similar a la de la funcion de mapear_top_artistas_cold_start.
    * Arreglo del endpoint /dashboard para rellenar las tablas vacías en caso de Cold Start.
## 25/05
    * Migración desde Termux completada.
    * Añadido requeriments.txt
## 26/05
    * Comenzada la reestructuración del Backend completamente.
## 28/05
    * Reescritura completa del scout.py
    * Añadido soporte para múltiples usuarios.
    * Añadidos los scripts auth.py y db.py con el objetivo de descentralizar y compartimentar el Backend.
    *Queda pendiente adaptar el resto de los scripts del Backend para aprovechar el nuevo sistema de autenticación y conexión a la base de datos.*
## 31/05
    * Se adapta calcular_fatiga.py para usar el sistema multiuser.
    * Se dejan placeholders en core_matematico.py hasta adaptarlo a las nuevas tablas de la base de datos.
## 7/06
 * **Se modifican las conexiones de la API** con SQLite para realizarlo a través de un Context Manager llamado db_session.
 * **Saneo del código** y funciones inutilizadas en api.py
 * **Implementación de Ngrok** para permitir el acceso a la API desde el exterior.
 * **Se implementa la primera prueba de soporte multiusuario** en api.py en el endpoint /radar.

# frontend-v2

## 12/08
 * **Reescritura completa del Frontend.**
 * **Creada una nueva arquitectura base para el frontend**, separando la aplicación en pantallas independientes y definiendo una estructura clara para la navegación y los distintos componentes de la interfaz.
 * **Creada la nueva estructura HTML de la aplicación** siguiendo una organización semántica y modular, separando las vistas de Home, Playlists, Búsqueda y Perfil.
 * **Rediseñada la Home desde cero** siguiendo una filosofía Mobile-First y MVP, definiendo la jerarquía de información y los principales componentes: saludo, O.V.R., resumen de biblioteca, temperatura musical, joyas olvidadas y acceso al perfil.
 * **Separada la estructura de presentación de la lógica de aplicación**, preparando el frontend para una futura reorganización del código JavaScript y evitando la arquitectura monolítica del frontend anterior.
 * **Iniciada la planificación de los componentes dinámicos** y su futura integración con los datos proporcionados por la API.

## 13/08
 * **Primera iteración para la nueva arquitectura del css** Añadiendo bordes a modo de debug para identificar los componentes.
 * **Añadido el O.V.R. Overview** a la Home.
 * **Cambiada la extensión de changelog.txt por CHANGELOG.md** para seguir el estándar de GitHub.