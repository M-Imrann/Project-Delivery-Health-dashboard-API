from django.contrib import admin
from .models import Client, Team, Project, Task


class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'manager']
    search_fields = ['name']


class TeamAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        'client', 'name', 'status', 'budget',
        'start_date', 'end_date', 'team'
        ]
    list_filter = ['status', 'budget', 'end_date']
    search_fields = ['name']


class TaskAdmin(admin.ModelAdmin):
    list_display = ['project', 'completed', 'completed_at',
                    'due_date', 'created_at', 'billable_hours'
                    ]
    list_filter = ['completed', 'due_date', 'billable_hours']
    search_fields = ['project']


admin.site.register(Client, ClientAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Task, TaskAdmin)
