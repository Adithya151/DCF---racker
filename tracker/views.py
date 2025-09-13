from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from .forms import ActivityLogForm
from .models import ActivityLog
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


#Machine learning model code
import numpy as np
from sklearn.linear_model import LinearRegression
def home(request):
    return render(request,'home.html')

@login_required(login_url='login')
@never_cache
def dashboard(request):
    if not request.session.get('can_visit_dashboard'):
        return redirect('home')
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

    # ==============================
    # 🔹 AI: Predict next week's CO₂
    # ==============================
    prediction = None
    if len(chart_data) >= 3:  # need at least 3 data points
        X = np.arange(len(chart_data)).reshape(-1, 1)
        y = np.array(chart_data)

        model = LinearRegression()
        model.fit(X, y)

        next_index = len(chart_data) + 7  # predict 7 days later
        prediction = round(float(model.predict([[next_index]])[0]), 2)

    # ==============================
    # 🔹 Suggestions (rule-based)
    # ==============================
    suggestions = []
    if total_drive > (0.6 * total_co2):  # if >60% from storage
        suggestions.append("📦 Reduce cloud storage usage, as it contributes most to your CO₂ footprint.")
    if total_emails > 100:  # arbitrary threshold
        suggestions.append("📧 Consider deleting old emails and reducing unnecessary emails.")
    if total_commits > 200:
        suggestions.append("💻 Optimize commits or batch updates to reduce emissions from GitHub activity.")
    if not suggestions:
        suggestions.append("✅ Great job! Your digital carbon footprint is under control.")

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


@login_required
def set_dashboard_flag(request):
    request.session['can_visit_dashboard'] = True
    return redirect('dashboard')


@csrf_exempt
def chatbot(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_message = data.get("message", "").lower().strip()

        responses = []  # collect all matches

        # Greetings
        greetings = ["hi", "hello", "hey", "yo", "hii", "good morning", "good evening"]
        if any(word in user_message for word in greetings):
            responses.append("Hello 👋! I'm your CO₂ tracker assistant. How can I help you today?")

        # Polite
        if any(word in user_message for word in ["thanks", "thank you", "thx", "ty", "cheers"]):
            responses.append("You're welcome 💚! Glad I could help.")

        # Small talk
        if "who are you" in user_message or "what are you" in user_message:
            responses.append("I'm your CO₂ assistant 🌱. I help you understand and reduce your digital carbon footprint.")
        if "how are you" in user_message:
            responses.append("I'm doing great, thanks for asking! 🌟 How about you?")
        if "bye" in user_message or "good night" in user_message:
            responses.append("Goodbye 👋, take care of your carbon footprint! 🌍")

        # CO₂ / Environment
        if any(word in user_message for word in ["co2", "carbon", "pollution", "emission", "footprint"]):
            responses.append("Every email, file, or commit adds to your digital CO₂ footprint. I can help you track and reduce it.")
        if any(word in user_message for word in ["reduce", "save", "cut", "lower", "control"]):
            responses.append("You can reduce CO₂ 🌱 by deleting unused emails, cleaning up files, and committing efficiently.")
        if "dashboard" in user_message or "show data" in user_message:
            responses.append("Your dashboard 📊 shows total CO₂ emissions, top sources, and activities.")

        # Fallback if nothing matched
        if not responses:
            responses.append("Hmm 🤔 I didn’t get that. Try asking about CO₂, emissions, reducing impact, or your dashboard.")

        # Join multiple replies if needed
        reply = " ".join(responses)

        return JsonResponse({"reply": reply})