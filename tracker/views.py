from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from .forms import ActivityLogForm
from .models import ActivityLog
from django.utils import timezone
from datetime import timedelta
def home(request):
    return render(request,'home.html')

@login_required
def dashboard(request):
    today = timezone.now().date()
    month_ago = today - timedelta(days=30)
    week_ago = today - timedelta(days=7)

    logs_month = ActivityLog.objects.filter(user=request.user, date__gte=month_ago).order_by("date")
    logs_week = ActivityLog.objects.filter(user=request.user, date__gte=week_ago)

    # CO₂ conversion factors
    CO2_EMAIL = 0.004
    CO2_DRIVE = 0.02
    CO2_COMMIT = 0.002

    # Cumulative CO2 for chart
    chart_labels = []
    chart_data = []
    cumulative_co2 = 0
    for log in logs_month:
        daily_co2 = (
            log.emails_sent * CO2_EMAIL +
            log.drive_storage_gb * CO2_DRIVE +
            log.github_commits * CO2_COMMIT
        )
        cumulative_co2 += daily_co2
        chart_labels.append(log.date.strftime("%Y-%m-%d"))
        chart_data.append(round(cumulative_co2, 2))

    # Total CO2 for last 7 days (stat card)
    total_co2 = sum(
        (log.emails_sent * CO2_EMAIL) +
        (log.drive_storage_gb * CO2_DRIVE) +
        (log.github_commits * CO2_COMMIT)
        for log in logs_week
    )

    # Total Emails, Drive GB, GitHub commits for last 7 days
    total_emails = sum(log.emails_sent for log in logs_week)
    total_drive = sum(log.drive_storage_gb for log in logs_week)
    total_commits = sum(log.github_commits for log in logs_week)

    return render(request, "tracker/dashboard.html", {
        "logs": logs_week,
        "total_co2": round(total_co2, 2),
        "total_emails": total_emails,
        "total_drive": total_drive,
        "total_commits": total_commits,
        "chart_labels": chart_labels,
        "chart_data": chart_data,
    })

    
    
@login_required
def log_activity(request):
    if request.method == "POST":
        form = ActivityLogForm(request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.user = request.user
            activity.save()
            return redirect('dashboard')
    else:
        form = ActivityLogForm()

    return render(request, "tracker/log_activity.html", {"form": form})


