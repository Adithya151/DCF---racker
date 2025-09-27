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
    

# User Profile to track total CO2
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="tracker_profile")
    total_co2 = models.FloatField(default=0.0)

    def __str__(self):
        return self.user.username

# Badges for achievements
class Badge(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    icon = models.CharField(max_length=50, default="🏆")  # emoji or icon class

    def __str__(self):
        return self.name

# User badges
class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    awarded_on = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"

