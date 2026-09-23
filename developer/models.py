from django.db import models
import uuid


class User(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    name = models.CharField(max_length=150)

    password = models.CharField(max_length=255)

    email = models.EmailField(
        unique=True
    )

    phone = models.CharField(
        max_length=15
    )

    def __str__(self):
        return self.name


class UserProfile(models.Model):

    AUTH_PROVIDERS = (
        ("mobile", "Mobile"),
        ("google", "Google"),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    name = models.CharField(
        max_length=150,
        blank=True
    )

    email = models.EmailField(
        blank=True
    )

    phone = models.CharField(
        max_length=15,
        blank=True,
        default=""
    )

    google_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )

    profile_image_url = models.URLField(
        max_length=1000,
        blank=True,
        default=""
    )

    auth_provider = models.CharField(
        max_length=20,
        choices=AUTH_PROVIDERS,
        default="mobile"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def generate_profile_image(self):

        if not self.name:
            return ""

        name_parts = self.name.strip().split()

        if len(name_parts) >= 2:
            initials = (
                name_parts[0][0] +
                name_parts[1][0]
            ).upper()
        else:
            initials = self.name.strip()[:2].upper()

        return (
            "https://ui-avatars.com/api/"
            f"?name={initials}"
            "&size=256"
            "&background=random"
            "&color=fff"
            "&bold=true"
        )

    def save(self, *args, **kwargs):

        if not self.profile_image_url:
            self.profile_image_url = self.generate_profile_image()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=150, unique=True)
    icon = models.ImageField(
        upload_to="categories/",
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="subcategories"
    )
    name = models.CharField(max_length=150)
    icon = models.ImageField(
        upload_to="subcategories/",
        blank=True,
        null=True
    )

    class Meta:
        unique_together = ("category", "name")

    def __str__(self):
        return f"{self.category.name} - {self.name}"    


class Product(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products"
    )

    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.CASCADE,
        related_name="products"
    )

    name = models.CharField(
        max_length=255
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    stock = models.PositiveIntegerField(
        default=0
    )

    featured = models.BooleanField(
        default=False
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images"
    )

    image = models.ImageField(
        upload_to="products/"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.product.name} - Image"