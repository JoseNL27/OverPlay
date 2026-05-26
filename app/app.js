const API_URL = "";

let chartInstancia = null;
let pantallaAnterior = "dashboard";
let ecosistemaInstancia = null;

// ==========================================
// 🛡️ EL GUARDIÁN DE LA SESIÓN
// ==========================================
async function verificarSesion() {
    try {
        const respuesta = await fetch('/api/me');
        const pantallaBienvenida = document.getElementById('pantalla-bienvenida');

        if (respuesta.ok) {
            // 🟢 CÓDIGO 200: El usuario tiene la cookie y está en la DB
            const datos = await respuesta.json();

            // 1. Escondemos la pantalla de bienvenida de golpe
            pantallaBienvenida.classList.add('hidden');

            // 2. Inyectamos su nombre real en el Perfil
            // (Asegúrate de que el <h2> o <span> de tu perfil tenga id="nombre-usuario")
            const elementoNombre = document.getElementById('nombre-usuario');
            if (elementoNombre) {
                elementoNombre.textContent = datos.nombre;
            }

            console.log(`[🛰️] Sesión confirmada. Bienvenido, ${datos.nombre}`);

            // 3. AQUÍ arrancarías el resto del Dashboard (cargar playlists, etc.)
            // cargarDatosDashboard(); 

        } else {
            // 🔴 CÓDIGO 401: No hay cookie o caducó
            // Quitamos el candado de la bienvenida para que cubra la pantalla
            pantallaBienvenida.classList.remove('hidden');
            console.log("[🚫] No hay sesión activa. Mostrando O.V.R. Gate.");
        }
    } catch (error) {
        console.error("❌ Error de red comprobando la sesión:", error);
        // Si el backend está apagado, mostramos la bienvenida por seguridad
        document.getElementById('pantalla-bienvenida').classList.remove('hidden');
    }
}

// Ejecutamos al guardián nada más cargar la página
window.onload = () => {
    verificarSesion();
};

// 🚀 ARRANQUE DE LA APLICACIÓN
inicializarApp();

function inicializarApp() {
    console.log("🚀 Iniciando OverPlay de forma segura...");

    // 1. Activamos la botonera global
    bindGlobalEvents();
    console.log("✅ Sistema de navegación mapeado");

    // 2. Cargamos el Dashboard inicial con escudo anti-crasheos
    try {
        cargarDashboard();
    } catch (error) {
        console.error("❌ El dashboard ha crasheado por:", error);
    }
}

/* =========================================================
   SISTEMA DE NAVEGACIÓN Y EVENTOS GLOBALES
========================================================= */
function bindGlobalEvents() {
    console.log("🔗 Sincronizando los cables del Nav-Bar...");

    const navInicio = document.getElementById("nav-inicio");
    const navPlaylists = document.getElementById("nav-playlists");
    const navBuscar = document.getElementById("nav-buscar");
    const navPerfil = document.getElementById("nav-perfil");

    // Evento: INICIO / DASHBOARD
    if (navInicio) {
        navInicio.onclick = () => {
            console.log("🏠 Moviendo interfaz al Dashboard...");
            mostrarPantalla("pantalla-dashboard");
            cargarDashboard();
        };
    }

    // Evento: PLAYLISTS
    if (navPlaylists) {
        navPlaylists.onclick = () => {
            console.log("🎵 Abriendo gestor de Playlists...");
            mostrarPantalla("pantalla-playlists");
            cargarPlaylists();
        };
    }

    // Evento: BUSCADOR
    if (navBuscar) {
        navBuscar.onclick = () => {
            console.log("🔍 Activando Escáner Global...");
            mostrarPantalla("pantalla-buscar");
            setHeader("Base de Datos", "Escáner manual");
            // Auto-focus para que el teclado del móvil salte al instante
            setTimeout(() => {
                const inputBuscador = document.getElementById("input-buscador");
                if (inputBuscador) inputBuscador.focus();
            }, 100);
        };
    }

    // Evento: PERFIL + CONFIGURACIÓN (La pestaña 'Tú')
    if (navPerfil) {
        navPerfil.onclick = () => {
            console.log("👤 Accediendo al perfil del operador...");
            mostrarPantalla("vista-perfil");
            setHeader("Perfil", "Configuración del núcleo");
        };
    }
}

// Intercambiador estético de botones activos en el Nav-Bar
function actualizarNav(idActivo) {
    document.querySelectorAll(".nav-item").forEach(item => {
        item.classList.remove("activa");
    });
    const item = document.getElementById(idActivo);
    if (item) item.classList.add("activa");
}

// El motor principal que muestra y oculta las pantallas sin conflictos
function mostrarPantalla(idObjetivo) {
    // Escaneamos todas las secciones de pantallas posibles
    const pantallas = document.querySelectorAll("section.pantalla, #vista-perfil");

    // Reseteo total: apagamos y añadimos el candado 'hidden' a todo
    pantallas.forEach(p => {
        p.style.display = "none";
        p.classList.add("hidden");
        p.classList.remove("activa");
    });

    // Encendemos quirúrgicamente la pantalla que queremos ver
    const pantallaActiva = document.getElementById(idObjetivo);
    if (pantallaActiva) {
        pantallaActiva.style.display = "block";
        pantallaActiva.classList.remove("hidden");
        pantallaActiva.classList.add("activa");
    }

    // 🎯 MAPEO AUTOMÁTICO DE BOTONES (Vincula la pantalla con su icono del menú)
    if (idObjetivo === "pantalla-dashboard") {
        actualizarNav("nav-inicio");
    } else if (idObjetivo === "pantalla-playlists" || idObjetivo === "pantalla-analisis") {
        actualizarNav("nav-playlists");
    } else if (idObjetivo === "pantalla-buscar") {
        actualizarNav("nav-buscar");
    } else if (idObjetivo === "vista-perfil") {
        actualizarNav("nav-perfil");
    }
}

/* =========================================================
   HELPERS UI
========================================================= */
function setHeader(titulo, subtitulo = "") {
    const tituloEl = document.getElementById("app-titulo");
    const subEl = document.getElementById("app-subtitulo");
    if (tituloEl) tituloEl.textContent = titulo;
    if (subEl) subEl.textContent = subtitulo;
}

