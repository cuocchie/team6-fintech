from django.db import models
from django.urls import reverse

from .account_type import AccountType
from .transaction import Split, Transaction
from .category_type import CategoryType

class CategoryQuerySet(models.QuerySet):
    def get_all(self):
        return self.all()

    def get_by_cat_type_id(self, category_type_id):
        return self.filter(category_type=category_type_id)

class Category(models.Model):
    name = models.CharField(max_length=64)
    active = models.BooleanField(default=True)
    last_modified = models.DateTimeField(auto_now=True)
    category_type = models.ForeignKey(CategoryType, models.SET_NULL, null=True, blank=True)

    objects = CategoryQuerySet.as_manager()

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def money_spent(self):
        return abs(Split.objects.filter(
                category=self, account__account_type=AccountType.PERSONAL,
                transaction__transaction_type=Transaction.WITHDRAW).aggregate(
            models.Sum('amount'))['amount__sum'] or 0)

    def get_absolute_url(self):
        return reverse('category_detail', args=[self.id])
