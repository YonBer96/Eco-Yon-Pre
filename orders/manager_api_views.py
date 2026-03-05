from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .models import Order

import io
import zipfile

from datetime import timedelta
from django.db.models import Sum
from django.http import HttpResponse
from django.template.loader import get_template
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from xhtml2pdf import pisa

from orders.models import OrderItem

# Modelo de usuario activo (por si en el futuro usas uno personalizado)
User = get_user_model()


# =====================================================
# PEDIDOS (VISTA ENCARGADO)
# =====================================================

@api_view(["GET"])
@permission_classes([IsAdminUser])
def manager_orders(request):
    """
    Devuelve la lista de pedidos para el dashboard del encargado.

    Soporta filtros por query params:
      - ?status=PENDING|PREPARING|READY|IN_TRANSIT|DONE|CANCELLED
      - ?q=<id de pedido o username>
    """

    status = (request.query_params.get("status") or "").strip().upper()
    q = (request.query_params.get("q") or "").strip()

    # Base: todos los pedidos reales (no carritos)
    qs = (
        Order.objects.exclude(status="CART")
        .select_related("user")
        .prefetch_related("items__product")
        .order_by("-created_at")
    )

    # Filtrar por estado
    if status:
        qs = qs.filter(status=status)

    # Buscar por id de pedido o por nombre de usuario
    if q:
        if q.isdigit():
            qs = qs.filter(id=int(q))
        else:
            qs = qs.filter(user__username__icontains=q)

    # Respuesta adaptada a la UI del dashboard
    return Response([
        {
            "id": o.id,
            "user": o.user.username,
            "status": o.status,
            "paid": o.paid,
            "total": str(o.total),
            "created_at": o.created_at,

            # Campos usados por la interfaz
            "delivery_method": getattr(o, "delivery_method", None),
            "delivery_slot": getattr(o, "delivery_slot", None),
        }
        for o in qs
    ])


# =====================================================
# CLIENTES
# =====================================================

@api_view(["GET"])
@permission_classes([IsAdminUser])
def manager_customers(request):
    """
    Devuelve la lista de clientes (usuarios no staff).
    Se usa para el panel de clientes del encargado.
    """
    qs = User.objects.filter(is_staff=False).order_by("username")

    return Response([
        {"id": u.id, "username": u.username, "email": u.email}
        for u in qs
    ])


@api_view(["GET"])
@permission_classes([IsAdminUser])
def manager_customer_orders(request, user_id):
    """
    Devuelve los pedidos de un cliente concreto.

    IMPORTANTE: el frontend necesita:
    - status
    - paid
    - total
    """
    u = get_object_or_404(User, id=user_id, is_staff=False)

    qs = (
        Order.objects.filter(user=u)
        .exclude(status="CART")
        .order_by("-created_at")
    )

    return Response([
        {
            "id": o.id,
            "status": o.status,
            "paid": o.paid,
            "total": str(o.total),
            "created_at": o.created_at,
        }
        for o in qs
    ])


# =====================================================
# ALBARANES
# =====================================================

@api_view(["GET"])
@permission_classes([IsAdminUser])
def manager_albaran_html(request, order_id):
    """
    Devuelve el albarán de un pedido en HTML.

    Se abre con fetch + JWT (no con enlace normal),
    para evitar problemas de autenticación.
    """
    order = get_object_or_404(
        Order.objects.select_related("user").prefetch_related("items__product"),
        id=order_id
    )

    html = render_to_string("invoices/albaran.html", {"order": order})
    return HttpResponse(html)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def manager_albaranes_zip(request):
    """
    Genera y descarga un ZIP con albaranes HTML.

    Permite filtrar por estado:
      /api/manager/albaranes/zip/?status=PREPARING

    Si no se indica estado, incluye todos excepto CART.
    """

    status = (request.query_params.get("status") or "").strip().upper()

    qs = (
        Order.objects.exclude(status="CART")
        .select_related("user")
        .prefetch_related("items__product")
        .order_by("-created_at")
    )

    if status:
        qs = qs.filter(status=status)

    # Buffer en memoria para el ZIP
    buf = io.BytesIO()

    # Creamos el ZIP
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for o in qs:
            html = render_to_string("invoices/albaran.html", {"order": o})
            filename = f"albaran_{o.id}_{o.user.username}.html"
            z.writestr(filename, html)

    buf.seek(0)

    # Nombre del archivo con fecha
    stamp = timezone.now().strftime("%Y%m%d_%H%M")
    name = f"albaranes_{status or 'ALL'}_{stamp}.zip"

    resp = HttpResponse(buf.getvalue(), content_type="application/zip")
    resp["Content-Disposition"] = f'attachment; filename="{name}"'
    return resp



def _current_week_range():
    # Semana actual: lunes a domingo (en la TZ del proyecto: Europe/Madrid)
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
        return None, None, "Rango de fechas inválido. Usa start=YYYY-MM-DD&end=YYYY-MM-DD"

    return start, end, None

def _summary_queryset(start, end):
    valid_statuses = ["PENDING", "PREPARING", "READY", "IN_TRANSIT", "DONE"]

    return (
        OrderItem.objects
        .filter(order__status__in=valid_statuses)
        .filter(order__created_at__date__gte=start, order__created_at__date__lte=end)
        .values("product__name", "product__unit")
        .annotate(total_qty=Sum("quantity"))
        .order_by("product__name")
    )

@api_view(["GET"])
@permission_classes([IsAdminUser])
def manager_albaran_summary(request):
    start, end, error = _get_range_from_request(request)
    if error:
        return HttpResponse(error, status=400)

    items = _summary_queryset(start, end)

    # HTML
    template = get_template("orders/manager_albaran_summary.html")
    html = template.render({"start": start, "end": end, "items": items})
    return HttpResponse(html)

@api_view(["GET"])
@permission_classes([IsAdminUser])
def manager_albaran_summary_pdf(request):
    start, end, error = _get_range_from_request(request)
    if error:
        return HttpResponse(error, status=400)

    items = _summary_queryset(start, end)

    template = get_template("orders/manager_albaran_summary_pdf.html")
    html = template.render({"start": start, "end": end, "items": items})

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="albaran_conjunto_{start}_{end}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse("Error generando PDF", status=500)

    return response

@api_view(["GET"])
@permission_classes([IsAdminUser])
def manager_orders(request):
    start, end, error = _get_range_from_request(request)  # ya lo tienes
    if error:
        return Response({"detail": error}, status=400)

    valid_statuses = ["PENDING", "PREPARING", "READY", "IN_TRANSIT", "DONE", "CANCELLED"]

    qs = (
        Order.objects
        .exclude(status="CART")
        .filter(status__in=valid_statuses)
        .filter(created_at__date__gte=start, created_at__date__lte=end)
        .prefetch_related("items__product", "user")
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
                    "username": getattr(o.user, "username", ""),
                },
                "items": [
                    {"product": it.product.name, "qty": str(it.quantity), "unit": it.product.unit}
                    for it in o.items.all()
                ]
            }
            for o in qs
        ]
    })