function escaparComillas(str) {
    return str ? str.replace(/'/g, "\\'") : "Desconocido";
}

/* =========================================================
   DASHBOARD PRINCIPAL (Saneado)
========================================================= */

async function cargarDashboard() {
    try {
        mostrarPantalla("pantalla-dashboard");
        cambiarRangoRadar('MAX');
        cargarJoyaDelDia();

        // 🚀 1. CARGAMOS WIDGETS PREMIUM (Sin fantasmas)
        await cargarWidgetsDashboard();

        // 🚀 2. CARGAMOS BANNER DE SATURACIÓN
        const res = await fetch("/dashboard");
        if (res.ok) {
            const data = await res.json();
            const banner = document.getElementById("banner-saturacion");

            if (banner && data.fatiga_semanal !== undefined) {
                const ptsSemanales = data.fatiga_semanal || 0;
                const estadoSemanal = data.estado_semanal || "FRESH";

                const getEstiloBanner = (p) => {
                    if (p < 30) return { color: "#4ade80", glow: "rgba(74,222,128,0.4)" };
                    if (p < 65) return { color: "#ffb347", glow: "rgba(255,179,71,0.4)" };
                    return { color: "#ff4d61", glow: "rgba(255,77,97,0.4)" };
                };
                const est = getEstiloBanner(ptsSemanales);

                banner.innerHTML = `
                    <div class="banner-saturacion">
                        <div class="banner-header">
                            <span class="banner-title">SATURACIÓN (ÚLTIMOS 7 DÍAS)</span>
                            <span class="banner-status" style="color: ${est.color}; text-shadow: 0 0 10px ${est.glow};">${estadoSemanal}</span>
                        </div>
                        <div class="banner-body">
                            <div class="banner-score" style="color: ${est.color}; text-shadow: 0 0 20px ${est.glow};">${ptsSemanales} <span style="font-size:16px; color:var(--text-fade);">pts</span></div>
                            <div class="banner-bar-bg">
                                <div class="banner-bar-fill" style="width: ${Math.min(ptsSemanales, 100)}%; background: ${est.color}; box-shadow: 0 0 15px ${est.glow};"></div>
                            </div>
                        </div>
                    </div>
                `;
            }
        }
    } catch (error) {
        console.error("❌ Error cargando el dashboard:", error);
    }
}

/* =========================================================
   WIDGETS PREMIUM DEL DASHBOARD (V6.1)
========================================================= */

async function cargarWidgetsDashboard() {
    try {
        const [resArtistas, resCanciones] = await Promise.all([
            fetch('/widgets/artistas'),
            fetch('/widgets/canciones')
        ]);

        if (!resArtistas.ok || !resCanciones.ok) throw new Error("Fallo en la API");

        const dataArtistas = await resArtistas.json();
        const dataCanciones = await resCanciones.json();

        inyectarWidgetArtistas('widget-artistas-quemados', dataArtistas.quemados, 'quemado', 'OR');
        inyectarWidgetArtistas('widget-artistas-frios', dataArtistas.frios, 'frio', 'pts');

        inyectarWidgetCanciones('widget-en-racha', dataCanciones.racha, 'racha', 'OR');
        inyectarWidgetCanciones('widget-quemadas', dataCanciones.quemadas, 'quemada', 'pts');
        inyectarWidgetCanciones('widget-olvidadas', dataCanciones.olvidadas, 'olvidada', 'Pico');
        inyectarWidgetRecientes('widget-recientes', dataCanciones.recientes);

    } catch (e) {
        console.error("❌ Error ensamblando widgets:", e);
    }
}

function inyectarWidgetArtistas(idContenedor, lista, claseEstilo, sufijoPuntos) {
    const div = document.getElementById(idContenedor);
    if (!div) return;

    div.innerHTML = "";
    if (!lista || lista.length === 0) {
        div.innerHTML = `<div style="color:#666; font-size:12px; padding:10px;">Escáner vacío.</div>`;
        return;
    }

    lista.forEach(art => {
        const imgSegura = art.img || `https://ui-avatars.com/api/?name=${encodeURIComponent(art.nombre)}&background=222&color=fff&bold=true`;
        div.innerHTML += `
            <div class="widget-neon-artista ${claseEstilo}" onclick="abrirDetalleArtista('${escaparComillas(art.nombre)}')">
                <img src="${imgSegura}" alt="${art.nombre}" onerror="this.src='https://ui-avatars.com/api/?name=X&background=222&color=fff'">
                <div class="widget-text-nombre">${art.nombre}</div>
                <div class="widget-text-score">${art.score} ${sufijoPuntos}</div>
            </div>
        `;
    });
}

function inyectarWidgetCanciones(idContenedor, lista, claseEstilo, sufijoPuntos) {
    const div = document.getElementById(idContenedor);
    if (!div) return;

    div.innerHTML = "";
    if (!lista || lista.length === 0) {
        div.innerHTML = `<div style="color:#666; font-size:12px; padding:10px;">Escáner vacío.</div>`;
        return;
    }

    lista.forEach(song => {
        const imgSegura = song.img || `https://ui-avatars.com/api/?name=${encodeURIComponent(song.nombre)}&background=222&color=fff&bold=true`;
        const idSeguro = `${escaparComillas(song.nombre)} - ${escaparComillas(song.artista)}`;

        div.innerHTML += `
            <div class="widget-neon-cancion ${claseEstilo}" onclick="abrirDetalle('${idSeguro}')">
                <img src="${imgSegura}" alt="${song.nombre}" onerror="this.src='https://ui-avatars.com/api/?name=X&background=222&color=fff'">
                <div class="widget-text-nombre">${song.nombre}</div>
                <div class="widget-text-score">${song.score} ${sufijoPuntos}</div>
            </div>
        `;
    });
}

function inyectarWidgetRecientes(idContenedor, lista) {
    const div = document.getElementById(idContenedor);
    if (!div) return;

    div.innerHTML = "";
    if (!lista || lista.length === 0) {
        div.innerHTML = `<div style="color:#666; font-size:12px; padding:10px;">Aún no hay historial.</div>`;
        return;
    }

    lista.forEach(song => {
        const imgSegura = song.img || `https://ui-avatars.com/api/?name=${encodeURIComponent(song.nombre)}&background=222&color=fff&bold=true`;
        const idSeguro = `${escaparComillas(song.nombre)} - ${escaparComillas(song.artista)}`;

        // 🎨 LÓGICA DE ESCANEO: Asignamos color según su toxicidad
        let claseEstilo = "fresh"; // Por defecto Verde
        if (song.score >= 65) claseEstilo = "burnout"; // Rojo
        else if (song.score >= 30) claseEstilo = "warning"; // Naranja

        div.innerHTML += `
            <div class="widget-neon-cancion ${claseEstilo}" onclick="abrirDetalle('${idSeguro}')">
                <img src="${imgSegura}" alt="${song.nombre}" onerror="this.src='https://ui-avatars.com/api/?name=X&background=222&color=fff'">
                <div class="widget-text-nombre">${song.nombre}</div>
                <div class="widget-text-score">${song.score} OR</div>
            </div>
        `;
    });
}

function abrirDetalleArtista(nombreArtista) {
    console.log(`Próximamente: Abriendo HUB de ${nombreArtista}...`);
}

/* =========================================================
   RADAR DINÁMICO (CREACIÓN + ANIMACIÓN)
========================================================= */
async function cambiarRangoRadar(rango) {
    // 1. Cambiamos el color del botón activo
    const botones = document.querySelectorAll(".btn-rango");
    botones.forEach(btn => {
        btn.classList.remove("activo");
        if (btn.innerText === rango) btn.classList.add("activo");
    });

    try {
        // 2. Pedimos los datos frescos a Python
        const res = await fetch(`/radar?rango=${rango}`);
        const ecoData = await res.json();

        const totalTracks = ecoData.fresh + ecoData.warning + ecoData.burnout;
        const textCenter = document.getElementById("radar-total");
        if (textCenter) textCenter.innerHTML = `${totalTracks} <span>TRACKS</span>`;

        const ctxEco = document.getElementById("grafica-ecosistema");
        if (!ctxEco) return;

        // 3. LA MAGIA: Si ya existe, se anima. Si no, se crea.
        if (ecosistemaInstancia) {
            ecosistemaInstancia.data.datasets[0].data = [ecoData.fresh, ecoData.warning, ecoData.burnout];
            ecosistemaInstancia.update(); // Animación fluida de colores
        } else {
            // Creación desde cero para la primera vez
            ecosistemaInstancia = new Chart(ctxEco.getContext("2d"), {
                type: 'doughnut',
                data: {
                    labels: ['FRESH', 'WARNING', 'OVERPLAYED'],
                    datasets: [{
                        data: [ecoData.fresh, ecoData.warning, ecoData.burnout],
                        backgroundColor: ['#4ade80', '#ffb347', '#ff4d61'],
                        borderWidth: 2,
                        borderColor: '#151517', // Color del fondo de tu UI
                        hoverOffset: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '75%', // Lo hace súper fino
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: 'rgba(21, 21, 23, 0.95)',
                            titleFont: { size: 12, family: 'Courier New' },
                            bodyFont: { size: 14, weight: 'bold' },
                            padding: 10,
                            callbacks: {
                                label: function (context) {
                                    return ` ${context.raw} temas`;
                                }
                            }
                        }
                    }
                }
            });
        }
    } catch (error) {
        console.error("❌ Error actualizando el radar:", error);
    }
}

function renderWidget(elementId, canciones) {
    const div = document.getElementById(elementId);
    if (!div) return;
    div.innerHTML = "";

    // 🛡️ ESCUDO ANTI-CRASHEOS: Si la API falla, no rompemos la web
    if (!canciones || !Array.isArray(canciones) || canciones.length === 0) {
        div.innerHTML = `
            <div style="padding: 10px; color: #b3b3b3; font-size: 12px; font-style: italic; background: rgba(255,255,255,0.02); border-radius: 6px;">
                Recopilando datos...
            </div>
        `;
        return;
    }

    canciones.slice(0, 4).forEach(c => {
        // Usamos el track_id exacto que nos manda el backend para que la gráfica no falle
        const idSeguro = c.track_id || `${escaparComillas(c.nombre)} - ${escaparComillas(c.artista)}`;

        div.innerHTML += `
            <div class="mini-card" onclick="abrirDetalle('${idSeguro}')">
                <img src="${c.imagen || 'https://via.placeholder.com/55'}" class="mini-portada">
                <div class="mini-info">
                    <div class="mini-titulo">${c.nombre}</div>
                    <div class="mini-artista">${c.artista}</div>
                </div>
            </div>
        `;
    });
}

/* =========================================================
   ZONA PLAYLISTS (Navegación arreglada)
========================================================= */

async function cargarPlaylists() {
    try {
        mostrarPantalla("pantalla-playlists");
        setHeader("Análisis", "Tus playlists de Spotify");
        pantallaAnterior = "dashboard";

        const contenedor = document.getElementById("lista-playlists");
        if (!contenedor) return;

        contenedor.innerHTML = `<div style="padding: 20px; text-align: center; color: #b3b3b3;">Conectando con Spotify... 📡</div>`;

        const res = await fetch("/playlists");
        const playlists = await res.json();

        contenedor.innerHTML = "";
        playlists.forEach(pl => {
            const nombreSeguro = pl.nombre ? pl.nombre.replace(/'/g, "\\'") : "Playlist";
            contenedor.innerHTML += `
                <div class="playlist-card" onclick="analizarPlaylist('${pl.id}', '${nombreSeguro}')">
                    <img src="${pl.imagen || 'https://via.placeholder.com/55'}" class="playlist-img">
                    <div class="playlist-info">
                        <div class="playlist-nombre">${pl.nombre}</div>
                        <div class="playlist-tracks">${pl.total_tracks} temas</div>
                    </div>
                </div>
            `;
        });
    } catch (error) {
        console.error("❌ Error en playlists:", error);
    }
}

async function analizarPlaylist(id, nombre) {
    try {
        mostrarPantalla("pantalla-analisis");
        setHeader("Analizando", nombre);
        pantallaAnterior = "playlists";

        const contenedor = document.getElementById("resultados-playlist");
        if (!contenedor) return;

        contenedor.innerHTML = `<div style="padding: 20px; text-align: center; color: #b3b3b3;">Calculando niveles de fatiga... ☢️</div>`;

        const res = await fetch(`/playlist/${id}`);
        let canciones = await res.json();

        // 🚀 RECUPERADO: Ordenar de más a menos fatiga
        canciones.sort((a, b) => b.puntos_fatiga - a.puntos_fatiga);

        function getDetallesFatiga(pts) {
            if (pts < 30) return { color: "#4ade80", label: "FRESH", glow: "rgba(74,222,128,0.4)" };
            if (pts < 65) return { color: "#ffb347", label: "WARNING", glow: "rgba(255,179,71,0.4)" };
            if (pts < 100) return { color: "#ff4d61", label: "OVERPLAYED", glow: "rgba(255,77,97,0.4)" };
            return { color: "#a855f7", label: "OVERLOAD", glow: "rgba(168,85,247,0.4)" };
        }

        contenedor.innerHTML = "";
        canciones.forEach(c => {
            const idSeguro = c.track_id;
            const info = getDetallesFatiga(c.puntos_fatiga);
            const anchoBarra = Math.min(c.puntos_fatiga, 100);

            contenedor.innerHTML += `
                <div class="card-cancion">
                    <div class="card-main-content" onclick="abrirDetalle('${idSeguro}')">
                        <img src="${c.imagen || 'https://via.placeholder.com/55'}" class="mini-portada">
                        <div class="card-info">
                            <div class="mini-titulo">${c.nombre}</div>
                            <div class="mini-artista">${c.artista}</div>
                            <div class="card-meta">
                                <span class="badge-estado" style="background: ${info.glow}; color: ${info.color}">
                                    ${info.label}
                                </span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card-acciones">
                        <div class="puntuacion-container">
                            <span class="puntuacion-badge" style="color: ${info.color}">
                                ${c.puntos_fatiga.toFixed(0)}
                            </span>
                        </div>
                        <div class="botones-feedback" style="display: flex; gap: 8px;">
                            <button class="mini-ovr-btn amnesty" onclick="event.stopPropagation(); registrarInputOVR('${idSeguro}', 'AMNESTY')" title="Amnistía (Bajar O.V.R.)">
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                                </svg>
                            </button>
                            
                            <button class="mini-ovr-btn overdrive" onclick="event.stopPropagation(); registrarInputOVR('${idSeguro}', 'OVERDRIVE')" title="Overdrive (Forzar Fatiga)">
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M13 5l7 7-7 7M5 5l7 7-7 7" transform="rotate(-90 12 12)"/>
                                </svg>
                            </button>
                        </div>
                    </div>

                    <div class="fatiga-bar-container">
                        <div class="fatiga-bar-fill" style="width: ${anchoBarra}%; background: linear-gradient(90deg, transparent, ${info.color}); box-shadow: 0 0 10px ${info.color}66;"></div>
                    </div>
                </div>
            `;
        });
    } catch (e) {
        console.error("❌ Error al analizar la playlist:", e);
    }
}
/*
function pintarCanciones(canciones) {

    const div =
        document.getElementById("resultados-playlist");

    div.innerHTML = "";

    canciones
        .sort((a, b) => b.puntos - a.puntos)
        .forEach(c => {

            const idSeguro =
                `${escaparComillas(c.nombre)} - ${escaparComillas(c.artista)}`;

            const porcentaje =
                Math.min(c.puntos, 100);

            div.innerHTML += `
                <div class="card-cancion"
                     onclick="abrirDetalle('${idSeguro}')">

                    <div class="card-portada">
                        <img src="${c.imagen}">
                        <div class="badge-fatiga ${c.color}"></div>
                    </div>

                    <div class="card-info">

                        <div class="card-top">
                            <div class="card-titulo">${c.nombre}</div>
                            <div class="card-artista">${c.artista}</div>
                        </div>

                        <div class="card-bottom">

                            <div class="progress-bar-container">
                                <div class="progress-bar-fill ${c.color}"
                                     style="width:${porcentaje}%">
                                </div>
                            </div>

                            <div class="card-puntos">
                                ${c.puntos}
                            </div>

                        </div>

                    </div>

                    <div class="card-acciones">

                        <button onclick="mandarFeedback('${idSeguro}','like',event)">
                            👍
                        </button>

                        <button onclick="mandarFeedback('${idSeguro}','dislike',event)">
                            👎
                        </button>

                    </div>

                </div>
            `;
        });
}
*/

/* =========================================================
   LA JOYA DEL DÍA
========================================================= */
async function cargarJoyaDelDia() {
    try {
        const res = await fetch("/joya");
        const joya = await res.json();
        const contenedor = document.getElementById("contenedor-joya");

        if (!contenedor) return;

        // Si no hay joya que cumpla los requisitos hoy, ocultamos la sección y listo
        if (joya.error) {
            contenedor.innerHTML = "";
            return;
        }

        contenedor.innerHTML = `
            <div class="joya-card" onclick="abrirDetalle('${joya.track_id}')">
                <img src="${joya.imagen_url}" class="joya-img">
                <div class="joya-info">
                    <div class="joya-label">💎 LA JOYA DEL DÍA</div>
                    <div class="joya-titulo">${joya.nombre}</div>
                    <div class="joya-artista">${joya.artista}</div>
                </div>
            </div>
        `;
    } catch (error) {
        console.error("❌ Error cargando la joya:", error);
    }
}
/* =========================================================
   FEEDBACK
========================================================= */

async function mandarFeedback(trackId, accion, event) {

    event.stopPropagation();

    try {

        await fetch(`${API_URL}/feedback`, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                track_id: trackId,
                accion
            })
        });

    } catch (error) {

        console.error(error);
    }
}

