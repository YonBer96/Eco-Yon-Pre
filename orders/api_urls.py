from django.urls import path
from . import api_views
from . import manager_api_views as m   # Endpoints exclusivos para el encargado


from .api_views import manager_albaran_summary, manager_albaran_summary_pdf
from orders.api_views import manager_orders


urlpatterns = [

    # ======================================================
    # 🛒 ECOMMERCE (CLIENTE)
    # ======================================================

    # Obtener el carrito actual del usuario
    # GET /api/cart/
    path("cart/", api_views.cart_detail),

    # Añadir un producto al carrito
    # POST /api/cart/add/
    path("cart/add/", api_views.add_to_cart),

    # Actualizar cantidad de un producto del carrito
    # PATCH /api/cart/item/<id>/
    path("cart/item/<int:item_id>/", api_views.update_item),

    # Eliminar un producto del carrito
    # DELETE /api/cart/item/<id>/delete/
    path("cart/item/<int:item_id>/delete/", api_views.delete_item),

    # Finalizar compra (convertir carrito en pedido)
    # POST /api/checkout/
    path("checkout/", api_views.checkout),

    # Obtener pedidos del usuario logueado
    # GET /api/my-orders/
    path("my-orders/", api_views.my_orders),


    # ======================================================
    # 🧾 FACTURAS
    # ======================================================

    # Ver factura en HTML
    # GET /api/invoice/<order_id>/
    path("invoice/<int:order_id>/", api_views.invoice),

    # Descargar factura en PDF
    # GET /api/invoice/<order_id>/pdf/
    path("invoice/<int:order_id>/pdf/", api_views.invoice_pdf),


    # ======================================================
    # 🧑‍💼 MANAGER / ENCARGADO
    # ======================================================

    # Listar todos los pedidos (vista de encargado)
    # GET /api/manager/orders/
    path("manager/orders/", m.manager_orders),

    # Cambiar el estado de un pedido
    # PATCH /api/manager/orders/<order_id>/status/
    path("manager/orders/<int:order_id>/status/", api_views.manager_set_status),

    # Generar albarán en HTML
    # GET /api/manager/orders/<order_id>/albaran/
    path("manager/orders/<int:order_id>/albaran/", m.manager_albaran_html),

    # Listar clientes
    # GET /api/manager/customers/
    path("manager/customers/", m.manager_customers),

    # Ver pedidos de un cliente concreto
    # GET /api/manager/customers/<user_id>/orders/
    path("manager/customers/<int:user_id>/orders/", m.manager_customer_orders),

    # Descargar ZIP con todos los albaranes
    # GET /api/manager/albaranes/zip/
    path("manager/albaranes/zip/", m.manager_albaranes_zip),

    path("manager/albaran/summary/", manager_albaran_summary, name="manager_albaran_summary"),
    path("manager/albaran/summary/pdf/", manager_albaran_summary_pdf, name="manager_albaran_summary_pdf"),
    path("manager/orders/", manager_orders, name="manager_orders"),
]
