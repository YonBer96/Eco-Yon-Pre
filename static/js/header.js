// header.js
// Usa apiFetch (definido en api.js). Este header es para JWT.

function setGuestUI() {
    const navAuth = document.getElementById("nav-auth");
    const navUser = document.getElementById("nav-user");
    const navDashboard = document.getElementById("nav-dashboard");

    if (navAuth) navAuth.classList.remove("hidden");
    if (navUser) navUser.classList.add("hidden");
    if (navDashboard) navDashboard.classList.add("hidden");
}

function setUserUI(isStaff) {
    const navAuth = document.getElementById("nav-auth");
    const navUser = document.getElementById("nav-user");
    const navDashboard = document.getElementById("nav-dashboard");

    if (navAuth) navAuth.classList.add("hidden");
    if (navUser) navUser.classList.remove("hidden");

    if (navDashboard) {
        // Blindar el href por si algo raro lo pisa
        navDashboard.setAttribute("href", "/dashboard/");

        if (isStaff) navDashboard.classList.remove("hidden");
        else navDashboard.classList.add("hidden");
    }
}

async function loadMeAndUpdateUI() {
    const token = localStorage.getItem("access_token");
    if (!token) {
        setGuestUI();
        return;
    }

    let res;
    try {
        res = await apiFetch("/api/me/");
    } catch (e) {
        setGuestUI();
        return;
    }

    if (!res || res.status === 401 || res.status === 403) {
        setGuestUI();
        return;
    }

    if (!res.ok) {
        setGuestUI();
        return;
    }

    const me = await res.json().catch(() => null);
    if (!me) {
        setGuestUI();
        return;
    }

    setUserUI(!!me.is_staff);
}

document.addEventListener("DOMContentLoaded", () => {
    loadMeAndUpdateUI();
});