/* =========================================================
   DETALLE CANCION
========================================================= */

// Variable global para que la gráfica no se duplique y pete

let chartOR = null;
let chartPlays = null;

async function abrirDetalle(trackId) {
    try {
        mostrarPantalla("pantalla-detalle");
        const contenedor = document.getElementById("pantalla-detalle");
        contenedor.innerHTML = `<div class="loader">Desencriptando metadatos V2... ⏳</div>`;

        const res = await fetch(`/cancion/detalle/${encodeURIComponent(trackId)}`);
        const data = await res.json();

        const meta = data.meta;
        const stats = data.stats;

        // --- 🧠 CÁLCULO DEL ESTADO EMOCIONAL ---
        let estadoEmocional = { texto: "FRESH", color: "#4ade80", glow: "rgba(74,222,128,0.4)" };
        if (stats.or_actual >= 80) estadoEmocional = { texto: "QUEMADÍSIMA ☢️", color: "#a855f7", glow: "rgba(168,85,247,0.4)" };
        else if (stats.or_actual >= 60) estadoEmocional = { texto: "ZONA DE PELIGRO 🔥", color: "#ff4d61", glow: "rgba(255,77,97,0.4)" };
        else if (stats.or_actual >= 30) estadoEmocional = { texto: "EN ROTACIÓN 🔄", color: "#ffb347", glow: "rgba(255,179,71,0.4)" };
        if (stats.max_gap_dias > 14 && stats.or_actual < 40) estadoEmocional = { texto: "ENFRIÁNDOSE 🧊", color: "#60a5fa", glow: "rgba(96,165,250,0.4)" };

        // --- 🎤 ENSAMBLAR CHIPS DE ARTISTAS ---
        let artistasHTML = `<span class="colab-chip main-artist" onclick="abrirDetalleArtista('${escaparComillas(meta.artista)}')">👑 ${meta.artista}</span>`;
        if (meta.colaboradores) {
            const colabs = meta.colaboradores.split(',');
            colabs.forEach(c => {
                artistasHTML += `<span class="colab-chip" onclick="abrirDetalleArtista('${escaparComillas(c.trim())}')">${c.trim()}</span>`;
            });
        }

        contenedor.innerHTML = `
            <div class="detalle-overlay" onclick="cerrarDetalle()"></div>
            <div class="detalle-panel">
                <button class="btn-close" style="z-index: 10;" onclick="cerrarDetalle()">✕</button>
                
                <div class="detalle-header-blur" style="background-image: url('${meta.imagen_url || 'https://via.placeholder.com/200'}')"></div>
                
                <div class="detalle-header-content">
                    <img src="${meta.imagen_url || 'https://via.placeholder.com/200'}" class="detalle-portada-v2">
                    <div class="detalle-titulo-v2">${meta.nombre}</div>
                    <div class="artistas-chips">${artistasHTML}</div>
                </div>

                <div class="tabs-container">
                    <button class="tab-btn active" onclick="cambiarPestanyaDetalle('info', this)">INFO</button>
                    <button class="tab-btn" onclick="cambiarPestanyaDetalle('overrating', this)">OVERRATING</button>
                </div>

                <div id="tab-info" class="tab-content active">
                    <div class="hud-grid">
                        <div class="hud-box">
                            <span class="hud-label">PRIMERA ESCUCHA</span>
                            <span class="hud-value" style="font-size:14px">${stats.descubrimiento}</span>
                        </div>
                        <div class="hud-box">
                            <span class="hud-label">TOTAL REPROS</span>
                            <span class="hud-value">${stats.total_escuchas}</span>
                        </div>
                        <div class="hud-box">
                            <span class="hud-label">AÑO</span>
                            <span class="hud-value">${meta.año}</span>
                        </div>
                        <div class="hud-box">
                            <span class="hud-label">POPULARIDAD</span>
                            <span class="hud-value">${meta.popularidad}<span style="font-size:10px">/100</span></span>
                        </div>
                    </div>
                    <div class="chart-card" style="margin-top:15px">
                        <div class="chart-title">HISTORIAL DE REPRODUCCIONES PÚRAS</div>
                        <div class="chart-container"><canvas id="grafica-repros"></canvas></div>
                    </div>
                </div>
<div class="ovr-controls-wrapper">
    <button class="ovr-btn overdrive" onclick="registrarInputOVR('${trackId}', 'OVERDRIVE')">
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M13 5l7 7-7 7M5 5l7 7-7 7" transform="rotate(-90 12 12)"/>
                                </svg>
                                OVERDRIVE
                            </button>
                            
                            <button class="ovr-btn amnesty" onclick="registrarInputOVR('${trackId}', 'AMNESTY')">
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                                </svg>
                                AMNISTÍA
                            </button>
                        </div>
                <div id="tab-overrating" class="tab-content">
                    <div class="hud-grid">
                        <div class="hud-box highlight" style="grid-column: span 2; border-color: ${estadoEmocional.color}">
                            <span class="hud-label">ESTADO EMOCIONAL</span>
                            <span class="hud-value" style="color: ${estadoEmocional.color}; text-shadow: 0 0 10px ${estadoEmocional.glow}">${estadoEmocional.texto}</span>
                        </div>
                        

                        <div class="hud-box">
                            <span class="hud-label">O.V.R. ACTUAL</span> <span class="hud-value neon-green">${stats.or_actual} <span style="font-size:12px">pts</span></span>
                        </div>
                        <div class="hud-box alert">
                            <span class="hud-label">PICO DE TRAUMA</span>
                            <span class="hud-value neon-red">${stats.pico_trauma}</span>
                            <span class="hud-sub">${stats.fecha_pico}</span>
                        </div>
                       <div class="hud-box">
    <span class="hud-label">MAX RACHA ESCUCHA</span>
    <span class="hud-value">${stats.max_racha_dias} <span style="font-size:12px">días</span></span>
    <span class="hud-sub" style="color: var(--primary);">${stats.racha_contexto}</span>
</div>

<div class="hud-box">
    <span class="hud-label">MAX ABSTINENCIA</span>
    <span class="hud-value">${stats.max_gap_dias} <span style="font-size:12px">días</span></span>
    <span class="hud-sub" style="color: var(--warning);">${stats.gap_contexto}</span>
</div>
                    </div>
                    <div class="chart-card" style="margin-top:15px">
                        <div class="chart-title">TRACKING TEMPORAL DE SATURACIÓN</div>
                        <div class="chart-container"><canvas id="grafica-fatiga"></canvas></div>
                    </div>
                </div>
            </div>
        `;

        // Renderizamos ambos gráficos
        renderizarGraficoBarras(data.grafica_repros);
        renderizarGraficaIronMan(data.grafica_or.map(p => p.x), data.grafica_or.map(p => p.y));

    } catch (e) {
        console.error("❌ Error en V2:", e);
        document.getElementById("pantalla-detalle").innerHTML = `<div class="loader" style="color:red;">Fallo de conexión.</div>`;
    }
}

