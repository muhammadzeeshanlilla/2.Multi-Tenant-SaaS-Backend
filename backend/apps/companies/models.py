from django.db import models
from django.utils.text import slugify


class Company(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            max_length = self._meta.get_field("slug").max_length
            base_slug = slugify(self.name)[:max_length] or "company"
            candidate = base_slug
            suffix = 2

            existing = Company.objects.exclude(pk=self.pk)
            while existing.filter(slug=candidate).exists():
                suffix_text = f"-{suffix}"
                candidate = f"{base_slug[:max_length - len(suffix_text)]}{suffix_text}"
                suffix += 1

            self.slug = candidate
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
