document.getElementById("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const form = e.target;
    const username = form.username.value.trim();
    const password = form.password.value;

    const res = await fetch("/api/token/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
    });

    const msg = document.getElementById("loginMsg");
    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
        msg.textContent = data.detail || "Error al iniciar sesión";
        return;
    }

    localStorage.setItem("access_token", data.access);
    localStorage.setItem("refresh_token", data.refresh);

    window.location.href = "/products/";
});