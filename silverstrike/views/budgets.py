from datetime import date, datetime
from calendar import monthrange

from dateutil.relativedelta import relativedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.urls import reverse_lazy, reverse
from django.shortcuts import render, get_object_or_404
from django.views import generic

from silverstrike.forms import BudgetForm, BudgetFormSet
from silverstrike.lib import last_day_of_month
from silverstrike.models import Budget, Category, Split, CategoryType, Transaction
from silverstrike.views.serializers import BudgetSerializer

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework import permissions

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
        print(context['form'])
        return context

    def form_valid(self, form):
        for f in form:
            f.save()
        return super(BudgetIndex, self).form_valid(form)

class IndexView(LoginRequiredMixin, generic.ListView):
    template_name = 'silverstrike/test.html'
    success_url = reverse_lazy('budget_index')
    form_class = BudgetFormSet

    model = Category

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        if 'month' in kwargs:
            self.month = date(kwargs.pop('year'), kwargs.pop('month'), 1)
        else:
            self.month = date.today().replace(day=1)

        self.budget_spending = Split.objects.personal().past().date_range(
            self.month, last_day_of_month(self.month)).order_by('category').values(
                'category', 'category__name').annotate(spent=Sum('amount'))

        context['month'] = self.month
        self.budgets = Budget.objects.for_month(self.month)
        context['previous_month'] = self.month - relativedelta(months=1)
        context['next_month'] = self.month + relativedelta(months=1)

        context['allocated'] = sum([x.amount for x in self.budgets])
        context['spent'] = sum([self.budget_spending.get(x.category_id, 0) for x in self.budgets])
        context['left'] = context['allocated'] - context['spent']
        
        initial = []
        for cat in Category.objects.order_by('category_type_id'):
            try:
                budget_amount = Budget.objects.get(category_id=cat.id).amount
            except Budget.DoesNotExist:
                budget_amount = 0
            
            (_, day) = monthrange(self.month.year, self.month.month)
            remained_day = day - datetime.now().day
            recommend_spending = int(budget_amount/remained_day)

            try:
                spent = self.budget_spending.get(category_id=cat.id)['spent']
            except Exception:
                spent = 0

            left = budget_amount - abs(spent)
            if left < 0: left = 0

            if budget_amount == 0:
                percent = 0
            else:
                percent = 100 - int((left/budget_amount)*100)
            # print(cat.name, percent, spent)
            try:
                budget_id = Budget.objects.get(category_id=cat.id).id
            except:
                budget_id = 0

            initial.append({
                'cat_id': cat.id,
                'cat_name': cat.name,
                'cat_type': CategoryType.objects.get(id=cat.category_type_id),
                'budget_amount': budget_amount,
                'recommend_spend': recommend_spending,
                'spent': abs(spent),
                'daily_spent': int(abs(spent)/datetime.now().day),
                'left': left,
                'percent': percent,
                'budget_id': budget_id
            })
            
        context['list'] = initial
        # print(context['form'])

        return context  


class BudgetUpdateView(LoginRequiredMixin, generic.edit.UpdateView):
    model = Budget
    fields = ['amount']

    def get_context_data(self, **kwargs):
        context = super(generic.edit.UpdateView, self).get_context_data(**kwargs)
        context['name'] = Category.objects.get(id=context['budget'].category_id).name
        print(context)
        return context

    def get_success_url(self):
        return reverse_lazy('budget_index')

class BudgetListApiView(APIView):

    def get(self, request):
        trans = Split.objects.all()
        result = trans.values('category',"date").annotate(Sum=Sum('amount')).order_by('category')
        category = Category.objects.all()
        # result2 = category.values("splits")
        
        
        return Response(result, status=status.HTTP_200_OK)