// Lógica de Pestañas
window.cambiarPestanyaDetalle = function (tab, btn) {
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(`tab-${tab}`).classList.add('active');
    btn.classList.add('active');
}

function renderizarGraficoBarras(datos) {
    const ctx = document.getElementById("grafica-repros");
    if (!ctx) return;
    if (chartPlays) chartPlays.destroy();

    const etiquetas = datos.map(d => d.x);
    const valores = datos.map(d => d.y);

    // Degradado premium para las barras
    let gradiente = ctx.getContext("2d").createLinearGradient(0, 0, 0, 300);
    gradiente.addColorStop(0, "#4ade80"); // Verde brillante arriba
    gradiente.addColorStop(1, "rgba(74, 222, 128, 0.1)"); // Transparente abajo

    chartPlays = new Chart(ctx.getContext("2d"), {
        type: "bar",
        data: {
            labels: etiquetas,
            datasets: [{
                label: "Reproducciones",
                data: valores,
                backgroundColor: gradiente,
                borderRadius: 4,
                hoverBackgroundColor: "#fff", // Se pone blanco nuclear al tocar
                borderWidth: 1,
                borderColor: "rgba(74, 222, 128, 0.5)"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(21, 21, 23, 0.95)',
                    titleColor: '#4ade80',
                    titleFont: { size: 12, family: 'Courier New' },
                    bodyFont: { size: 14, weight: 'bold' },
                    padding: 10,
                    displayColors: false
                }
            },
            scales: {
                x: {
                    display: true, // ¡Encendemos el eje X!
                    grid: { display: false },
                    ticks: {
                        color: "rgba(255,255,255,0.4)",
                        maxTicksLimit: 6, // Máximo 6 fechas para no saturar
                        font: { size: 10, family: 'Courier New' },
                        callback: function (value, index, values) {
                            // Muestra solo Día/Mes para que quede más limpio
                            let fecha = this.getLabelForValue(value);
                            return fecha ? fecha.substring(5, 10).replace('-', '/') : '';
                        }
                    }
                },
                y: {
                    grid: { color: "rgba(255,255,255,0.05)" },
                    ticks: { stepSize: 1, color: "rgba(255,255,255,0.4)" }
                }
            },
            interaction: {
                mode: 'index',
                intersect: false,
            }
        }
    });
}

