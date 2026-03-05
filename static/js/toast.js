(function () {
    // Se asegura de que exista el contenedor de toasts en el DOM
    function ensureWrap() {
        let wrap = document.querySelector(".toast-wrap");
        if (!wrap) {
            wrap = document.createElement("div");
            wrap.className = "toast-wrap";
            document.body.appendChild(wrap);
        }
        return wrap;
    }

    // Devuelve el icono según tipo de mensaje
    function iconFor(type) {
        if (type === "success") return "✅";
        if (type === "error") return "⛔";
        if (type === "warn") return "⚠️";
        return "ℹ️";
    }

    // Devuelve el título según tipo
    function titleFor(type) {
        if (type === "success") return "Hecho";
        if (type === "error") return "Ups";
        if (type === "warn") return "Ojo";
        return "Info";
    }

    // Hace global la función toast()
    window.toast = function toast(message, type = "info", opts = {}) {
        const wrap = ensureWrap();
        const el = document.createElement("div");
        el.className = `toast toast--${type}`;

        // Tiempo visible del toast (ms)
        const duration = opts.duration ?? 2200;

        // HTML del toast
        el.innerHTML = `
      <div class="icon">${iconFor(type)}</div>
      <div>
        <p class="title">${titleFor(type)}</p>
        <p class="msg">${String(message ?? "")}</p>
      </div>
      <button class="close" aria-label="Cerrar">✕</button>
    `;

        // Cierre manual o automático
        const close = () => {
            el.style.animation = "toastOut .16s ease forwards";
            setTimeout(() => el.remove(), 160);
        };

        el.querySelector(".close").addEventListener("click", close);
        wrap.prepend(el);

        // Autocierre
        if (duration > 0) setTimeout(close, duration);
    };
})();
