from decimal import Decimal

from django.conf import settings
from decimal import Decimal
from datetime import timedelta
from io import BytesIO

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.dateparse import parse_date

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from xhtml2pdf import pisa

from .models import Order, OrderItem
from catalog.models import Product

# =====================================================
# UTILS (FUNCIONES DE APOYO)
# =====================================================

@transaction.atomic
def get_cart(user):
    """
    Obtiene el carrito activo del usuario (status = CART).
    Si no existe, lo crea.

    select_for_update bloquea la fila para evitar carritos duplicados
    en peticiones simultáneas.
    """
    cart = (
        Order.objects.select_for_update()
        .filter(user=user, status="CART")
        .order_by("-id")
        .first()
    )
    if cart:
        return cart

    return Order.objects.create(user=user, status="CART")


def cart_snapshot(cart):
    """
    Convierte el carrito en un diccionario JSON listo para el frontend.
    Se usa para mantener siempre sincronizado el estado del carrito.
    """
    items = cart.items.select_related("product").all()

    return {
        "id": cart.id,
        "status": cart.status,
        "items_count": items.count(),
        "items": [
            {
                "id": it.id,
                "product_id": it.product.id,
                "name": it.product.name,
                "price": str(it.product.price),
                "unit": it.product.unit,
                "quantity": str(it.quantity),
                "subtotal": str(it.subtotal),
            }
            for it in items
        ],
        "subtotal": str(cart.subtotal_amount),
        "vat": str(cart.vat_amount),
        "total": str(cart.total_amount),
    }


# =====================================================
# CARRITO
# =====================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cart_detail(request):
    """
    Devuelve el carrito actual del usuario.
    """
    cart = get_cart(request.user)
    return Response(cart_snapshot(cart))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def add_to_cart(request):
    """
    Añade un producto al carrito o incrementa su cantidad.
    """
    product_id = request.data.get("product_id")
    quantity = request.data.get("quantity")

    if not product_id or quantity is None:
        return Response({"detail": "Datos incompletos"}, status=400)

    # Validación de cantidad
    try:
        qty = int(quantity)
        if qty <= 0:
            raise ValueError
    except Exception:
        return Response({"detail": "Cantidad inválida"}, status=400)

    # Bloquea producto para validar stock de forma segura
    product = (
        Product.objects.select_for_update()
        .filter(id=product_id, is_active=True)
        .first()
    )
    if not product:
        return Response({"detail": "Producto no encontrado"}, status=404)

    if product.stock < qty:
        return Response({"detail": "Stock insuficiente"}, status=400)

    cart = get_cart(request.user)

    # Bloquea item si ya existe
    item = (
        OrderItem.objects.select_for_update()
        .filter(order=cart, product=product)
        .first()
    )

    if item:
        if product.stock < (item.quantity + qty):
            return Response({"detail": "Stock insuficiente"}, status=400)
        item.quantity += qty
        item.save()
    else:
        OrderItem.objects.create(order=cart, product=product, quantity=qty)

    cart.refresh_from_db()
    return Response({
        "detail": "Producto añadido",
        "cart": cart_snapshot(cart),
    })


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def update_item(request, item_id):
    """
    Modifica la cantidad de un producto del carrito.
    """
    item = (
        OrderItem.objects.select_for_update()
        .select_related("product", "order")
        .filter(id=item_id, order__user=request.user, order__status="CART")
        .first()
    )
    if not item:
        return Response({"detail": "Item no encontrado"}, status=404)

    try:
        qty = int(request.data.get("quantity"))
        if qty <= 0:
            raise ValueError
    except Exception:
        return Response({"detail": "Cantidad inválida"}, status=400)

    product = Product.objects.select_for_update().filter(id=item.product_id).first()
    if product.stock < qty:
        return Response({"detail": "Stock insuficiente"}, status=400)

    item.quantity = qty
    item.save()

    cart = item.order
    cart.refresh_from_db()

    return Response({
        "detail": "Actualizado",
        "cart": cart_snapshot(cart),
    })


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
@transaction.atomic
def delete_item(request, item_id):
    """
    Elimina un producto del carrito.
    """
    item = (
        OrderItem.objects.select_for_update()
        .select_related("order")
        .filter(id=item_id, order__user=request.user, order__status="CART")
        .first()
    )
    if not item:
        return Response({"detail": "Item no encontrado"}, status=404)

    cart = item.order
    item.delete()

    cart.refresh_from_db()
    return Response({
        "detail": "Eliminado",
        "cart": cart_snapshot(cart),
    })


