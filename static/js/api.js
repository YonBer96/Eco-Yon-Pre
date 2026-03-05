// static/js/api.js
// =========================
// AUTENTICACIÓN (JWT)
// =========================
//
// Objetivo (modo actual del proyecto):
// - El FRONT de clientes usa JWT guardado en localStorage.
// - Si hay access_token -> lo enviamos como Authorization: Bearer ...
// - Si el access caduca -> intentamos refresh con refresh_token y reintentamos 1 vez.
// - Si refresh falla -> borramos tokens y (opcional) redirigimos a /login/.
// - NO dependemos de sesión Django para la API de cliente.
//
// Nota:
// - Deja credentials: "same-origin" por si algún endpoint de staff usa cookies,
//   pero para clientes JWT no es imprescindible.

function getAccessToken() {
    return localStorage.getItem("access_token");
}

function getRefreshToken() {
    return localStorage.getItem("refresh_token");
}

function clearJwtTokens() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
}

function logout(redirectTo = "/login/") {
    clearJwtTokens();
    window.location.href = redirectTo;
}

// =========================
// REFRESH TOKEN
// =========================

async function refreshAccessToken() {
    const refresh = getRefreshToken();
    if (!refresh) return false;

    const res = await fetch("/api/token/refresh/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh }),
        credentials: "same-origin",
    });

    if (!res.ok) return false;

    const data = await res.json().catch(() => ({}));
    if (!data.access) return false;

    localStorage.setItem("access_token", data.access);
    return true;
}

// =========================
// FETCH CENTRALIZADO PARA LA API
// =========================
//
// Firma: apiFetch(url, options)
// Extra (opcional): options.redirectOn401 (boolean)
// - Si redirectOn401=true y no se puede refrescar, hace logout().
// - Por defecto NO redirige automáticamente, para que cada página decida.

async function apiFetch(url, options = {}) {
    const {
        redirectOn401 = false, // flag custom, no se pasa a fetch
        ...fetchOptions
    } = options;

    const buildHeaders = () => {
        const headers = { ...(fetchOptions.headers || {}) };
        const token = getAccessToken();
        if (token) headers.Authorization = `Bearer ${token}`;

        // Si mandas body string y no has puesto content-type, lo ponemos
        if (fetchOptions.body && typeof fetchOptions.body === "string" && !headers["Content-Type"]) {
            headers["Content-Type"] = "application/json";
        }

        return headers;
    };

    // 1er intento
    let res = await fetch(url, {
        credentials: "same-origin",
        ...fetchOptions,
        headers: buildHeaders(),
    });

    // Si 401, intenta refresh UNA vez y reintenta
    if (res.status === 401) {
        const refreshed = await refreshAccessToken();
        if (refreshed) {
            res = await fetch(url, {
                credentials: "same-origin",
                ...fetchOptions,
                headers: buildHeaders(),
            });
        }
    }

    // Si sigue 401 -> tokens fuera y (opcional) redirect
    if (res.status === 401) {
        clearJwtTokens();
        if (redirectOn401 && window.location.pathname !== "/login/") {
            window.location.href = "/login/";
            return null;
        }
    }

    return res;
}

// Helper opcional para devolver {res, data} ya parseado (JSON o texto)
async function apiFetchParsed(url, options = {}) {
    const res = await apiFetch(url, options);
    if (!res) return { res: null, data: null };

    const ct = (res.headers.get("content-type") || "").toLowerCase();
    let data = null;

    try {
        if (ct.includes("application/json")) data = await res.json();
        else data = await res.text();
    } catch (e) {
        data = null;
    }

    return { res, data };
}