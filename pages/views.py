from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

def login_page(request):
    """
    Login clásico de Django (sesión/cookie).

    Esto es imprescindible para entrar a vistas HTML protegidas
    con @manager_required (dashboard).

    Soporta ?next=/ruta/ para redirigir después de iniciar sesión.
    """

    # next puede venir por GET (cuando Django redirige) o por POST (hidden input)
    next_url = request.GET.get("next") or request.POST.get("next") or "/products/"

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""

        user = authenticate(request, username=username, password=password)

        # Credenciales incorrectas
        if user is None:
            messages.error(request, "Usuario o contraseña incorrectos.")
            return render(request, "pages/login.html", {"next": next_url})

        # Si el usuario intenta entrar al dashboard, debe ser staff
        if next_url.startswith("/dashboard") and not user.is_staff:
            messages.error(request, "No tienes permisos para acceder al dashboard.")
            return render(request, "pages/login.html", {"next": next_url})

        #  Crea sesión Django (cookie sessionid)
        login(request, user)

        return redirect(next_url)

    return render(request, "pages/login.html", {"next": next_url})


def register_page(request):
    return render(request, "pages/register.html")

def products_page(request):
    return render(request, "pages/products.html")

def cart_page(request):
    return render(request, "pages/cart.html")

def my_orders_page(request):
    return render(request, "pages/my_orders.html")

def checkout_page(request):
    return render(request, "pages/checkout.html")

