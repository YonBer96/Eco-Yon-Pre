function ymd(d) {
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return `${yyyy}-${mm}-${dd}`;
}

function currentWeekRange() {
    const now = new Date();
    const day = (now.getDay() + 6) % 7; // lunes=0 ... domingo=6
    const monday = new Date(now);
    monday.setDate(now.getDate() - day);
    const sunday = new Date(monday);
    sunday.setDate(monday.getDate() + 6);
    return { start: ymd(monday), end: ymd(sunday) };
}

function urlWithDates(base) {
    const start = document.getElementById("startDate")?.value;
    const end = document.getElementById("endDate")?.value;

    const params = new URLSearchParams();
    if (start) params.set("start", start);
    if (end) params.set("end", end);

    const qs = params.toString();
    return qs ? `${base}?${qs}` : base;
}

function moneyEUR(v) {
    const n = Number(v);
    if (Number.isNaN(n)) return `${v} €`;
    return `${n.toFixed(2)} €`;
}

function renderOrders(data) {
    const box = document.getElementById("ordersBox");
    if (!box) return;

    const orders = Array.isArray(data.orders) ? data.orders : [];

    if (!orders.length) {
        box.innerHTML = `
      <div class="card">
        <p class="muted" style="margin:0">No hay pedidos en este rango.</p>
      </div>
    `;
        return;
    }

    box.innerHTML = orders.map(o => {
        const itemsHtml = (o.items || []).map(it =>
            `<li>${it.product} — ${it.qty} ${it.unit || ""}</li>`
        ).join("");

        return `
      <div class="card" style="margin-bottom:12px">
        <div style="display:flex; justify-content:space-between; gap:10px; flex-wrap:wrap">
          <div>
            <b>Pedido #${o.id}</b>
            <div class="muted" style="font-size:13px;margin-top:4px">
              Usuario: ${o.user?.username || "?"} · Estado: ${o.status} · Pagado: ${o.paid ? "Sí" : "No"}
            </div>
            <div class="muted" style="font-size:13px;margin-top:4px">
              Fecha: ${o.created_at}
            </div>
          </div>
          <div style="text-align:right">
            <b>${moneyEUR(o.total)}</b>
          </div>
        </div>

        <ul style="margin:10px 0 0 18px">
          ${itemsHtml}
        </ul>
      </div>
    `;
    }).join("");
}

async function loadOrders() {
    const msg = document.getElementById("dashMsg");
    if (msg) msg.textContent = "Cargando pedidos…";

    const url = urlWithDates("/api/manager/orders/");
    const res = await apiFetch(url, { redirectOn401: true });

    if (!res || !res.ok) {
        if (msg) msg.textContent = "No se pudieron cargar los pedidos.";
        return;
    }

    const data = await res.json();
    if (msg) msg.textContent = `Mostrando pedidos del ${data.start} al ${data.end}`;
    renderOrders(data);
}

document.addEventListener("DOMContentLoaded", () => {
    // Set semana actual por defecto
    const { start, end } = currentWeekRange();
    const startEl = document.getElementById("startDate");
    const endEl = document.getElementById("endDate");
    if (startEl) startEl.value = start;
    if (endEl) endEl.value = end;

    // Botones
    const btnLoad = document.getElementById("btnLoadOrders");
    const btnWeek = document.getElementById("btnWeek");
    const btnHtml = document.getElementById("btnAlbaranHtml");
    const btnPdf = document.getElementById("btnAlbaranPdf");

    if (btnLoad) btnLoad.addEventListener("click", loadOrders);

    if (btnWeek) {
        btnWeek.addEventListener("click", () => {
            const r = currentWeekRange();
            if (startEl) startEl.value = r.start;
            if (endEl) endEl.value = r.end;
            loadOrders();
        });
    }

    if (btnHtml) {
        btnHtml.addEventListener("click", () => {
            window.open(urlWithDates("/api/manager/albaran/summary/"), "_blank");
        });
    }

    if (btnPdf) {
        btnPdf.addEventListener("click", () => {
            window.open(urlWithDates("/api/manager/albaran/summary/pdf/"), "_blank");
        });
    }

    // Carga inicial
    loadOrders();
});