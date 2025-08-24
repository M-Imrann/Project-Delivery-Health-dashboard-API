from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse
from .models import Client
from .serializers import ClientSummarySerializer
import csv
import openpyxl


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class HealthDashboardAPI(APIView):
    """
    Health Dashboard API
    """
    permission_classes = [IsAuthenticated]

    # Cache results for 10 minutes
    @method_decorator(cache_page(60 * 10))
    def get(self, request):
        last_90_days = timezone.now().date() - timedelta(days=90)

        # Admin access and Manager Access
        if request.user.is_superuser:
            clients = Client.objects.filter(
                projects__start_date__gte=last_90_days
            ).distinct()
        else:
            clients = Client.objects.filter(
                manager=request.user,
                projects__start_date__gte=last_90_days
            ).distinct()

        # Filtering
        status = request.GET.get("status")
        min_budget = request.GET.get("min_budget")
        start_after = request.GET.get("start_after")

        if status:
            clients = clients.filter(projects__status=status)
        if min_budget:
            clients = clients.filter(projects__budget__gte=float(min_budget))
        if start_after:
            clients = clients.filter(projects__start_date__gte=start_after)

        # Ordering
        ordering = request.GET.get("ordering")
        if ordering in [
            "total_spent", "-total_spent", "delivery_health",
                "-delivery_health", "overdue_projects", "-overdue_projects"
                ]:
            """We will sort after serialization as the delivery_health
            is calculated in serializer."""
            pass

        serializer = ClientSummarySerializer(
            clients.prefetch_related("projects__tasks", "projects__team"),
            many=True,
            context={"request": request}
        )

        data = serializer.data

        # We will handle ordering manually as delivery_health is not in models.
        if ordering:
            reverse = ordering.startswith("-")
            key = ordering.lstrip("-")
            data = sorted(data, key=lambda x: x.get(key, 0), reverse=reverse)

        # Pagination
        paginator = StandardResultsSetPagination()
        paginated_data = paginator.paginate_queryset(data, request)

        # Export handling
        export = request.GET.get("export")
        if export == "csv":
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = 'attachment; ' \
                'filename="project_health.csv"'
            writer = csv.writer(response)
            writer.writerow(
                ["Client", "Total Projects", "Total Budget", "Total Spent",
                 "Delivery Health", "Overdue Projects", "Top Teams"]
            )
            for client in paginated_data:
                writer.writerow([
                    client["name"],
                    client["total_projects"],
                    client["total_budget"],
                    client["total_spent"],
                    client["delivery_health"],
                    client["overdue_projects"],
                    ", ".join(client["top_teams"]),
                ])
            return response

        elif export == "excel":
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Project Health"
            ws.append(
                ["Client", "Total Projects", "Total Budget", "Total Spent",
                 "Delivery Health", "Overdue Projects", "Top Teams"]
            )
            for client in paginated_data:
                ws.append([
                    client["name"],
                    client["total_projects"],
                    client["total_budget"],
                    client["total_spent"],
                    client["delivery_health"],
                    client["overdue_projects"],
                    ", ".join(client["top_teams"]),
                ])
            response = HttpResponse(
                content_type="application/vnd.openxmlformats-officedocument\
                    .spreadsheetml.sheet"
            )
            response["Content-Disposition"] = 'attachment; ' \
                'filename=project_health.xlsx'
            wb.save(response)
            return response

        return paginator.get_paginated_response(paginated_data)
