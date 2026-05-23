import copy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app

# Create a TestClient for the FastAPI application once for the test module.
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the global activities state before and after each test.

    The app uses an in-memory activities dictionary. This fixture makes a deep copy
    of the initial state, yields control to the test, then resets the state in
    the finally block so tests remain isolated.
    """
    original_activities = copy.deepcopy(activities)
    try:
        yield
    finally:
        activities.clear()
        activities.update(copy.deepcopy(original_activities))


def test_get_activities_returns_activity_list():
    # Arrange: choose a known activity from the seeded app data.
    expected_activity = "Chess Club"

    # Act: request the activity catalog.
    response = client.get("/activities")

    # Assert: confirm the response contains the seeded activity details.
    assert response.status_code == 200
    data = response.json()
    assert expected_activity in data
    assert data[expected_activity]["schedule"] == "Fridays, 3:30 PM - 5:00 PM"


def test_signup_for_activity_adds_participant():
    # Arrange: prepare an activity and a new participant email.
    activity_name = "Programming Class"
    email = "newstudent@mergington.edu"

    # Act: sign up the student for the activity.
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert: verify the signup succeeded and the participant was added.
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_duplicate_returns_bad_request():
    # Arrange: use an email already registered for the activity.
    activity_name = "Chess Club"
    duplicate_email = "michael@mergington.edu"

    # Act: attempt a duplicate signup.
    response = client.post(f"/activities/{activity_name}/signup", params={"email": duplicate_email})

    # Assert: confirm the app rejects duplicate signups.
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_invalid_activity_returns_not_found():
    # Arrange: choose an activity name that does not exist.
    invalid_activity = "Nonexistent Club"
    email = "student@mergington.edu"

    # Act: try signing up for the invalid activity.
    response = client.post(f"/activities/{invalid_activity}/signup", params={"email": email})

    # Assert: verify the app returns a 404 for unknown activities.
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_from_activity_removes_participant():
    # Arrange: remove an existing participant from a valid activity.
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"

    # Act: delete the signup for the participant.
    response = client.delete(f"/activities/{activity_name}/signup", params={"email": existing_email})

    # Assert: ensure the participant was removed successfully.
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {existing_email} from {activity_name}"}
    assert existing_email not in activities[activity_name]["participants"]


def test_unregister_missing_participant_returns_not_found():
    # Arrange: choose a valid activity but an email that is not signed up.
    activity_name = "Chess Club"
    missing_email = "missing@student.edu"

    # Act: attempt to remove the nonexistent participant.
    response = client.delete(f"/activities/{activity_name}/signup", params={"email": missing_email})

    # Assert: confirm the app returns a 404 for missing participants.
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"


def test_unregister_invalid_activity_returns_not_found():
    # Arrange: choose an invalid activity name.
    invalid_activity = "Nonexistent Club"
    email = "student@mergington.edu"

    # Act: attempt to unregister from the invalid activity.
    response = client.delete(f"/activities/{invalid_activity}/signup", params={"email": email})

    # Assert: ensure the app returns a 404 for unknown activities.
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
