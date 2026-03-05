// checkout.js
//  No exigimos JWT: si hay sesión Django, debe funcionar igualmente.
//  Si hay JWT, apiFetch lo usará.
//  Si NO hay JWT, apiFetch usará cookie de sesión y añadirá CSRF en POST.

document.addEventListener("DOMContentLoaded", () => {
    // Botón de confirmar pedido
    document.getElementById("confirmBtn").addEventListener("click", confirmOrder);

    // Referencias a los campos de entrega
    const method = document.getElementById("delivery_method");
    const addr = document.getElementById("delivery_address");

    // Si cambia el método de entrega:
    // - si es DELIVERY: activamos el input de dirección
    // - si es PICKUP: desactivamos y limpiamos la dirección
    method.addEventListener("change", () => {
        const isDelivery = method.value === "DELIVERY";
        addr.disabled = !isDelivery;
        if (!isDelivery) addr.value = "";
    });

    // Ejecuta el change al cargar para dejar el estado inicial correcto
    method.dispatchEvent(new Event("change"));
});

async function confirmOrder() {
    // Datos de entrega
    const delivery_method = document.getElementById("delivery_method").value;
    const delivery_slot = document.getElementById("delivery_slot").value;
    const delivery_address = document.getElementById("delivery_address").value.trim();

    // Validación mínima en frontend: si es envío, debe haber dirección
    if (delivery_method === "DELIVERY" && !delivery_address) {
        toast("Pon una dirección para el envío.", "warn");
        return;
    }

    // Construimos el cuerpo que espera la API de checkout
    const body = {
        // Datos de facturación (empresa)
        company_name: document.getElementById("company_name").value,
        company_cif: document.getElementById("company_cif").value,
        company_address: document.getElementById("company_address").value,

        // Método de pago
        payment_method: document.getElementById("payment_method").value,

        // Datos de entrega
        delivery_method,
        delivery_slot,
        delivery_address,
    };

    //  Llamada a la API usando apiFetchParsed (JWT si existe, si no sesión + CSRF)
    const { res, data } = await apiFetchParsed(`${API_URL}/checkout/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        redirectOn401: true, // checkout es zona protegida: si 401 real, fuera
    });

    // Si es 401, apiFetch ya habrá limpiado JWT y redirigido si toca
    if (res.status === 401) return;

    // Si el backend devuelve error
    if (!res.ok) {
        const msg =
            (data && data.detail) ? data.detail :
                "No se pudo confirmar el pedido.";
        toast(msg, "error");
        return;
    }

    // Éxito: mensaje y redirección
    toast("Pedido confirmado ✅", "success");
    setTimeout(() => (window.location.href = "/my-orders/"), 700);
}
