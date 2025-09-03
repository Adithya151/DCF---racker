from django.contrib import admin
from .models import ActivityLog, CarbonFootprint
# Register your models here.

admin.site.register(ActivityLog)
admin.site.register(CarbonFootprint)
