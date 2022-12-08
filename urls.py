from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from silverstrike.views import budgets as budget_views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('silverstrike.urls')),
    path('api', budget_views.BudgetListApiView.as_view()),
]
