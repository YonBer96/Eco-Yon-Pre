from django.conf import settings
from django.db import models
from decimal import Decimal

# Referencia al modelo de usuario activo del proyecto
User = settings.AUTH_USER_MODEL


class Order(models.Model):
    """
    Representa un pedido.

    Mientras status = "CART", actúa como carrito.
    Cuando pasa a PENDING o superior, es un pedido real.
    """

    # Estados posibles del pedido
    STATUS_CHOICES = [
        ("CART", "Carrito"),
        ("PENDING", "Pendiente"),
        ("PREPARING", "Preparando"),
        ("READY", "Listo"),
        ("IN_TRANSIT", "En camino"),
        ("DONE", "Entregado"),
        ("CANCELLED", "Cancelado"),
    ]

    # Usuario dueño del pedido/carrito
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Estado actual del pedido
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="CART")

    # Fecha de creación
    created_at = models.DateTimeField(auto_now_add=True)


    # =========================
    # DATOS DE FACTURACIÓN
    # =========================

    company_name = models.CharField(max_length=150, blank=True)
    company_cif = models.CharField(max_length=50, blank=True)
    company_address = models.CharField(max_length=200, blank=True)

    # Porcentaje de IVA aplicado al pedido
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("21.00"))


    # =========================
    # PAGO
    # =========================

    payment_method = models.CharField(max_length=50, blank=True)
    paid = models.BooleanField(default=False)


    # =========================
    # FACTURA
    # =========================

    invoice_number = models.CharField(max_length=32, blank=True, null=True, unique=True)
    invoice_issued_at = models.DateTimeField(blank=True, null=True)


    # =========================
    # ENTREGA
    # =========================

    DELIVERY_CHOICES = [
        ("PICKUP", "Recogida en tienda"),
        ("DELIVERY", "Envío a domicilio"),
    ]

    delivery_method = models.CharField(max_length=20, choices=DELIVERY_CHOICES, default="PICKUP")
    delivery_slot = models.CharField(max_length=60, blank=True, default="")
    delivery_address = models.CharField(max_length=220, blank=True, default="")


    # =========================
    # CÁLCULOS
    # =========================

    @property
    def subtotal_amount(self):
        """
        Suma de los subtotales de todos los productos del pedido.
        """
        return sum((item.subtotal for item in self.items.all()), Decimal("0"))

    @property
    def vat_amount(self):
        """
        Importe del IVA calculado sobre el subtotal.
        """
        rate = self.vat_rate or Decimal("0")
        return self.subtotal_amount * (rate / Decimal("100"))

    @property
    def total_amount(self):
        """
        Total del pedido (subtotal + IVA).
        """
        return self.subtotal_amount + self.vat_amount

    # Compatibilidad con código anterior
    @property
    def total(self):
        return self.total_amount

    def __str__(self):
        return f"Pedido #{self.id} - {self.user}"


class OrderItem(models.Model):
    """
    Representa un producto dentro de un pedido.
    """

    # Pedido al que pertenece este item
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)

    # Producto comprado
    product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE)

    # Cantidad comprada
    quantity = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        """
        Precio total de este producto (precio x cantidad).
        """
        return self.quantity * self.product.price

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
