from datetime import date

from dateutil.relativedelta import relativedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.urls import reverse_lazy
from django.shortcuts import render
from django.views import generic

from silverstrike.forms import BudgetFormSet
from silverstrike.lib import last_day_of_month
from silverstrike.models import Budget, Category, Split, CategoryType


class BudgetIndex(LoginRequiredMixin, generic.edit.FormView):
    template_name = 'silverstrike/budget_index.html'
    context_object_name = 'formset'
    success_url = reverse_lazy('budgets')
    form_class = BudgetFormSet

    def dispatch(self, request, *args, **kwargs):
        if 'month' in kwargs:
            self.month = date(kwargs.pop('year'), kwargs.pop('month'), 1)
        else:
            self.month = date.today().replace(day=1)
        return super(BudgetIndex, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        # assigned categories
        self.budgets = Budget.objects.for_month(self.month)
        budget_spending = Split.objects.personal().past().date_range(
            self.month, last_day_of_month(self.month)).order_by('category').values(
                'category', 'category__name').annotate(spent=Sum('amount'))

        self.budget_spending = {e['category']: abs(e['spent']) for e in budget_spending}
        initial = []

        # existing budgets
        for budget in self.budgets:
            initial.append({
                'budget_id': budget.id,
                'category_id': budget.category_id,
                'category_name': budget.category.name,
                'spent': self.budget_spending.get(budget.category_id, 0),
                'amount': budget.amount,
                'left': -self.budget_spending.get(budget.category_id, 0) + budget.amount,
                'month': self.month,
                'category_type': budget.category.category_type.name,
                'category_type_id': budget.category.category_type_id
                })

        ids = [budget.category_id for budget in self.budgets]
        for category in Category.objects.exclude(id__in=ids).exclude(active=False):
            initial.append({
                'budget_id': -1,
                'category_id': category.id,
                'category_name': category.name,
                'spent': self.budget_spending.get(category.id, 0),
                'amount': 0,
                'left': -self.budget_spending.get(category.id, 0),
                'month': self.month,
                'category_type': category.category_type.name,
                'category_type_id': category.category_type_id
            })

        initial = sorted(initial, key=lambda d: d['category_type_id'])
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'budgets'
        context['month'] = self.month
        context['previous_month'] = self.month - relativedelta(months=1)
        context['next_month'] = self.month + relativedelta(months=1)

        context['allocated'] = sum([x.amount for x in self.budgets])
        context['spent'] = sum([self.budget_spending.get(x.category_id, 0) for x in self.budgets])
        context['left'] = context['allocated'] - context['spent']
        return context

    def form_valid(self, form):
        for f in form:
            f.save()
        return super(BudgetIndex, self).form_valid(form)

# class CategoryTypeIndex(LoginRequiredMixin, generic.ListView):
#     template_name = 'silverstrike/test.html'
#     context_object_name = 'category_type_list'
#     model = category_type.CategoryType

#     def get_queryset(self):
#         return category_type.CategoryType.objects.order_by('name')

class IndexView(LoginRequiredMixin, generic.DetailView):
    template_name = 'silverstrike/test.html'
    context_object_name = 'category_list'
    category = Category
    category_type = CategoryType.objects.get_queryset().get_all()

    def get_context_data(self, **kwargs):
        context = {}
        # print([cat.id for cat in self.category_type])
        for category_type in self.category_type:
            context[category_type.name] = [category.name for category in Category.objects.get_queryset().get_by_cat_type_id(category_type.id)]
        return context

class CategoryTypeCreateView(LoginRequiredMixin, generic.edit.CreateView):
    model = CategoryType
    fields = ['name']
    success_url = reverse_lazy('budgets')


class CategoryTypeUpdateView(LoginRequiredMixin, generic.edit.UpdateView):
    model = CategoryType
    fields = ['name']

    success_url = reverse_lazy('budgets')


class CategoryTypeDeleteView(LoginRequiredMixin, generic.edit.DeleteView):
    model = CategoryType
    success_url = reverse_lazy('budgets')
