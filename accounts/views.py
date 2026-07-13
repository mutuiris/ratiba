"""Authentication views: signup"""

from django.contrib.auth import login
from django.shortcuts import redirect, render

from accounts.forms import SignupForm
from clinic.models import Patient


def signup(request):
    """Register a new patient account and log them in"""
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = "patient"
            user.save()
            Patient.objects.create(user=user, name=user.username)
            login(request, user)
            return redirect("web-doctors")
    else:
        form = SignupForm()
    return render(request, "clinic/signup.html", {"form": form})
