from rest_framework import serializers
from .models import Project, Client, Team
from django.db.models import Sum, Count, F
from datetime import date, timedelta


class ProjectSummarySerializer(serializers.ModelSerializer):
    """
    Project Summary Serializer in which we:
    get total amount spent,
    get percentage of task,
    get avererage task delay,
    get lead developers,
    get team velocity
    """
    amount_spent = serializers.SerializerMethodField()
    tasks_completed_percent = serializers.SerializerMethodField()
    avg_task_delay = serializers.SerializerMethodField()
    lead_developer = serializers.SerializerMethodField()
    team_velocity = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "name", "status", "budget", "amount_spent",
            "start_date", "end_date", "tasks_completed_percent",
            "avg_task_delay", "lead_developer", "team_velocity"
        ]

    def get_amount_spent(self, obj):
        """
        get_amount_spent calculate the total amount that is
        spent on the budget

        Return: Total amount spent
        """
        return obj.tasks.aggregate(total=Sum("billable_hours"))["total"] or 0

    def get_tasks_completed_percent(self, obj):
        """
        get_tasks_completed_percent calculates the percentage
        that how much project is completed.

        Return : Percentage of Completed Project
        """
        total_tasks = obj.tasks.count()
        completed_tasks = obj.tasks.filter(completed=True).count()
        return (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    def get_avg_task_delay(self, obj):
        """
        get_avg_task_delay calcultes the task delay

        Return: Average task delay
        """
        completed_tasks = obj.tasks.filter(
            completed=True,
            completed_at__isnull=False
            )
        delays = [(t.completed_at - t.due_date).days for t in completed_tasks]
        return sum(delays) / len(delays) if delays else 0

    def get_lead_developer(self, obj):
        """
        get_lead_developer gets the user with most task
        """
        lead = obj.tasks.values("assigned_to__username").annotate(
            task_count=Count("id")
        ).order_by("-task_count").first()
        return lead["assigned_to__username"] if lead else None

    def get_team_velocity(self, obj):
        """
        get_team_velocity calculates the average task completed

        Return : Team velocity for 30 days
        """
        team = obj.team
        if not team:
            return 0
        if team.cached_velocity:
            return round(team.cached_velocity, 2)
        last_30_days = date.today() - timedelta(days=30)
        tasks_done = obj.tasks.filter(
            completed=True,
            completed_at__gte=last_30_days
        ).count()
        return round(tasks_done / 30, 2)


class ClientSummarySerializer(serializers.ModelSerializer):
    """
    Client Summary Serializer in which we:
    get total projects,
    get total budget,
    get total spent,
    get delivery health,
    get overdue projects,
    get top team
    """
    total_projects = serializers.SerializerMethodField()
    total_budget = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    delivery_health = serializers.SerializerMethodField()
    overdue_projects = serializers.SerializerMethodField()
    top_teams = serializers.SerializerMethodField()
    projects = ProjectSummarySerializer(many=True)

    class Meta:
        model = Client
        fields = [
            "name", "total_projects", "total_budget", "total_spent",
            "delivery_health", "overdue_projects", "top_teams", "projects"
        ]

    def get_total_projects(self, obj):
        """
        fetch total projects
        """
        return obj.projects.count()

    def get_total_budget(self, obj):
        """
        get_total_budget calculates the budget of all projects

        Return : Total Budget
        """
        return obj.projects.aggregate(total=Sum("budget"))["total"] or 0

    def get_total_spent(self, obj):
        """
        get_total_spent calculates the total spent

        Return : total spent
        """
        return sum([
            p.tasks.aggregate(total=Sum("billable_hours"))["total"] or 0
            for p in obj.projects.all()
        ])

    def get_delivery_health(self, obj):
        """
        get_delivery_health checks the progress of project
        """
        total = obj.projects.count()
        if total == 0:
            return "no_projects"

        on_time = 0
        for p in obj.projects.filter(status="completed"):
            late_tasks = p.tasks.filter(
                completed=True,
                completed_at__gt=F("due_date")
            ).count()
            if late_tasks == 0:
                on_time += 1

        percent = (on_time / total) * 100
        if percent >= 80:
            return "on_track"
        elif percent >= 50:
            return "at_risk"
        return "delayed"

    def get_overdue_projects(self, obj):
        """
        Counts the overdue projects
        """
        return obj.projects.filter(status="overdue").count()

    def get_top_teams(self, obj):
        """
        get the top 3 teams by average task delivery speed
        """
        teams = Team.objects.filter(project__client=obj)\
            .order_by("-cached_velocity")[:3]
        return [t.name for t in teams]
