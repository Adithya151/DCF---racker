from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ActivityLogForm
from .models import ActivityLog
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import timedelta, date
import numpy as np
from sklearn.linear_model import LinearRegression

from django.http import JsonResponse
from .gemini_chatbot import ask_gemini


from .models import UserProfile, Badge, UserBadge, ActivityLog
from django.db.models import Sum
from django.db.models import Sum, F, FloatField, ExpressionWrapper

CO2_EMAIL = 0.004      # 4 g per email
CO2_DRIVE = 1.1        # 1.1 kg per GB/month
CO2_COMMIT = 0.0005    # 0.5 g per commit

DAILY_CO2_GOAL = 1.0   # Daily CO₂ goal in kg

def home(request):
    return render(request, 'home.html')


@login_required(login_url='login')
@never_cache
def dashboard(request):
    if not request.session.get('can_visit_dashboard'):
        return redirect('home')

    today = timezone.now().date()
    period = request.GET.get("period", "week")

    if period == "week":
        start_date = today - timedelta(days=7)
    elif period == "month":
        start_date = today - timedelta(days=30)
    else:
        start_date = None

    if start_date:
        logs_period = ActivityLog.objects.filter(user=request.user, date__gte=start_date).order_by("date")
    else:
        logs_period = ActivityLog.objects.filter(user=request.user).order_by("date")

    total_co2 = sum(
        log.emails_sent * CO2_EMAIL +
        log.drive_storage_gb * CO2_DRIVE +
        log.github_commits * CO2_COMMIT
        for log in logs_period
    )
    total_emails = sum(log.emails_sent for log in logs_period)
    total_drive = sum(log.drive_storage_gb for log in logs_period)
    total_commits = sum(log.github_commits for log in logs_period)

    # Chart data
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

    # Prediction (Linear Regression)
    prediction = None
    if len(chart_data) >= 3:
        X = np.arange(len(chart_data)).reshape(-1, 1)
        y = np.array(chart_data)
        model = LinearRegression()
        model.fit(X, y)
        next_index = len(chart_data) + 7
        prediction = round(float(model.predict([[next_index]])[0]), 2)

    # Suggestions
    suggestions = []
    if total_drive > 0.6 * total_co2:
        suggestions.append("📦 Reduce cloud storage usage, as it contributes most to your CO₂ footprint.")
    if total_emails > 100:
        suggestions.append("📧 Consider deleting old emails and reducing unnecessary emails.")
    if total_commits > 200:
        suggestions.append("💻 Optimize commits or batch updates to reduce emissions from GitHub activity.")
    if not suggestions:
        suggestions.append("✅ Great job! Your digital carbon footprint is under control.")

    # Daily CO₂
    daily_logs = ActivityLog.objects.filter(user=request.user, date=today)
    daily_co2 = sum(
        log.emails_sent * CO2_EMAIL +
        log.drive_storage_gb * CO2_DRIVE +
        log.github_commits * CO2_COMMIT
        for log in daily_logs
    )
    daily_progress = min(int((daily_co2 / DAILY_CO2_GOAL) * 100), 100)

    # User rank
    all_profiles = list(UserProfile.objects.order_by("total_co2"))
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if user_profile in all_profiles:
        user_rank = all_profiles.index(user_profile) + 1
    else:
        user_rank = None

    return render(request, "tracker/dashboard.html", {
        "logs": logs_period,
        "total_co2": round(total_co2, 2),
        "total_emails": total_emails,
        "total_drive": total_drive,
        "total_commits": total_commits,
        "chart_labels": chart_labels,
        "chart_data": chart_data,
        "period": period,
        "prediction": prediction,
        "suggestions": suggestions,
        "daily_co2": round(daily_co2, 2),
        "daily_progress": daily_progress,
        "daily_goal": DAILY_CO2_GOAL,
        "user_rank": user_rank,
    })



@login_required
@login_required(login_url='login')
def log_activity(request):
    if request.method == "POST":
        form = ActivityLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.user = request.user
            log.date = date.today()
            log.save()

            # --- Update total CO₂ for leaderboard ---
            agg = ActivityLog.objects.filter(user=request.user).aggregate(
                total_co2=Sum(
                    ExpressionWrapper(
                        F("emails_sent") * CO2_EMAIL +
                        F("drive_storage_gb") * CO2_DRIVE +
                        F("github_commits") * CO2_COMMIT,
                        output_field=FloatField()
                    )
                )
            )
            total = agg["total_co2"] or 0.0
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            profile.total_co2 = total
            profile.save()
            # ------------------------------------------------

            messages.success(request, "✅ Activity logged successfully!")
            return redirect("dashboard")
    else:
        form = ActivityLogForm()

    return render(request, "tracker/log_activity.html", {"form": form})


# LEADERBOARD VIEW
@login_required(login_url='login')
def leaderboard(request):
    # Always make sure profiles are up-to-date
    for profile in UserProfile.objects.all():
        agg = ActivityLog.objects.filter(user=profile.user).aggregate(
            total_co2=Sum(
                ExpressionWrapper(
                    F("emails_sent") * 0.004 +
                    F("drive_storage_gb") * 1.1 +
                    F("github_commits") * 0.0005,
                    output_field=FloatField()
                )
            )
        )
        total = agg["total_co2"] or 0.0
        profile.total_co2 = total
        profile.save()

    top_users = UserProfile.objects.order_by("total_co2")[:10]
    print("Profiles:", UserProfile.objects.all())
    print("Top users:", list(top_users.values("user__username", "total_co2")))


    return render(request, "tracker/leaderboard.html", {"top_users": top_users})

def reset_dashboard(request):
    if request.user.is_authenticated:
        ActivityLog.objects.filter(user=request.user).delete()
    return redirect('dashboard')


@login_required
def set_dashboard_flag(request):
    request.session['can_visit_dashboard'] = True
    return redirect('dashboard')


@csrf_exempt
@login_required
def chatbot(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()
        reply = ask_gemini(request.user, user_message)

        return JsonResponse({"reply": reply})

    return JsonResponse({"error": "Invalid request"}, status=400)


# Badges view
@login_required
def badges(request):
    # Example badge 
    first_log_badge = Badge.objects.get_or_create(
        name="First Activity Logged",
        defaults={'description': "Logged your first activity!", 'icon': "🎉"}
    )[0]

    user_logs = ActivityLog.objects.filter(user=request.user).count()
    if user_logs >= 1 and not UserBadge.objects.filter(user=request.user, badge=first_log_badge).exists():
        UserBadge.objects.create(user=request.user, badge=first_log_badge)

    user_badges = UserBadge.objects.filter(user=request.user)
    return render(request, 'tracker/badges.html', {'user_badges': user_badges})
