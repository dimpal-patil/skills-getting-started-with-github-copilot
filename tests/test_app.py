import copy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture(autouse=True)
def reset_activities():
    original_activities = copy.deepcopy(activities)
    activities.clear()
    activities.update(original_activities)
    yield
    activities.clear()
    activities.update(original_activities)


client = TestClient(app)


def sign_up_user(activity_name: str, email: str):
    return client.post(f"/activities/{activity_name}/signup?email={email}")


def test_get_activities_returns_activity_catalog():
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert expected_activity in payload
    assert "participants" in payload[expected_activity]


def test_signup_adds_student_to_activity():
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    # Act
    response = sign_up_user(activity_name, email)

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == f"Signed up {email} for {activity_name}"

    activities_response = client.get("/activities").json()
    assert email in activities_response[activity_name]["participants"]


def test_duplicate_signup_is_rejected():
    # Arrange
    activity_name = "Chess Club"
    email = "duplicate@mergington.edu"

    # Act
    first_response = sign_up_user(activity_name, email)
    second_response = sign_up_user(activity_name, email)

    # Assert
    assert first_response.status_code == 200
    assert second_response.status_code == 400

    activities_response = client.get("/activities").json()
    assert activities_response[activity_name]["participants"].count(email) == 1


def test_unregister_participant_from_activity():
    # Arrange
    activity_name = "Chess Club"
    email = "removeme@mergington.edu"
    sign_up_user(activity_name, email)

    # Act
    response = client.delete(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 200
    activities_response = client.get("/activities").json()
    assert email not in activities_response[activity_name]["participants"]


def test_signup_for_missing_activity_returns_404():
    # Arrange
    activity_name = "Nonexistent Club"
    email = "student@mergington.edu"

    # Act
    response = sign_up_user(activity_name, email)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_missing_participant_returns_404():
    # Arrange
    activity_name = "Chess Club"
    email = "notregistered@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
