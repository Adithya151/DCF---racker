import google.generativeai as genai
from dotenv import load_dotenv
from django.db.models import Sum, F, ExpressionWrapper, FloatField
from tracker.models import UserProfile, ActivityLog
import os

# --- Gemini API Setup ---
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")


def ask_gemini(user, user_message: str):
    """
    Sends the user query and personalized DCF Tracker context to Gemini.
    Returns Gemini's text response.
    """

    # ---- 1. Handle Unauthenticated Users ----
    if not user or not user.is_authenticated:
        prompt = f"""
        You are EcoBot, an AI assistant in the DCF Tracker web app.
        The user is not logged in.

        User asked: "{user_message}"

        Please answer generally about carbon footprint tracking, CO₂ reduction,
        and environmental sustainability.
        """
        response = model.generate_content(prompt)
        return response.text.strip() if response.text else "Sorry, I didn’t catch that."

    # ---- 2. Get user-specific data ----
    try:
        profile = UserProfile.objects.get(user=user)
        total_users = UserProfile.objects.count()
        rank = list(UserProfile.objects.order_by("total_co2")).index(profile) + 1

        latest_log = ActivityLog.objects.filter(user=user).order_by("-date").first()
        if latest_log:
            latest_data = (
                f"Last logged on {latest_log.date}: "
                f"{latest_log.emails_sent} emails, "
                f"{latest_log.drive_storage_gb} GB drive storage, "
                f"{latest_log.github_commits} commits."
            )
        else:
            latest_data = "No activity logs found."

    except UserProfile.DoesNotExist:
        profile = None
        rank = "N/A"
        latest_data = "No profile or activity data found."

    # ---- 3. Build Contextual Prompt ----
    prompt = f"""
    You are EcoBot, the intelligent AI assistant built into the DCF Tracker web app.
    The app helps users monitor and reduce their digital CO₂ footprint.

    User context:
    - Username: {user.username}
    - Total CO₂ Emission: {profile.total_co2 if profile else 0:.2f} kg
    - Rank: {rank} out of {total_users}
    - Latest activity: {latest_data}

    The user asked: "{user_message}"

    Instructions for your answer:
    - If the question is about emissions, ranking, or suggestions, use the data above.
    - If it’s about general sustainability or CO₂, explain normally.
    - Keep answers friendly, short, and conversational.
    """

    # ---- 4. Generate response from Gemini ----
    try:
        response = model.generate_content(prompt)
        return response.text.strip() if response.text else "Sorry, I didn’t catch that."
    except Exception as e:
        return f"⚠️ Gemini Error: {e}"