function renderizarGraficaIronMan(etiquetas, datos) {
    const ctx = document.getElementById("grafica-fatiga");
    if (!ctx) return;
    if (chartOR) chartOR.destroy();

    let gradiente = ctx.getContext("2d").createLinearGradient(0, 0, 0, 300);
    gradiente.addColorStop(0, "rgba(29, 185, 84, 0.5)");
    gradiente.addColorStop(1, "rgba(29, 185, 84, 0.0)");

    chartOR = new Chart(ctx.getContext("2d"), {
        type: "line",
        data: {
            labels: etiquetas,
            datasets: [{
                label: "OverRate",
                data: datos,
                borderColor: "#1DB954",
                borderWidth: 2,
                backgroundColor: gradiente,
                fill: true,
                tension: 0.4, // Curvas más suaves
                pointRadius: 0,
                hitRadius: 20,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: "#fff",
                pointHoverBorderColor: "#1DB954"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(21, 21, 23, 0.95)',
                    titleColor: '#1DB954',
                    titleFont: { size: 12, family: 'Courier New' },
                    bodyFont: { size: 14, weight: 'bold' },
                    padding: 10,
                    displayColors: false
                }
            },
            scales: {
                x: {
                    display: true, // Eje X encendido
                    grid: { color: "rgba(255,255,255,0.03)", drawBorder: false },
                    ticks: {
                        color: "rgba(255,255,255,0.4)",
                        maxTicksLimit: 6,
                        font: { size: 10, family: 'Courier New' },
                        callback: function (value, index, values) {
                            let fecha = this.getLabelForValue(value);
                            return fecha ? fecha.substring(5, 10).replace('-', '/') : '';
                        }
                    }
                },
                y: {
                    grid: { color: "rgba(255,255,255,0.05)", borderDash: [5, 5] },
                    ticks: { color: "rgba(255,255,255,0.4)" }
                }
            },
            interaction: {
                mode: 'index',
                intersect: false,
            }
        }
    });
}

