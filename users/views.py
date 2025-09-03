from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
import random
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail

def signup_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
        else:
            user = User.objects.create_user(username=username, password=password)
            login(request, user)
            return redirect('login')
    return render(request, "users/register.html")

def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password")
    return render(request, "users/login.html")

def logout_view(request):
    logout(request)
    return redirect('login')


# Temporary storage for OTPs (better: use a model or cache)
OTP_STORE = {}

def forgot_password(request):
    if request.method == "POST":
        username = request.POST.get("username")
        try:
            user = User.objects.get(username=username)
            otp = random.randint(100000, 999999)  # 6-digit OTP
            OTP_STORE[username] = otp
            # TODO: send otp via email (using Django Email backend)
            print("DEBUG OTP:", otp)  # remove later, just for testing
            messages.success(request, "OTP has been sent to your registered email.")
            request.session["reset_username"] = username
            return redirect("verify_otp")
        except User.DoesNotExist:
            messages.error(request, "User not found.")
    return render(request, "users/forgot_password.html")


def verify_otp(request):
    username = request.session.get("reset_username")
    if not username:
        return redirect("forgot_password")

    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        if OTP_STORE.get(username) and str(OTP_STORE[username]) == entered_otp:
            messages.success(request, "OTP verified. Please reset your password.")
            return redirect("reset_password")
        else:
            messages.error(request, "Invalid OTP. Try again.")
    return render(request, "users/verify_otp.html")


def reset_password(request):
    username = request.session.get("reset_username")
    if not username:
        return redirect("forgot_password")

    if request.method == "POST":
        new_password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("reset_password")

        user = User.objects.get(username=username)
        user.password = make_password(new_password)  # securely hash password
        user.save()

        OTP_STORE.pop(username, None)  # clear OTP
        request.session.pop("reset_username", None)

        messages.success(request, "Password reset successful! Please login.")
        return redirect("login")

    return render(request, "users/reset_password.html")