# =====================================================
# CHECKOUT
# =====================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def checkout(request):
    """
    Convierte el carrito en pedido real.
    - Valida datos
    - Descuenta stock
    - Cambia estado a PENDING
    """
    cart = get_cart(request.user)

    if not cart.items.exists():
        return Response({"detail": "Carrito vacío"}, status=400)

    data = request.data or {}

    # Datos de facturación
    cart.company_name = (data.get("company_name") or "").strip()
    cart.company_cif = (data.get("company_cif") or "").strip()
    cart.company_address = (data.get("company_address") or "").strip()

    # Pago
    cart.payment_method = (data.get("payment_method") or "card").strip()
    cart.paid = cart.payment_method == "card"

    # Entrega
    delivery_method = (data.get("delivery_method") or "PICKUP").strip().upper()
    if delivery_method not in ("PICKUP", "DELIVERY"):
        return Response({"detail": "Método de entrega inválido"}, status=400)

    delivery_slot = (data.get("delivery_slot") or "").strip()
    delivery_address = (data.get("delivery_address") or "").strip()

    if delivery_method == "DELIVERY" and not delivery_address:
        return Response({"detail": "La dirección es obligatoria"}, status=400)

    cart.delivery_method = delivery_method
    cart.delivery_slot = delivery_slot
    cart.delivery_address = delivery_address if delivery_method == "DELIVERY" else ""

    # Descuento real de stock
    for item in cart.items.select_for_update().select_related("product"):
        if item.product.stock < item.quantity:
            return Response({"detail": f"Stock insuficiente para {item.product.name}"}, status=400)
        item.product.stock -= item.quantity
        item.product.save()

    cart.status = "PENDING"
    cart.save()

    return Response({"detail": "Pedido confirmado", "order_id": cart.id})


# =====================================================
# PEDIDOS DEL CLIENTE
# =====================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_orders(request):
    """
    Devuelve todos los pedidos del usuario autenticado.
    """
    qs = (
        Order.objects.filter(user=request.user)
        .exclude(status="CART")
        .prefetch_related("items__product")
        .order_by("-created_at")
    )

    return Response([
        {
            "id": o.id,
            "status": o.status,
            "paid": o.paid,
            "total": str(o.total),
            "created_at": o.created_at,
            "items": [
                {
                    "product": it.product.name,
                    "qty": str(it.quantity),
                    "unit": it.product.unit,
                }
                for it in o.items.all()
            ],
        }
        for o in qs
    ])


# =====================================================
# FACTURAS
# =====================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def invoice(request, order_id):
    """
    Devuelve la factura en HTML.
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)
    html = render_to_string("invoices/invoice.html", {"order": order})
    return HttpResponse(html)


def render_pdf_from_html(html: str) -> bytes:
    """
    Convierte HTML en PDF usando xhtml2pdf.
    """
    result = BytesIO()
    pisa.CreatePDF(html, dest=result, encoding="utf-8")
    return result.getvalue()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def invoice_pdf(request, order_id):
    """
    Genera y devuelve la factura en PDF.
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)
    html = render_to_string("invoices/invoice_pdf.html", {"order": order})

    try:
        pdf_bytes = render_pdf_from_html(html)
    except Exception:
        return Response({"detail": "No se pudo generar el PDF"}, status=500)

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="factura_{order.id}.pdf"'
    return response


# =====================================================
# MANAGER
# =====================================================

