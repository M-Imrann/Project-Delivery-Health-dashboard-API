from django.db import models
from django.contrib.auth.models import User


class Client(models.Model):
    """
    Model for Client
    """
    name = models.CharField(max_length=255)
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clients_managed'
        )

    def __str__(self):
        return f"{self.name}"


class Team(models.Model):
    """
    Model for Team
    """
    name = models.CharField(max_length=255)
    members = models.ManyToManyField(User)
    cached_velocity = models.FloatField(default=0)

    def __str__(self):
        return f"{self.name}"


class Project(models.Model):
    """
    Model for Project
    """
    STATUS_CHOICES = [
        ('active', "Active"),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
    ]
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='projects'
        )
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    budget = models.FloatField()
    start_date = models.DateField()
    end_date = models.DateField()
    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
        )

    def __str__(self):
        return f"{self.name}"


class Task(models.Model):
    """
    Model for Task
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tasks'
        )
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateField(null=True, blank=True)
    due_date = models.DateField()
    created_at = models.DateField(auto_now_add=True)
    billable_hours = models.FloatField(default=0)

    def __str__(self):
        return f"{self.project}"
