// Devuelve el access token guardado en el navegador (JWT)
function getToken() {
    return localStorage.getItem("access_token");
}

// Formatea un valor como euros con 2 decimales
function moneyEUR(v) {
    const n = Number(v);
    if (Number.isNaN(n)) return `${v} €`;      // si no es número, lo muestra tal cual
    return `${n.toFixed(2)} €`;                // 2 decimales siempre
}

// Wrapper de fetch que añade el token JWT al header Authorization
// y hace logout automático si el backend responde 401
async function apiFetch(url, options = {}) {
    const token = localStorage.getItem("access_token");
    const headers = { ...(options.headers || {}) };

    // Si hay token, lo mandamos como "Bearer <token>"
    if (token) headers.Authorization = `Bearer ${token}`;

    // Ejecuta la petición HTTP real
    const res = await fetch(url, { ...options, headers });

    // Si el token no vale/caducó → cerrar sesión y redirigir
    if (res.status === 401) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "/login/";
        return null;
    }

    return res;
}

// Carga el carrito desde la API y lo pinta en pantalla

async function refreshAccessToken() {
    const refresh = localStorage.getItem("refresh_token");
    if (!refresh) return false;

    const res = await fetch("/api/token/refresh/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh }),
    });

    if (!res.ok) return false;

    const data = await res.json();
    if (!data.access) return false;

    localStorage.setItem("access_token", data.access);
    return true;
}

// Wrapper de fetch con JWT + auto-refresh (1 intento) y logout si no se puede refrescar
async function apiFetch(url, options = {}) {
    const buildHeaders = () => {
        const token = localStorage.getItem("access_token");
        const headers = { ...(options.headers || {}) };
        if (token) headers.Authorization = `Bearer ${token}`;
        return headers;
    };

    // 1º intento
    let res = await fetch(url, { ...options, headers: buildHeaders() });

    // Si access caducó, refresca y reintenta 1 vez
    if (res.status === 401) {
        const refreshed = await refreshAccessToken();
        if (!refreshed) {
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");
            window.location.href = "/login/";
            return null;
        }

        // 2º intento con access nuevo
        res = await fetch(url, { ...options, headers: buildHeaders() });
    }

    // Si sigue 401, fuera
    if (res.status === 401) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "/login/";
        return null;
    }

    return res;
}

// Cuando carga el HTML, se carga el carrito automáticamente
document.addEventListener("DOMContentLoaded", loadCart);
