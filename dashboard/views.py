from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages

from catalog.models import Product
from .forms import ProductCreateForm


# =========================
# CONTROL DE ACCESO
# =========================

def is_manager(user):
    """
    Comprueba si el usuario es un encargado.

    Un encargado es:
    - usuario autenticado
    - con is_staff = True
    """
    return user.is_authenticated and user.is_staff


# Decorador que protege las vistas del dashboard
# Si no cumple is_manager, redirige a /login/
manager_required = user_passes_test(is_manager, login_url="/staff/login/")


# =========================
# VISTAS DEL DASHBOARD
# =========================

@manager_required
def dashboard_home(request):
    """
    Página principal del dashboard.
    """
    return render(request, "dashboard/home.html")


@manager_required
def product_list(request):
    """
    Listado de productos para el encargado.

    Permite:
    - buscar por nombre
    - filtrar por tipo (FRUTA / VERDURA)
    """

    # Parámetros de búsqueda desde la URL
    q = (request.GET.get("q") or "").strip()
    ptype = (request.GET.get("product_type") or "").strip()

    # Base: todos los productos, más recientes primero
    qs = Product.objects.all().order_by("-id")

    # Filtrar por tipo si es válido
    if ptype in ("FRUTA", "VERDURA"):
        qs = qs.filter(product_type=ptype)

    # Filtrar por nombre
    if q:
        qs = qs.filter(name__icontains=q)

    return render(
        request,
        "dashboard/products_list.html",
        {
            "products": qs,
            "q": q,
            "ptype": ptype
        },
    )


@manager_required
def product_create(request):
    """
    Crear un nuevo producto desde el dashboard.

    - GET  → muestra formulario
    - POST → valida y guarda el producto
    """

    if request.method == "POST":
        # Formulario con datos y archivos (imagen)
        form = ProductCreateForm(request.POST, request.FILES)

        if form.is_valid():
            # Guarda el producto en base de datos
            form.save()
            messages.success(request, "Producto creado correctamente ✅")
            return redirect("dashboard_products")

        # Si hay errores en el formulario
        messages.error(request, "Revisa el formulario.")

    else:
        # Formulario vacío
        form = ProductCreateForm()

    return render(request, "dashboard/product_create.html", {"form": form})


# =========================
# ALIAS DE NOMBRES (opcional)
# =========================

# Permiten usar estos nombres directamente en urls.py si se desea
dashboard_products = product_list
dashboard_product_create = product_create