function cerrarDetalle() {
    const contenedor = document.getElementById("pantalla-detalle");
    contenedor.innerHTML = ""; // Limpiamos para la próxima vez
    mostrarPantalla(pantallaAnterior);
}

function pintarGrafica(datos) {

    // Configuración visual de la gráfica (ESTILO NEÓN PREMIUM)
    const ctx = document.getElementById("grafica-fatiga").getContext("2d");

    // Creamos un degradado que va de verde transparente a negro
    let gradiente = ctx.createLinearGradient(0, 0, 0, 300);
    gradiente.addColorStop(0, "rgba(29, 185, 84, 0.4)");
    gradiente.addColorStop(1, "rgba(29, 185, 84, 0.0)");

    chartInstancia = new Chart(ctx, {
        type: "line",
        data: {
            labels: etiquetas,
            datasets: [{
                label: "Nivel de Fatiga",
                data: datosPuntos,
                borderColor: "#1DB954", // Verde Spotify
                borderWidth: 3,
                backgroundColor: gradiente, // Aplicamos el degradado debajo de la curva
                fill: true, // Rellena el espacio bajo la curva
                tension: 0.4, // Curvas muy suaves y elegantes
                pointBackgroundColor: "#fff", // Puntos blancos que destacan
                pointBorderColor: "#1DB954",
                pointBorderWidth: 2,
                pointRadius: 3, // Puntos más visibles
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    titleFont: { size: 13 },
                    bodyFont: { size: 14, weight: 'bold' },
                    displayColors: false,
                    padding: 10,
                    cornerRadius: 8
                }
            },
            scales: {
                x: {
                    display: false // Ocultamos el eje X para que quede más limpio
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: "rgba(255,255,255,0.05)", // Líneas horizontales muy sutiles
                        drawBorder: false
                    },
                    ticks: {
                        color: "rgba(255,255,255,0.4)",
                        font: { size: 10 }
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index',
            },
        }
    });
}

function cerrarDetalle() {

    if (pantallaAnterior === "playlists") {
        mostrarPantalla("pantalla-analisis");
    } else {
        mostrarPantalla("pantalla-dashboard");
    }
}

// =========================================================
// MOTOR OVERRIDE: PLACEHOLDER DE INFERENCIA MANUAL
// =========================================================
function registrarInputOVR(trackId, accion) {
    // 1. Efecto háptico en móvil (si lo soporta)
    if (navigator.vibrate) navigator.vibrate(50);

    // 2. Aquí prepararemos el fetch() hacia el backend para guardarlo en la DB
    // fetch(`/override/input`, { method: 'POST', body: JSON.stringify({ trackId, accion }) })

    console.log(`[OVERRIDE ENGINE] 🧠 Input de usuario registrado:`);
    console.log(`   ➔ Track: ${trackId}`);
    console.log(`   ➔ Acción: ${accion}`);
    console.log(`   ➔ Info: Este dato calibrará la red neuronal en la v1.0 Alpha.`);

    // 3. Mini feedback visual temporal para que sepas que ha funcionado
    const btn = event.currentTarget;
    const textoOriginal = btn.innerHTML;
    btn.innerHTML = `<span style="color:#fff">¡REGISTRADO!</span>`;
    setTimeout(() => { btn.innerHTML = textoOriginal; }, 1000);
}


/* =========================================================
   FEEDBACK MANUAL (Botones Hielo / Fuego)
========================================================= */
async function mandarFeedback(evento, trackId, accion) {
    // Esto evita que el clic "atraviese" el botón y abra la ventana de detalles
    evento.stopPropagation();

    // Efecto visual instantáneo para que se sienta fluido
    const btn = evento.currentTarget;
    const colorOriginal = btn.style.background;
    btn.style.background = accion === "like" ? "rgba(74, 222, 128, 0.3)" : "rgba(255, 77, 97, 0.3)";

    try {
        const res = await fetch("/feedback", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ track_id: trackId, accion: accion })
        });

        if (res.ok) {
            const data = await res.json();
            // Refrescamos la playlist para ver los nuevos puntos en directo
            if (pantallaAnterior === "playlists") {
                // Truco para recargar la misma playlist sin volver atrás
                document.getElementById("btn-cargar-playlists").click();
            } else {
                cargarDashboard();
            }
        }
    } catch (error) {
        console.error("❌ Error enviando feedback:", error);
    } finally {
        setTimeout(() => btn.style.background = colorOriginal, 300);
    }
}

