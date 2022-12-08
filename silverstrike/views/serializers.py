from rest_framework import serializers
from silverstrike.models import Budget
class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ["amount","month"]