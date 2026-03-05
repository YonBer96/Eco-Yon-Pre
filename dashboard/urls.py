from django.urls import path
from . import views


urlpatterns = [
    # Página principal del dashboard
    # Ej: /dashboard/
    path("", views.dashboard_home, name="dashboard_home"),

    # Listado de productos en el dashboard
    # Ej: /dashboard/products/
    path("products/", views.product_list, name="dashboard_products"),

    # Crear nuevo producto desde el dashboard
    # Ej: /dashboard/products/new/
    path("products/new/", views.product_create, name="dashboard_product_create"),
]
