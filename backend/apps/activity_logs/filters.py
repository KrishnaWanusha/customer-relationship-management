import django_filters
from .models import ActivityLog


class ActivityLogFilter(django_filters.FilterSet):
    action = django_filters.ChoiceFilter(choices=ActivityLog.Action.choices)
    model_name = django_filters.CharFilter(lookup_expr="iexact")
    timestamp_after = django_filters.DateTimeFilter(field_name="timestamp", lookup_expr="gte")
    timestamp_before = django_filters.DateTimeFilter(field_name="timestamp", lookup_expr="lte")

    class Meta:
        model = ActivityLog
        fields = ["action", "model_name"]
