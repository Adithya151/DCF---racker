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
    period = request.GET.get("period", "week")  # default to 'week'

    # Determine start date based on selected period
    if period == "week":
        start_date = today - timedelta(days=7)
    elif period == "month":
        start_date = today - timedelta(days=30)
    else:  # all time
        start_date = None

    # Filter logs for the stat cards
    if start_date:
        logs_period = ActivityLog.objects.filter(user=request.user, date__gte=start_date).order_by("date")
    else:
        logs_period = ActivityLog.objects.filter(user=request.user).order_by("date")

    # CO₂ conversion factors (kg)
    CO2_EMAIL = 0.004      # 4 g per email
    CO2_DRIVE = 1.1        # 1.1 kg per GB/month
    CO2_COMMIT = 0.0005    # 0.5 g per commit

    # Totals for the selected period (stat cards)
    total_co2 = sum(
        (log.emails_sent * CO2_EMAIL) +
        (log.drive_storage_gb * CO2_DRIVE) +
        (log.github_commits * CO2_COMMIT)
        for log in logs_period
    )
    total_emails = sum(log.emails_sent for log in logs_period)
    total_drive = sum(log.drive_storage_gb for log in logs_period)
    total_commits = sum(log.github_commits for log in logs_period)

    # Chart data: cumulative CO2 over the period
    chart_labels = []
    chart_data = []
    cumulative_co2 = 0
    for log in logs_period:
        daily_co2 = (
            log.emails_sent * CO2_EMAIL +
            log.drive_storage_gb * CO2_DRIVE +
            log.github_commits * CO2_COMMIT
        )
        cumulative_co2 += daily_co2
        chart_labels.append(log.date.strftime("%Y-%m-%d"))
        chart_data.append(round(cumulative_co2, 2))

    return render(request, "tracker/dashboard.html", {
        "logs": logs_period,
        "total_co2": round(total_co2, 2),
        "total_emails": total_emails,
        "total_drive": total_drive,
        "total_commits": total_commits,
        "chart_labels": chart_labels,
        "chart_data": chart_data,
        "period": period,
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


def reset_dashboard(request):
    if request.user.is_authenticated:
        # Delete all ActivityLog entries for this user
        ActivityLog.objects.filter(user=request.user).delete()
    return redirect('dashboard')