from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    emails_sent = models.IntegerField(default=0)
    drive_storage_gb = models.FloatField(default=0)
    github_commits = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.date}"

class CarbonFootprint(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    week_start = models.DateField()
    co2_emails = models.FloatField(default=0)
    co2_drive = models.FloatField(default=0)
    co2_github = models.FloatField(default=0)

    @property
    def total_co2(self):
        return self.co2_emails + self.co2_drive + self.co2_github

    def __str__(self):
        return f"{self.user.username} - {self.week_start}"