/* =========================================================
   MÓDULO DE CONFIGURACIÓN DEL NÚCLEO
========================================================= */

const modalConfig = document.getElementById('modal-configuracion');

// Escuchadores de eventos para actualizar los numeritos en vivo
document.querySelectorAll('.slider-neon').forEach(slider => {
    slider.addEventListener('input', (e) => {
        const spanId = e.target.id.replace('cfg-', 'val-');
        const span = document.getElementById(spanId);
        if (span) {
            // Si es el año, no le ponemos decimales
            span.innerText = e.target.id === 'cfg-nostalgia' ? e.target.value : parseFloat(e.target.value).toFixed(1);
        }
    });
});

async function abrirConfiguracion() {
    console.log("🛠️ Inyectando modal de configuración...");
    const modalConfig = document.getElementById('modal-configuracion');

    if (!modalConfig) {
        console.error("❌ ERROR: El HTML no tiene el div con id 'modal-configuracion'.");
        return; // Cortamos aquí para que no pete
    }

    // 1. Mostrar la ventana a la fuerza bruta
    modalConfig.style.display = 'flex';
    modalConfig.classList.remove('hidden');

    // 2. Pedir los datos actuales a la API
    try {
        const res = await fetch('/config');
        if (res.ok) {
            const data = await res.json();

            // Asignar valores a los inputs (con fallbacks por si la DB está vacía)
            document.getElementById('cfg-sensibilidad').value = data.factor_sensibilidad || 1.0;
            document.getElementById('cfg-atracon').value = data.tolerancia_atracon || 1.0;
            document.getElementById('cfg-amnesia').value = data.tasa_amnesia || 1.0;
            document.getElementById('cfg-nostalgia').value = data.año_nostalgia || 2015;
            document.getElementById('cfg-rapidos').value = data.generos_rapidos || "reggaeton, trap";
            document.getElementById('cfg-refugio').value = data.generos_refugio || "lo-fi, jazz";

            // Actualizar los textos visuales
            document.getElementById('val-sensibilidad').innerText = parseFloat(data.factor_sensibilidad || 1).toFixed(1);
            document.getElementById('val-atracon').innerText = parseFloat(data.tolerancia_atracon || 1).toFixed(1);
            document.getElementById('val-amnesia').innerText = parseFloat(data.tasa_amnesia || 1).toFixed(1);
            document.getElementById('val-nostalgia').innerText = data.año_nostalgia || 2015;
        }
    } catch (e) {
        console.error("❌ Error cargando configuración desde la API:", e);
    }
}

function cerrarConfiguracion() {
    document.getElementById('modal-configuracion').style.display = 'none';

    // 🧠 LÓGICA NINJA: Volver a iluminar la sección en la que estábamos de fondo
    const pantallaActual = Array.from(document.querySelectorAll("section")).find(p => p.style.display === "block" || p.style.display === "");

    if (pantallaActual) {
        if (pantallaActual.id === "pantalla-dashboard") {
            actualizarNav("nav-inicio");
        } else if (pantallaActual.id === "pantalla-playlists" || pantallaActual.id === "pantalla-analisis") {
            actualizarNav("nav-playlists");
        }
    } else {
        // Por si acaso todo falla, volvemos a inicio
        actualizarNav("nav-inicio");
    }
}

async function guardarConfiguracion() {
    const btn = document.querySelector('.btn-guardar-config');
    btn.innerText = "INYECTANDO...";

    // Empaquetamos los datos exactos que espera Python (ConfigUsuario)
    const payload = {
        factor_sensibilidad: parseFloat(document.getElementById('cfg-sensibilidad').value),
        tolerancia_atracon: parseFloat(document.getElementById('cfg-atracon').value),
        tasa_amnesia: parseFloat(document.getElementById('cfg-amnesia').value),
        año_nostalgia: parseInt(document.getElementById('cfg-nostalgia').value),
        generos_rapidos: document.getElementById('cfg-rapidos').value,
        generos_refugio: document.getElementById('cfg-refugio').value
    };

    try {
        const res = await fetch('/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (res.ok) {
            btn.innerText = "✅ PARÁMETROS FIJADOS";
            setTimeout(() => {
                btn.innerText = "💾 INYECTAR PARÁMETROS";
                cerrarConfiguracion();
            }, 1000);
        } else {
            alert("Error del sistema: " + data.detail);
            btn.innerText = "💾 INYECTAR PARÁMETROS";
        }
    } catch (e) {
        console.error("❌ Error guardando configuración:", e);
        btn.innerText = "❌ ERROR DE CONEXIÓN";
        setTimeout(() => btn.innerText = "💾 INYECTAR PARÁMETROS", 2000);
    }
}

let todosLosGeneros = [];

async function abrirConfiguracion() {
    const modalConfig = document.getElementById('modal-configuracion');
    if (!modalConfig) return;

    modalConfig.style.display = 'flex';
    modalConfig.classList.remove('hidden');

    try {
        // 1. Pedimos a la vez la config del usuario y TODOS los géneros de la DB
        const [resConfig, resGeneros] = await Promise.all([
            fetch('/config'),
            fetch('/generos_db')
        ]);

        const configData = await resConfig.json();
        const generosData = await resGeneros.json();

        // 2. Rellenamos los sliders normales
        document.getElementById('cfg-sensibilidad').value = configData.factor_sensibilidad || 1.0;
        document.getElementById('cfg-atracon').value = configData.tolerancia_atracon || 1.0;
        document.getElementById('cfg-amnesia').value = configData.tasa_amnesia || 1.0;
        document.getElementById('cfg-nostalgia').value = configData.año_nostalgia || 2015;

        document.getElementById('val-sensibilidad').innerText = parseFloat(configData.factor_sensibilidad || 1).toFixed(1);
        document.getElementById('val-atracon').innerText = parseFloat(configData.tolerancia_atracon || 1).toFixed(1);
        document.getElementById('val-amnesia').innerText = parseFloat(configData.tasa_amnesia || 1).toFixed(1);
        document.getElementById('val-nostalgia').innerText = configData.año_nostalgia || 2015;

        // 3. Pintamos la malla de géneros
        todosLosGeneros = generosData.generos || [];
        const generosRapidos = (configData.generos_rapidos || "").split(',').map(g => g.trim());
        const generosRefugio = (configData.generos_refugio || "").split(',').map(g => g.trim());

        renderizarGridGeneros(generosRapidos, generosRefugio);

    } catch (e) {
        console.error("❌ Error cargando configuración:", e);
    }
}

