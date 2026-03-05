// my_orders.js
// ✅ Funciona con JWT o con sesión Django (cookie).
// ✅ NO redirige por falta de token.
// ✅ Solo redirige si el backend devuelve 401 real.

function fmtEUR(v) {
    const n = Number(v);
    if (Number.isNaN(n)) return `${v} €`;
    return `${n.toFixed(2)} €`;
}

// Si realmente no estás autenticado, apiFetch puede redirigir
function handle401() {
    // limpiamos JWT por si existía
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    window.location.href = "/login/";
}

// =========================
// CARGAR PEDIDOS DEL USUARIO
// =========================
async function loadOrders() {
    const msg = document.getElementById("ordersMsg");
    const list = document.getElementById("ordersList");

    if (msg) msg.textContent = "";
    if (list) list.innerHTML = "";

    // Asegura que api.js está cargado
    if (typeof apiFetchParsed !== "function") {
        if (msg) msg.textContent = "Error: api.js no está cargado (apiFetchParsed no existe).";
        console.error("apiFetchParsed no existe. Revisa orden de scripts en my_orders.html");
        return;
    }

    // Pedimos al backend los pedidos del usuario autenticado (JWT o sesión)
    const { res, data } = await apiFetchParsed(`${API_URL}/my-orders/`, {
        redirectOn401: false, // lo gestionamos aquí para controlar el flujo
    });

    if (res.status === 401) {
        handle401();
        return;
    }

    if (!res.ok) {
        if (msg) msg.textContent = "No se pudieron cargar tus pedidos.";
        return;
    }

    const orders = Array.isArray(data) ? data : [];

    if (!orders.length) {
        if (list) list.innerHTML = "<p>No tienes pedidos todavía.</p>";
        return;
    }

    // Pintamos cada pedido como una tarjeta
    orders.forEach(o => {
        const div = document.createElement("div");
        div.className = "card";

        div.innerHTML = `
          <b>Pedido #${o.id}</b><br>
          Estado: ${o.status}<br>
          Total: ${fmtEUR(o.total)}<br>
          Fecha: ${o.created_at ? new Date(o.created_at).toLocaleString() : "-"}<br><br>

          <button class="btn btn--secondary" type="button" data-view="${o.id}">Ver factura</button>
          <button class="btn" type="button" data-pdf="${o.id}">Descargar PDF</button>
        `;

        list.appendChild(div);
    });

    // Eventos: abrir factura HTML
    list.querySelectorAll("[data-view]").forEach(btn => {
        btn.addEventListener("click", () => openInvoice(btn.dataset.view));
    });

    // Eventos: descargar factura PDF
    list.querySelectorAll("[data-pdf]").forEach(btn => {
        btn.addEventListener("click", () => downloadInvoicePdf(btn.dataset.pdf));
    });
}

// =========================
// FACTURA HTML (NUEVA PESTAÑA)
// =========================
async function openInvoice(orderId) {
    const { res, data } = await apiFetchParsed(`${API_URL}/invoice/${orderId}/`, {
        redirectOn401: false,
    });

    if (res.status === 401) {
        handle401();
        return;
    }

    if (!res.ok) {
        alert("No se pudo cargar la factura");
        return;
    }

    const html = (typeof data === "string") ? data : "";
    const w = window.open("", "_blank");
    if (!w) {
        alert("Permite popups para abrir la factura.");
        return;
    }

    w.document.open();
    w.document.write(html);
    w.document.close();
}

// =========================
// FACTURA PDF (DESCARGA)
// =========================
async function downloadInvoicePdf(orderId) {
    const res = await apiFetch(`${API_URL}/invoice/${orderId}/pdf/`, {
        redirectOn401: false,
    });

    if (res.status === 401) {
        handle401();
        return;
    }

    if (!res.ok) {
        alert("No se pudo descargar el PDF");
        return;
    }

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = `factura_${orderId}.pdf`;

    document.body.appendChild(a);
    a.click();
    a.remove();

    window.URL.revokeObjectURL(url);
}

// Al cargar la página, cargamos pedidos automáticamente
document.addEventListener("DOMContentLoaded", loadOrders);
