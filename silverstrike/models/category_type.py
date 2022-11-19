from django.db import models
from django.urls import reverse

class CategoryTypeQuerySet(models.QuerySet):
    def get_all(self):
        return self.order_by('id')

class CategoryType(models.Model):
    use_in_migrations = True
    name = models.CharField(max_length=64)

    objects = CategoryTypeQuerySet.as_manager()
    # last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'category_types'
        ordering = ['name']

    def __str__(self):
        return self.name