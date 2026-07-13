"""Tests for accounts: signup form and view"""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from clinic.models import Patient

User = get_user_model()


@pytest.mark.django_db
def test_signup_page_renders():
    response = Client().get("/accounts/signup/")
    assert response.status_code == 200
    assert "Create an account" in response.content.decode()


@pytest.mark.django_db
def test_signup_creates_user_and_patient():
    client = Client()
    response = client.post(
        "/accounts/signup/",
        {"username": "newuser", "password1": "Str0ngPass!", "password2": "Str0ngPass!"},
    )
    assert response.status_code == 302
    user = User.objects.get(username="newuser")
    assert user.role == "patient"
    assert Patient.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_signup_invalid_shows_form():
    client = Client()
    response = client.post(
        "/accounts/signup/",
        {"username": "u", "password1": "short", "password2": "mismatch"},
    )
    assert response.status_code == 200
    assert User.objects.filter(username="u").count() == 0


@pytest.mark.django_db
def test_signup_logs_user_in():
    client = Client()
    client.post(
        "/accounts/signup/",
        {"username": "autouser", "password1": "Str0ngPass!", "password2": "Str0ngPass!"},
    )
    response = client.get("/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_login_page_renders():
    response = Client().get("/accounts/login/")
    assert response.status_code == 200
    assert "Welcome back" in response.content.decode()


@pytest.mark.django_db
def test_login_valid_redirects():
    User.objects.create_user("bob", password="Pass1234!")
    client = Client()
    response = client.post("/accounts/login/", {"username": "bob", "password": "Pass1234!"})
    assert response.status_code == 302
