from django.db import models

# definimos el modelo Producto
class Product(models.Model):
    FRUTA = "FRUTA"
    VERDURA = "VERDURA"
    # lista de duplas
    TYPE_CHOICES = [(FRUTA, "Fruta"), (VERDURA, "Verdura")]
    # nombre del producto
    name = models.CharField(max_length=120)
    # TIPO
    product_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    # descripcion
    description = models.TextField(blank=True, default="")  
    # imagen
    image = models.ImageField(upload_to="products/", blank=True, null=True)  
    # precio
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # unidad,kg,u
    unit = models.CharField(max_length=30, default="kg")
    # cantidad
    stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # hay stock?
    is_active = models.BooleanField(default=True)

    # metodo para convertir el objeto en texto por su nombre
    # se usa en el admin, en relaciones foreign key, en la shell
    def __str__(self):
        return self.name


