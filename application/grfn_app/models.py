from django.db import models

class GrafanaServer(models.Model):
    url = models.URLField(max_length=200)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    folder = models.CharField(max_length=100)

    def __str__(self):
        return self.url if self.url else "GrafanaServer object with empty URL"

class Dashboard(models.Model):
    title = models.CharField(max_length=100)
    dashboard_uid = models.CharField(max_length=50, unique=True)
    dashboard_slug = models.CharField(max_length=100, default=None)

    def __str__(self):
        return self.title

class Board(models.Model):
    panel_id = models.IntegerField()
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='boards')
    panel_title = models.CharField(max_length=100, default='')
    embed_url = models.URLField(max_length=500, default='')
    time_range = models.CharField(max_length=100, choices=(('Custom', 'Custom'), ('Default', 'Default')))
    custom_time_range = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ('panel_id', 'dashboard')

    def __str__(self):
        return f"Panel {self.panel_id}"
