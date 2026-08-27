## 24/05
* **Añadidas las rutas de la API: /logout y api/me**
* **Se le da funcionalidad al login o logout de OverPlay.**
* **Funcion async function verificarSesion() en app.js para controlar los logins a través del /me.**
* **Añadido el COLD START INTELIGENTE en /callback**, capturando los datos del endpoint de spotify /v1/me/top/artists para generar patrones de escucha de nuevos usuarios. Estos datos se guardan en la tabla perfiles_usuario y van ligados a cada user_id. Asimismo, se crea la tabla fatiga_artistas en la que se guarda el estado "Transitorio", "Artista Ancla" y el multiplicador de fatiga de cada artista de los devueltos por el endpoint antes mencionado.
* Asimismo, **se añade el calculo de O.V.R. de los top_tracks** (mapear_top_tracks_cold_start) de nuevos usuarios, usando una lógica similar a la de la funcion de mapear_top_artistas_cold_start.
* **Arreglo del endpoint /dashboard para rellenar las tablas vacías en caso de Cold Start.**

## 25/05
* **Migración desde Termux completada.**
* **Añadido requeriments.txt**

## 26/05
* **Comenzada la reestructuración del Backend completamente.**

## 28/05
* **Reescritura completa del scout.py**
* **Añadido soporte para múltiples usuarios.**
* **Añadidos los scripts auth.py y db.py** con el objetivo de descentralizar y compartimentar el Backend. 
*Queda pendiente adaptar el resto de los scripts del Backend para aprovechar el nuevo sistema de autenticación y conexión a la base de datos.*

## 31/05
* **Se adapta calcular_fatiga.py para usar el sistema multiuser.**
* **Se dejan placeholders en core_matematico.py hasta adaptarlo a las nuevas tablas de la base de datos.**

## 7/06
* **Se modifican las conexiones de la API con SQLite** para realizarlo a través de un Context Manager llamado db_session.
* **Saneo del código y funciones inutilizadas en api.py**
* **Implementación de Ngrok** para permitir el acceso a la API desde el exterior.
* **Se implementa la primera prueba de soporte multiusuario** en api.py en el endpoint /radar.

# frontend-v2

## 11/08
 * **Reescritura completa del Frontend.**
 * **Creada una nueva arquitectura base para el frontend**, separando la aplicación en pantallas independientes y definiendo una estructura clara para la navegación y los distintos componentes de la interfaz.
 * **Creada la nueva estructura HTML de la aplicación** siguiendo una organización semántica y modular, separando las vistas de Home, Playlists, Búsqueda y Perfil.
 * **Rediseñada la Home desde cero** siguiendo una filosofía Mobile-First y MVP, definiendo la jerarquía de información y los principales componentes: saludo, O.V.R., resumen de biblioteca, temperatura musical, joyas olvidadas y acceso al perfil.
 * **Separada la estructura de presentación de la lógica de aplicación**, preparando el frontend para una futura reorganización del código JavaScript y evitando la arquitectura monolítica del frontend anterior.
 * **Iniciada la planificación de los componentes dinámicos** y su futura integración con los datos proporcionados por la API.

## 12/08
 * **Primera iteración para la nueva arquitectura del css** Añadiendo bordes a modo de debug para identificar los componentes.
 * **Añadido el O.V.R. Overview** a la Home.
 * **Cambiada la extensión de changelog.txt por CHANGELOG.md** para seguir el estándar de GitHub.

## 13/08
 * **Reestructuración del componente "Resumen de tu biblioteca"** dentro del Overview, incluyendo la estructura de la gráfica, leyenda y controles de rango temporal.
 * **Creada la estructura HTML y CSS inicial del modal de detalle**, preparado para mostrar información tanto de canciones como de artistas.
 * **Reestructuración de los widgets del frontend** mediante una clase común para establecer una base de diseño y estructura compartida entre los distintos componentes.
 * **Comienzo de la reescritura del código JavaScript**
 * **Añadida la funcionalidad de navegación entre pantallas** mediante la barra de navegación inferior.
 * **La nueva rama (frontend-v2) se convierte en la rama principal** y la antigua (main) se renombra a legacy.

## 14/08
 * **Hecha la estructura de la pantalla de Playlist** usando placeholders para maquetación.
 * **Hecha la estructura de la pantalla de Búsqueda** usando placeholders para maquetación.
 * **Hecha la estructura de la pantalla de Configuración** usando placeholders para maquetación.

## 17/08
 * **Reestructuracón de todo el CSS en carpetas**, siguiendo la estructura:
    - base
    - layout
    - components
    - screens
    - debug
 * **Se elimina styles.css y desing-legacy.css**
 * **Añadida tipografía provisional CSS**
 * **Creado el modal de playlist.**
 * **Reescritura del código CSS del Modal** para hacerlo reutilizable.
 * **Eliminado legacy-index.html**

## 18/08
 * **Algunos tests minoritarios en .overview-widget.css**

## 19/08
 * **Se convierte la clase playlist-card en un componente global reutilizable** (media-card.css)
 * **Diseñado el widget de musical-temperature.**
 * **Diseñado el widget de perfil (profile-widget)**
 * **Introducida la funcionalidad de "Insights"**, será desarrollada en profundidad posteriormente.
 * **Diseñado el widget de "Featured Insight"** en sustitución de "Forgotten Gem".

## 20/08
* **Configuración de las variables globales del CSS**
* **Añadida una versión temprana del diseño del componente .media-card**

## 24/08
* **Añadido Background general**
* **Añadido diseño blur a header y navbar**
* **Refinado el diseño del componente .widget**
* **Añadido el diseño de .featured-insight**

## 25/08
* **Refinamiento del componenete .widget y .featured-insight.**
* **Diseño de nav-bar terminado.**
* **Añadido host.py para acceder a la app en local.**
* **Completado el diseño de .musical-temperature.**
* **Terminado el diseño del componente media-card.**

## 26/08
* **Añadido diseño global para todos los button.**
* **Diseño del widget profile-widget terminado.**
* **Añadido logo beta de OverPlay**

## 27/08
* **Añadido manifest.json para que OverPlay sea PWA**
* **Añadidos iconos de la app**
* **Nuevo diseño del widget .overview**
* **Creado el componente global de label**
* **Creado el componente global time-range-buttons**

 
