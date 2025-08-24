from celery import shared_task
from datetime import date, timedelta
from .models import Team


@shared_task
def recompute_team_velocities():
    """
    Weekly recomputation of team delivery velocity
    """
    last_30_days = date.today() - timedelta(days=30)

    teams = Team.objects.all()
    for team in teams:
        tasks_done = team.members.filter(
            task__completed=True,
            task__completed_at__gte=last_30_days
        ).count()
        velocity = round(tasks_done / 30, 2)

        team.cached_velocity = velocity
        team.save(update_fields=["cached_velocity"])

    return f"Recomputed velocity for {teams.count()} teams."
