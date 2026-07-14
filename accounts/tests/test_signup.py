import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from clinic.models import Patient

User = get_user_model()


@pytest.mark.django_db
def test_signup_get_renders_form():
    response = Client().get("/signup/")
    assert response.status_code == 200
    assert "form" in response.context


@pytest.mark.django_db
def test_signup_post_creates_patient_and_logs_in():
    response = Client().post(
        "/signup/",
        {"username": "newuser", "password1": "str0ngP@ss!", "password2": "str0ngP@ss!"},
    )
    assert response.status_code == 302
    user = User.objects.get(username="newuser")
    assert user.role == "patient"
    assert Patient.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_signup_invalid_shows_errors():
    response = Client().post("/signup/", {"username": "", "password1": "x", "password2": "y"})
    assert response.status_code == 200
    assert response.context["form"].errors
