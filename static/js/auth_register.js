// Captura el envío del formulario de registro
document.getElementById("registerForm").addEventListener("submit", async (e) => {
    e.preventDefault(); // Evita recargar la página

    const form = e.target;

    // Obtiene los datos del formulario
    const username = form.username.value.trim();
    const email = form.email.value.trim();
    const password = form.password.value;

    // Llamada a la API para crear un nuevo usuario
    const res = await fetch(`${API_URL}/register/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, email, password })
    });

    const msg = document.getElementById("registerMsg");
    const data = await res.json();

    // Si hay error en el registro
    if (!res.ok) {
        msg.textContent = data.detail || "Error registrando";
        return;
    }

    // Mensaje de éxito
    msg.textContent = "Usuario creado. Ahora inicia sesión.";

    // Redirige al login tras un pequeño retraso
    setTimeout(() => window.location.href = "/login/", 800);
});
