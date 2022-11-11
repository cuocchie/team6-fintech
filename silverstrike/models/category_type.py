from django.db import models
from django.urls import reverse

class CategoryType(models.Model):
    use_in_migrations = True
    name = models.CharField(max_length=64)
    # last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'category_types'
        ordering = ['name']

    def __str__(self):
        return self.name