// Escapa texto para evitar inyectar HTML al usar innerHTML (protección básica XSS)
function esc(str) {
    return String(str ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

// Formatea valores como euros (2 decimales)
function moneyEUR(v) {
    const n = Number(v);
    if (Number.isNaN(n)) return `${v}€`;
    return `${n.toFixed(2)}€`;
}

// Escribe HTML dentro del contenedor del grid
function showInGrid(html) {
    const grid = document.getElementById("productsGrid");
    if (grid) grid.innerHTML = html;
}

// Lee filtros desde inputs del DOM: búsqueda y tipo
function getFilters() {
    const q = (document.getElementById("searchInput")?.value || "").trim();
    const product_type = document.getElementById("typeSelect")?.value || "";
    return { q, product_type };
}

async function loadProducts() {
    // En tu proyecto, ver productos requiere login (IsAuthenticated en backend)
    // Por eso si no hay token, mandas a /login/
    const token = localStorage.getItem("access_token");

    // Estado “cargando”
    showInGrid(`<p class="muted">Cargando productos…</p>`);

    // Construye query string a partir de filtros
    const { q, product_type } = getFilters();
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (product_type) params.set("product_type", product_type);

    const qs = params.toString();
    const url = `${API_URL}/products/${qs ? "?" + qs : ""}`;

    // Llama a la API usando el wrapper apiFetch (mete JWT y maneja 401)
    const res = await apiFetch(url);
    if (!res) return;

    // Error de backend
    if (!res.ok) {
        showInGrid(`<p class="muted">No se pudieron cargar los productos.</p>`);
        return;
    }

    // Lista de productos JSON
    const items = await res.json();

    // Sin resultados
    if (!items.length) {
        showInGrid(`<p class="muted">No hay productos que coincidan.</p>`);
        return;
    }

    const grid = document.getElementById("productsGrid");
    grid.innerHTML = "";

    // Pinta cada producto como una tarjeta
    items.forEach((p) => {
        const card = document.createElement("div");
        card.className = "card";
        card.style.position = "relative";

        // Si hay imagen, la mostramos
        const imgHtml = p.image
            ? `<img src="${p.image}" alt="${esc(p.name)}"
             style="width:100%; height:160px; object-fit:cover; border-radius:12px; margin-bottom:10px;">`
            : "";

        // Calculamos el estado del stock (agotado / bajo / ok)
        const stockNum = Number(p.stock);
        const isOut = !Number.isFinite(stockNum) ? false : stockNum <= 0;
        const isLow = !isOut && Number.isFinite(stockNum) && stockNum <= 5;

        // Badge visual según stock
        const badgeHtml = isOut
            ? `<div class="badge badge--out">Agotado</div>`
            : isLow
                ? `<div class="badge badge--low">Últimas unidades</div>`
                : "";

        // Montamos HTML de la tarjeta
        card.innerHTML = `
        ${badgeHtml}
        ${imgHtml}
        <h3>${esc(p.name)}</h3>
        <div class="price">${moneyEUR(p.price)}</div>

        <div style="display:flex; gap:10px; align-items:center; margin-top:10px">
            <input
                type="number"
                min="1"
                step="1"
                value="1"
                id="qty-${p.id}"
                style="width:80px"
                ${isOut ? "disabled" : ""}
            >
            <button
                class="btn btn--primary"
                type="button"
                data-add="${p.id}"
                ${isOut ? "disabled style='opacity:0.55; cursor:not-allowed'" : ""}
            >
                 ${isOut ? "Agotado" : "🧺 Añadir"}
            </button>
         </div>
     `;

        grid.appendChild(card);
    });

    // Bind de botones “Añadir”
    grid.querySelectorAll("[data-add]").forEach((btn) => {
        btn.onclick = async () => {
            const productIdRaw = btn.dataset.add;
            const productId = parseInt(productIdRaw, 10);

            // Validación rápida del id
            if (!Number.isFinite(productId) || productId <= 0) {
                toast("Producto inválido", "error");
                return;
            }

            // Lee cantidad del input
            const qtyEl = document.getElementById(`qty-${productId}`);
            const raw = qtyEl ? String(qtyEl.value).trim() : "1";

            // Cantidad (entera)
            let qty = parseInt(raw, 10);
            if (!Number.isFinite(qty) || qty <= 0) qty = 1;

            // Evita doble click
            const prev = btn.textContent;
            btn.disabled = true;
            btn.textContent = "Añadiendo…";

            // Llama a la API para añadir al carrito
            const resAdd = await apiFetch(`${API_URL}/cart/add/`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ product_id: productId, quantity: qty }),
            });

            // Restaurar UI
            btn.disabled = false;
            btn.textContent = prev;

            if (!resAdd) return;

            const data = await resAdd.json().catch(() => ({}));

            // Error de stock / validación
            if (!resAdd.ok) {
                toast(data.detail || "No se pudo añadir", "error");
                return;
            }

            toast("Añadido al carrito ✅", "success");
        };
    });
}

// Arranque al cargar la página: listeners + cargar productos
document.addEventListener("DOMContentLoaded", () => {
    const search = document.getElementById("searchInput");
    const typeSelect = document.getElementById("typeSelect");
    const clearBtn = document.getElementById("btnClear");

    // Debounce para búsqueda (evita llamar API en cada tecla)
    if (search) {
        let t;
        search.addEventListener("input", () => {
            clearTimeout(t);
            t = setTimeout(loadProducts, 220);
        });
    }

    // Cambio de filtro por tipo
    if (typeSelect) typeSelect.addEventListener("change", loadProducts);

    // Botón limpiar filtros
    if (clearBtn) {
        clearBtn.addEventListener("click", () => {
            if (search) search.value = "";
            if (typeSelect) typeSelect.value = "";
            loadProducts();
        });
    }

    // Primera carga
    loadProducts();
});
