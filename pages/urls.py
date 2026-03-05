from django.urls import path
from . import views

urlpatterns = [
    # Página de login
    # /login/
    path("login/", views.login_page, name="login_page"),

    # Página de registro
    # /register/
    path("register/", views.register_page, name="register_page"),

    # Catálogo de productos
    # /products/
    path("products/", views.products_page, name="products_page"),

    # Carrito de la compra
    # /cart/
    path("cart/", views.cart_page, name="cart_page"),

    # Pedidos del usuario
    # /my-orders/
    path("my-orders/", views.my_orders_page, name="my_orders_page"),

    # Checkout (finalizar compra)
    # /checkout/
    path("checkout/", views.checkout_page, name="checkout_page"),
]