@api_view(["POST", "PATCH"])
@permission_classes([IsAdminUser])
def manager_set_status(request, order_id):
    """
    Permite al encargado cambiar el estado de un pedido.
    """
    order = get_object_or_404(Order, id=order_id)

    status = request.data.get("status")
    valid = ["PENDING", "PREPARING", "READY", "IN_TRANSIT", "DONE", "CANCELLED"]

    if status not in valid:
        return Response({"detail": "Estado inválido"}, status=400)

    order.status = status
    order.save()

    return Response({"detail": "Estado actualizado"})


def _current_week_range():
    now = timezone.localtime()
    monday = (now - timedelta(days=now.weekday())).date()
    sunday = monday + timedelta(days=6)
    return monday, sunday


def _get_range_from_request(request):
    start_str = request.GET.get("start")
    end_str = request.GET.get("end")

    if start_str and end_str:
        start = parse_date(start_str)
        end = parse_date(end_str)
    else:
        start, end = _current_week_range()

    if not start or not end or start > end:
        return None, None, "Rango inválido"

    return start, end, None


@api_view(["GET"])
@permission_classes([IsAdminUser])
def manager_orders(request):
    """
    Pedidos de TODOS los usuarios (no CART) filtrables por rango.
    Por defecto: semana actual.
    """
    start, end, error = _get_range_from_request(request)
    if error:
        return Response({"detail": error}, status=400)

    qs = (
        Order.objects
        .exclude(status="CART")
        .filter(created_at__date__gte=start, created_at__date__lte=end)
        .select_related("user")
        .prefetch_related("items__product")
        .order_by("-created_at")
    )

    return Response({
        "start": str(start),
        "end": str(end),
        "orders": [
            {
                "id": o.id,
                "created_at": o.created_at,
                "status": o.status,
                "paid": o.paid,
                "total": str(o.total_amount),
                "user": {
                    "id": o.user_id,
                    "username": o.user.username,
                },
                "items": [
                    {
                        "product": it.product.name,
                        "qty": str(it.quantity),
                        "unit": it.product.unit,
                    }
                    for it in o.items.all()
                ],
            }
            for o in qs
        ]
    })

@api_view(["GET"])
@permission_classes([IsAdminUser])
def manager_albaran_summary(request):
    start, end, error = _get_range_from_request(request)
    if error:
        return Response({"detail": error}, status=400)

    valid_statuses = ["PENDING", "PREPARING", "READY", "IN_TRANSIT", "DONE"]

    items = (
        OrderItem.objects
        .filter(order__status__in=valid_statuses)
        .filter(order__created_at__date__gte=start, order__created_at__date__lte=end)
        .values("product__name", "product__unit")
        .annotate(total_qty=Sum("quantity"))
        .order_by("product__name")
    )

    html = render_to_string("orders/manager_albaran_summary.html", {
        "start": start,
        "end": end,
        "items": list(items),
        "generated_at": timezone.localtime(),
    })

    return HttpResponse(html)

@api_view(["GET"])
@permission_classes([IsAdminUser])
def manager_albaran_summary_pdf(request):
    start, end, error = _get_range_from_request(request)
    if error:
        return Response({"detail": error}, status=400)

    valid_statuses = ["PENDING", "PREPARING", "READY", "IN_TRANSIT", "DONE"]

    items = (
        OrderItem.objects
        .filter(order__status__in=valid_statuses)
        .filter(order__created_at__date__gte=start, order__created_at__date__lte=end)
        .values("product__name", "product__unit")
        .annotate(total_qty=Sum("quantity"))
        .order_by("product__name")
    )

    html = render_to_string("orders/manager_albaran_summary_pdf.html", {
        "start": start,
        "end": end,
        "items": list(items),
        "generated_at": timezone.localtime(),
    })

    try:
        pdf_bytes = render_pdf_from_html(html)
    except Exception:
        return Response({"detail": "No se pudo generar el PDF"}, status=500)

    filename = f'albaran_conjunto_{start}_{end}.pdf'
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response

