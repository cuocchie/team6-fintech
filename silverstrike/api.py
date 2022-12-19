import datetime

from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _

from .models import Account, AccountType, Split
from .ml import finance_predictor, finance_predictor_index
from .models import Account, AccountType, Split

@login_required
def get_accounts(request, account_type):
    accounts = Account.objects.exclude(account_type=AccountType.SYSTEM)
    if account_type != 'all':
        account_type = getattr(AccountType, account_type)
        accounts = accounts.filter(account_type=account_type)

    return JsonResponse(list(accounts.values_list('name', flat=True)), safe=False)


@login_required
def get_accounts_balance(request, dstart, dend):
    try:
        dstart = datetime.datetime.strptime(dstart, '%Y-%m-%d').date()
        dend = datetime.datetime.strptime(dend, '%Y-%m-%d').date()
    except ValueError:
        return HttpResponseBadRequest(_('Invalid date format, expected yyyy-mm-dd'))
    dataset = []
    for account in Account.objects.personal().active():
        data = list(zip(*account.get_data_points(dstart, dend)))
        dataset.append({'name': account.name, 'data': data[1]})
    if dataset:
        labels = [datetime.datetime.strftime(x, '%d %b %Y') for x in data[0]]
    else:
        labels = []
    return JsonResponse({'labels': labels, 'dataset': dataset})


@login_required
def get_account_balance(request, account_id, dstart, dend):
    account = get_object_or_404(Account, pk=account_id)
    try:
        dstart = datetime.datetime.strptime(dstart, '%Y-%m-%d').date()
        dend = datetime.datetime.strptime(dend, '%Y-%m-%d').date()
    except ValueError:
        return HttpResponseBadRequest(_('Invalid date format, expected yyyy-mm-dd'))
    labels, data = zip(*account.get_data_points(dstart, dend))
    return JsonResponse({'data': data, 'labels': labels})


@login_required
def get_balances(request, dstart, dend):

    datatest = finance_predictor.process_file()
    print(datatest)
    # datatest = {
    #     'labels': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
    #     'datafront': [1, 2, 3, 4, 5, 6, 7],
    #     'databack': [None, None, None, None, None, None, 7, 8, 9, 10, 11, 12, 13, 14]
    # }
    return JsonResponse(datatest, safe=False)

@login_required
def get_balances_index(request, dstart, dend):

    datatest = finance_predictor_index.process_file()
    print(datatest)
    # datatest = {
    #     'labels': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
    #     'datafront': [1, 2, 3, 4, 5, 6, 7],
    #     'databack': [None, None, None, None, None, None, 7, 8, 9, 10, 11, 12, 13, 14]
    # }
    return JsonResponse(datatest, safe=False)


@login_required
def category_spending(request, dstart, dend):
    try:
        dstart = datetime.datetime.strptime(dstart, '%Y-%m-%d')
        dend = datetime.datetime.strptime(dend, '%Y-%m-%d')
    except ValueError:
        return HttpResponseBadRequest(_('Invalid date format, expected yyyy-mm-dd'))
    res = Split.objects.expense().past().date_range(dstart, dend).order_by('category').values(
        'category__name').annotate(spent=models.Sum('amount'))
    if res:
        res = [(e['category__name'] or 'No category', abs(e['spent'])) for e in res if e['spent']]
        categories, spent = zip(*res)
    else:
        categories, spent = [], []
    return JsonResponse({'categories': categories, 'spent': spent})
