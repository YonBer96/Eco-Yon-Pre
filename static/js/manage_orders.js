// manage_orders.js
// Dashboard (encargado): debe funcionar con sesión Django *o* JWT.
// Importante: NO redirigimos por falta de token. La sesión puede estar activa.

function show(id) {
    document.getElementById("viewOrders").classList.add("hidden");
    document.getElementById("viewCustomers").classList.add("hidden");
    document.getElementById("viewAlbaranes").classList.add("hidden");
    document.getElementById(id).classList.remove("hidden");
}

// Helpers API (usa apiFetch/apiFetchParsed de api.js)
async function apiGet(path) {
    return apiFetchParsed(`${API_URL}${path}`, { redirectOn401: true });
}

async function apiPost(path, body) {
    return apiFetchParsed(`${API_URL}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        redirectOn401: true,
    });
}

/* =========================
   Helpers UI
========================= */
function fmtEUR(v) {
    const n = Number(v);
    if (Number.isNaN(n)) return `${v}€`;
    return `${n.toFixed(2)}€`;
}

function formatDelivery(o) {
    const method = (o && o.delivery_method) ? String(o.delivery_method).toUpperCase() : "PICKUP";
    const slot = (o && o.delivery_slot) ? ` — ${o.delivery_slot}` : "";

    if (method === "DELIVERY") return `🚚 Envío${slot}`;
    return `🏪 Recogida${slot}`;
}

/**
 * Abre el albarán en nueva pestaña.
 * Ojo: si usas window.location, no puedes añadir headers.
 * Por eso hacemos fetch → HTML → window.open().
 */
async function openAlbaran(orderId) {
    const { res, data } = await apiGet(`/manager/orders/${orderId}/albaran/`);
    if (res.status === 401) return; // apiFetch ya habrá redirigido si toca

    if (!res.ok) {
        toast("No se pudo abrir el albarán.", "error");
        return;
    }

    const html = typeof data === "string" ? data : "";
    const w = window.open("", "_blank");
    if (!w) {
        toast("Permite popups para abrir el albarán.", "info");
        return;
    }
    w.document.open();
    w.document.write(html);
    w.document.close();
}

/**
 * Descarga ZIP (albaranes) con fetch.
 * Necesario porque <a href> / window.location no permite mandar Authorization.
 */
async function downloadZipByStatus(status) {
    toast("Generando ZIP…", "info");

    const res = await apiFetch(`${API_URL}/manager/albaranes/zip/?status=${encodeURIComponent(status)}`, {
        redirectOn401: true,
    });

    if (res.status === 401) return;

    if (!res.ok) {
        toast("No se pudo generar el ZIP.", "error");
        return;
    }

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;

    const cd = res.headers.get("content-disposition") || "";
    const m = cd.match(/filename="([^"]+)"/);
    a.download = m ? m[1] : `albaranes_${status}.zip`;

    document.body.appendChild(a);
    a.click();
    a.remove();

    window.URL.revokeObjectURL(url);
    toast("ZIP descargado ✅", "success");
}

/* ====== PEDIDOS ====== */
async function renderOrders() {
    const wrap = document.getElementById("viewOrders");
    wrap.innerHTML = `
    <h2>Pedidos</h2>
    <div class="toolbar">
      <div class="filters">
        <select id="stFilter">
          <option value="">Todos</option>
          <option value="PENDING">Pendiente</option>
          <option value="PREPARING">Preparando</option>
          <option value="READY">Listo</option>
          <option value="IN_TRANSIT">En camino</option>
          <option value="DONE">Entregado</option>
          <option value="CANCELLED">Cancelado</option>
        </select>
        <input id="qFilter" placeholder="Buscar (id o usuario)..." />
      </div>
      <button class="btn btn--secondary" type="button" id="reloadOrders">Recargar</button>
    </div>
    <div id="ordersTable"></div>
  `;

    document.getElementById("reloadOrders").onclick = loadOrders;
    document.getElementById("stFilter").onchange = loadOrders;
    document.getElementById("qFilter").oninput = () => {
        clearTimeout(window.__t);
        window.__t = setTimeout(loadOrders, 220);
    };

    await loadOrders();
}

async function loadOrders() {
    const st = document.getElementById("stFilter").value;
    const q = document.getElementById("qFilter").value.trim();

    const params = new URLSearchParams();
    if (st) params.set("status", st);
    if (q) params.set("q", q);

    const qs = params.toString();
    const { res, data } = await apiGet(`/manager/orders/${qs ? "?" + qs : ""}`);
    if (res.status === 401) return;

    if (!res.ok) { toast("No se pudieron cargar pedidos", "error"); return; }

    const el = document.getElementById("ordersTable");

    el.innerHTML = `
    <table class="table">
      <thead>
        <tr>
          <th>ID</th><th>Cliente</th><th>Estado</th><th>Pago</th><th>Total</th><th>Entrega</th><th>Acciones</th>
        </tr>
      </thead>
      <tbody>
        ${data.map(o => `
          <tr>
            <td><b>#${o.id}</b></td>
            <td>${o.user}</td>
            <td>${o.status}</td>
            <td>${o.paid ? "✅ Pagado" : "⏳ Pendiente"}</td>
            <td><b>${fmtEUR(o.total)}</b></td>
            <td>${formatDelivery(o)}</td>
            <td style="display:flex; gap:8px; flex-wrap:wrap">
              <select id="st-${o.id}" style="width:160px">
                <option value="PENDING">PENDING</option>
                <option value="PREPARING">PREPARING</option>
                <option value="READY">READY</option>
                <option value="IN_TRANSIT">IN_TRANSIT</option>
                <option value="DONE">DONE</option>
                <option value="CANCELLED">CANCELLED</option>
              </select>
              <button class="btn btn--secondary" type="button" data-save="${o.id}">Guardar</button>
              <button class="btn" type="button" data-alb="${o.id}">Albarán</button>
            </td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;

    data.forEach(o => {
        const sel = document.getElementById(`st-${o.id}`);
        if (sel) sel.value = o.status;
    });

    el.querySelectorAll("[data-save]").forEach(btn => {
        btn.onclick = async () => {
            const id = btn.dataset.save;
            const status = document.getElementById(`st-${id}`).value;

            const prev = btn.textContent;
            btn.disabled = true;
            btn.textContent = "Guardando…";

            const out = await apiPost(`/manager/orders/${id}/status/`, { status });

            btn.disabled = false;
            btn.textContent = prev;

            const { res, data } = out;
            if (res.status === 401) return;

            if (!res.ok) {
                const msg = (data && data.detail) ? data.detail : "No se pudo cambiar estado";
                toast(msg, "error");
                return;
            }

            toast("Estado actualizado ✅", "success");
            await loadOrders();
        };
    });

    el.querySelectorAll("[data-alb]").forEach(btn => {
        btn.onclick = () => openAlbaran(btn.dataset.alb);
    });
}

/* ====== CLIENTES ====== */
async function renderCustomers() {
    const wrap = document.getElementById("viewCustomers");
    wrap.innerHTML = `
    <h2>Clientes registrados</h2>
    <div class="toolbar">
      <div class="filters">
        <input id="custQ" placeholder="Buscar cliente..." />
      </div>
      <button class="btn btn--secondary" type="button" id="reloadCustomers">Recargar</button>
    </div>
    <div id="customersList"></div>
    <div id="customerOrders" style="margin-top:14px"></div>
  `;

    document.getElementById("reloadCustomers").onclick = loadCustomers;
    document.getElementById("custQ").oninput = () => {
        clearTimeout(window.__tc);
        window.__tc = setTimeout(loadCustomers, 220);
    };

    await loadCustomers();
}

async function loadCustomers() {
    const { res, data } = await apiGet("/manager/customers/");
    if (res.status === 401) return;

    if (!res.ok) { toast("No se pudieron cargar clientes", "error"); return; }

    const q = document.getElementById("custQ").value.trim().toLowerCase();
    const filtered = data.filter(u =>
        !q ||
        (u.username || "").toLowerCase().includes(q) ||
        (u.email || "").toLowerCase().includes(q)
    );

    const list = document.getElementById("customersList");
    list.innerHTML = `
    <table class="table">
      <thead><tr><th>Usuario</th><th>Email</th><th></th></tr></thead>
      <tbody>
        ${filtered.map(u => `
          <tr>
            <td><b>${u.username}</b></td>
            <td>${u.email || "-"}</td>
            <td>
              <button class="btn btn--secondary" type="button" data-u="${u.id}" data-name="${u.username}">
                Ver pedidos
              </button>
            </td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;

    list.querySelectorAll("[data-u]").forEach(btn => {
        btn.onclick = () => loadCustomerOrders(btn.dataset.u, btn.dataset.name);
    });
}

async function loadCustomerOrders(userId, username) {
    const { res, data } = await apiGet(`/manager/customers/${userId}/orders/`);
    if (res.status === 401) return;

    if (!res.ok) { toast("No se pudieron cargar pedidos del cliente", "error"); return; }

    const box = document.getElementById("customerOrders");
    box.innerHTML = `
    <h3>Pedidos de ${username}</h3>
    <table class="table">
      <thead><tr><th>ID</th><th>Estado</th><th>Pago</th><th>Total</th><th></th></tr></thead>
      <tbody>
        ${data.map(o => `
          <tr>
            <td><b>#${o.id}</b></td>
            <td>${o.status}</td>
            <td>${o.paid ? "✅" : "⏳"}</td>
            <td>${fmtEUR(o.total)}</td>
            <td>
              <button class="btn" type="button" data-alb="${o.id}">Albarán</button>
            </td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;

    box.querySelectorAll("[data-alb]").forEach(btn => {
        btn.onclick = () => openAlbaran(btn.dataset.alb);
    });
}

/* ====== ALBARANES ====== */
async function renderAlbaranes() {
    const wrap = document.getElementById("viewAlbaranes");
    wrap.innerHTML = `
    <h2>Albaranes</h2>
    <p class="muted">Genera un ZIP con todos los albaranes por estado (para preparar pedidos).</p>
    <div class="toolbar">
      <div class="filters">
        <select id="albStatus">
          <option value="PREPARING">PREPARING</option>
          <option value="READY">READY</option>
          <option value="PENDING">PENDING</option>
          <option value="IN_TRANSIT">IN_TRANSIT</option>
        </select>
      </div>
      <button class="btn btn--primary" type="button" id="downloadZip">Descargar ZIP</button>
    </div>
  `;

    document.getElementById("downloadZip").onclick = async () => {
        const st = document.getElementById("albStatus").value;
        await downloadZipByStatus(st);
    };
}

/* ====== TABS ====== */
document.addEventListener("DOMContentLoaded", async () => {
    document.getElementById("tabOrders").onclick = async () => { show("viewOrders"); await renderOrders(); };
    document.getElementById("tabCustomers").onclick = async () => { show("viewCustomers"); await renderCustomers(); };
    document.getElementById("tabAlbaranes").onclick = async () => { show("viewAlbaranes"); await renderAlbaranes(); };

    show("viewOrders");
    await renderOrders();
});