function renderizarGridGeneros(rapidos, refugios, filtro = "") {
    const grid = document.getElementById('grid-generos');
    grid.innerHTML = "";

    todosLosGeneros.forEach(g => {
        if (filtro && !g.includes(filtro.toLowerCase())) return; // Filtro del buscador

        const chip = document.createElement('div');
        chip.className = 'genre-chip';
        chip.innerText = g;
        chip.dataset.genero = g; // Guardamos el nombre en el HTML

        // Le ponemos el color que le toca según la BD
        if (rapidos.includes(g)) chip.classList.add('rapido');
        else if (refugios.includes(g)) chip.classList.add('refugio');

        // Lógica del Clic (Neutral -> Rapido -> Refugio -> Neutral)
        chip.onclick = () => {
            if (chip.classList.contains('rapido')) {
                chip.classList.remove('rapido');
                chip.classList.add('refugio');
            } else if (chip.classList.contains('refugio')) {
                chip.classList.remove('refugio');
            } else {
                chip.classList.add('rapido');
            }
        };

        grid.appendChild(chip);
    });
}

function filtrarGeneros() {
    const texto = document.getElementById('buscador-generos').value;

    // Para no perder lo que hemos tocado antes de guardar, leemos el estado actual del HTML
    const rapidosActuales = Array.from(document.querySelectorAll('.genre-chip.rapido')).map(c => c.dataset.genero);
    const refugiosActuales = Array.from(document.querySelectorAll('.genre-chip.refugio')).map(c => c.dataset.genero);

    renderizarGridGeneros(rapidosActuales, refugiosActuales, texto);
}

async function guardarConfiguracion() {
    const btn = document.querySelector('.btn-guardar-config');
    btn.innerText = "INYECTANDO...";

    // 🧠 Extraemos los textos de los chips que están en rojo o en azul
    const rapidos = Array.from(document.querySelectorAll('.genre-chip.rapido')).map(c => c.dataset.genero).join(', ');
    const refugios = Array.from(document.querySelectorAll('.genre-chip.refugio')).map(c => c.dataset.genero).join(', ');

    const payload = {
        factor_sensibilidad: parseFloat(document.getElementById('cfg-sensibilidad').value),
        tolerancia_atracon: parseFloat(document.getElementById('cfg-atracon').value),
        tasa_amnesia: parseFloat(document.getElementById('cfg-amnesia').value),
        año_nostalgia: parseInt(document.getElementById('cfg-nostalgia').value),
        generos_rapidos: rapidos,
        generos_refugio: refugios
    };

    try {
        const res = await fetch('/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            btn.innerText = "✅ PARÁMETROS FIJADOS";
            setTimeout(() => { btn.innerText = "💾 INYECTAR PARÁMETROS"; cerrarConfiguracion(); }, 1000);
        }
    } catch (e) {
        console.error(e);
        btn.innerText = "❌ ERROR";
    }
}

/* =========================================================
   MOTOR DE BÚSQUEDA (Final Boss)
========================================================= */
let timeoutBusqueda = null; // El temporizador ninja

function ejecutarBusqueda() {
    const input = document.getElementById("input-buscador");
    const contenedor = document.getElementById("resultados-busqueda");
    const query = input.value.trim();

    // Si borramos todo o hay menos de 2 letras, no buscamos
    if (query.length < 2) {
        contenedor.innerHTML = `<div style="text-align: center; color: #666; font-size: 13px; margin-top: 40px;">Teclea al menos 2 letras... 🛰️</div>`;
        return;
    }

    // 🛑 MAGIA DEBOUNCE: Si el usuario sigue tecleando, cancelamos la búsqueda anterior
    clearTimeout(timeoutBusqueda);

    contenedor.innerHTML = `<div class="loader" style="font-size:12px;">Rastreando coincidencias... 🔍</div>`;

    // Ejecutamos la búsqueda real 300ms después de la última tecla pulsada
    timeoutBusqueda = setTimeout(async () => {
        try {
            const res = await fetch(`/buscar?q=${encodeURIComponent(query)}`);
            if (!res.ok) throw new Error("Fallo en la API de búsqueda");

            const data = await res.json();

            if (!data.resultados || data.resultados.length === 0) {
                contenedor.innerHTML = `<div style="text-align: center; color: #ff4757; font-size: 13px; margin-top: 40px;">No hay registros de "${query}".</div>`;
                return;
            }

            // Pintamos los resultados reciclando tu diseño de lista limpia (.widget-track)
            contenedor.innerHTML = "";
            data.resultados.forEach(c => {
                const imgSegura = c.img || `https://ui-avatars.com/api/?name=${encodeURIComponent(c.nombre)}&background=222&color=fff&bold=true`;

                // Color dinámico según lo quemada que esté la canción
                let glowColor = "rgba(74, 222, 128, 0.4)";
                let textColor = "#4ade80"; // Verde
                if (c.score >= 65) { glowColor = "rgba(255, 77, 97, 0.4)"; textColor = "#ff4d61"; } // Rojo
                else if (c.score >= 30) { glowColor = "rgba(255, 179, 71, 0.4)"; textColor = "#ffb347"; } // Naranja

                contenedor.innerHTML += `
                    <div class="widget-track" onclick="abrirDetalle('${escaparComillas(c.track_id)}')">
                        <img src="${imgSegura}" class="widget-portada" onerror="this.src='https://ui-avatars.com/api/?name=X&background=222&color=fff'">
                        <div class="widget-info">
                            <div class="widget-titulo">${c.nombre}</div>
                            <div class="widget-artista">${c.artista}</div>
                        </div>
                        <div class="widget-score" style="color: ${textColor}; text-shadow: 0 0 10px ${glowColor};">
                            ${c.score} <span style="font-size:10px;">OR</span>
                        </div>
                    </div>
                `;
            });
        } catch (e) {
            console.error("❌ Error en la búsqueda:", e);
            contenedor.innerHTML = `<div style="color:red; text-align:center; font-size:12px; margin-top:20px;">Error de conexión 📡</div>`;
        }
    }, 300);
}

/* =========================================================
   DEBUG
========================================================= */

async function debugCancion(trackId) {

    try {

        const res =
            await fetch(`${API_URL}/debug/cancion/${encodeURIComponent(trackId)}`);

        const datos = await res.json();

        console.table(datos.historial);
        console.table(datos.fatiga);
        console.table(datos.feedback);

    } catch (error) {

        console.error(error);
    }
}