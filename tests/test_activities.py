"""
Integration tests for FastAPI activities API endpoints.

Tests are organized by endpoint and follow the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up test data and fixtures
- Act: Execute the operation under test
- Assert: Verify the result matches expectations
"""

import pytest


# ============================================================================
# GET /activities Tests
# ============================================================================

class TestGetActivities:
    """Tests for GET /activities endpoint (list all activities)."""
    
    def test_get_activities_returns_all_activities(self, client):
        """
        Test: GET /activities returns 200 with all 9 activities
        
        Arrange: Use client fixture with fresh app state
        Act: GET /activities
        Assert: Status 200, response contains all 9 activities
        """
        # Arrange
        expected_activities = [
            "Chess Club", "Programming Class", "Gym Class",
            "Basketball Team", "Tennis Club", "Drama Club",
            "Art Class", "Debate Team", "Science Club"
        ]
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9
        assert all(activity in data for activity in expected_activities)
    
    def test_get_activities_response_structure(self, client):
        """
        Test: Each activity has required fields (description, schedule, max_participants, participants)
        
        Arrange: Use client fixture
        Act: GET /activities
        Assert: Response structure is valid for all activities
        """
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        
        # Assert
        data = response.json()
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data, dict), f"{activity_name} should be a dict"
            assert required_fields.issubset(
                activity_data.keys()
            ), f"{activity_name} missing required fields"
            assert isinstance(activity_data["participants"], list), \
                f"participants for {activity_name} should be a list"
    
    def test_get_activities_initial_participants(self, client, sample_activities):
        """
        Test: Activities have correct initial participant counts
        
        Arrange: Use client and sample_activities fixtures
        Act: GET /activities
        Assert: Participant counts match expected initial state
        """
        # Arrange: sample_activities provides expected counts
        
        # Act
        response = client.get("/activities")
        
        # Assert
        data = response.json()
        for activity_name, expected_count in sample_activities.items():
            actual_count = len(data[activity_name]["participants"])
            assert actual_count == expected_count, \
                f"{activity_name} should have {expected_count} participants, got {actual_count}"


# ============================================================================
# GET / Tests
# ============================================================================

class TestRootRedirect:
    """Tests for GET / endpoint (redirect to static files)."""
    
    def test_root_redirect_to_static(self, client):
        """
        Test: GET / redirects to static index.html
        
        Arrange: Use client fixture
        Act: GET / (follow_redirects=False to capture redirect response)
        Assert: Status 307 or 303 (redirect) pointing to /static/index.html
        """
        # Arrange
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code in [307, 303], \
            "Root should return redirect status code"
        assert "static" in response.headers.get("location", "").lower(), \
            "Redirect location should point to /static"


# ============================================================================
# POST /activities/{activity_name}/signup Tests
# ============================================================================

class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_happy_path(self, client):
        """
        Test: Valid signup returns 200 and adds participant to activity
        
        Arrange: Prepare activity name and new email not yet signed up
        Act: POST to /activities/{activity}/signup with email
        Assert: Status 200, response message, participant in activity
        """
        # Arrange
        activity_name = "Chess Club"
        email = "newtestudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
        
        # Verify participant was added by fetching activities
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]
    
    def test_signup_duplicate_email_returns_400(self, client):
        """
        Test: Duplicate signup (same email twice) returns 400
        
        Arrange: Try to signup same email for same activity twice
        Act: POST /signup first time (succeeds), POST second time
        Assert: First request 200, second request 400
        """
        # Arrange
        activity_name = "Programming Class"
        email = "duplicate@mergington.edu"
        
        # Act & Assert
        # First signup should succeed
        first_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert first_response.status_code == 200
        
        # Second signup should fail
        second_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert second_response.status_code == 400
        assert "already signed up" in second_response.json()["detail"]
    
    def test_signup_nonexistent_activity_returns_404(self, client):
        """
        Test: Signup for non-existent activity returns 404
        
        Arrange: Use activity name that doesn't exist
        Act: POST to /activities/NonexistentActivity/signup
        Assert: Status 404, error message
        """
        # Arrange
        activity_name = "NonexistentActivity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_can_exceed_max_participants(self, client):
        """
        Test: Current app allows unlimited participants (no max capacity enforcement)
        
        Note: This test documents current app behavior. The app stores max_participants
        but doesn't enforce it. Future enhancement: implement capacity checking.
        
        Arrange: Get an activity with max_participants limit
        Act: Sign up more participants than max_participants allows
        Assert: App allows it (no validation on max capacity yet)
        """
        # Arrange
        activity_name = "Basketball Team"
        max_participants = 15
        
        # Get initial state
        activities_response = client.get("/activities")
        initial_count = len(activities_response.json()[activity_name]["participants"])
        
        # Act: Fill up to max and add one more
        for i in range(max_participants):
            email = f"basketball_player_{i}@mergington.edu"
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            # All signups succeed (no capacity limit enforced)
            assert response.status_code == 200
        
        # Assert: Final count exceeds max_participants (confirming no enforcement)
        activities_response = client.get("/activities")
        final_count = len(activities_response.json()[activity_name]["participants"])
        assert final_count == initial_count + max_participants
    
    def test_signup_multiple_emails_for_same_activity(self, client):
        """
        Test: Different emails can signup for same activity (happy path for multiple)
        
        Arrange: Prepare two different emails
        Act: POST signup for first email, then second email
        Assert: Both return 200, both appear in participants
        """
        # Arrange
        activity_name = "Drama Club"
        email1 = "actor1@mergington.edu"
        email2 = "actor2@mergington.edu"
        
        # Act
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email1}
        )
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email2}
        )
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email1 in participants
        assert email2 in participants


# ============================================================================
# DELETE /activities/{activity_name}/unregister Tests
# ============================================================================

class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint."""
    
    def test_unregister_happy_path(self, client):
        """
        Test: Valid unregister returns 200 and removes participant
        
        Arrange: Signup a student, then prepare to unregister
        Act: DELETE /activities/{activity}/unregister with email
        Assert: Status 200, participant removed from activity
        """
        # Arrange
        activity_name = "Art Class"
        email = "artist@mergington.edu"
        
        # Setup: Signup the student first
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Act: Unregister the student
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity_name]["participants"]
    
    def test_unregister_nonexistent_activity_returns_404(self, client):
        """
        Test: Unregister from non-existent activity returns 404
        
        Arrange: Use activity name that doesn't exist
        Act: DELETE /activities/NonexistentActivity/unregister
        Assert: Status 404
        """
        # Arrange
        activity_name = "NonexistentActivity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_unregister_not_registered_returns_404(self, client):
        """
        Test: Unregister for email not in participants returns 404
        
        Arrange: Try to unregister email that was never signed up
        Act: DELETE with email not in participants list
        Assert: Status 404, error message
        """
        # Arrange
        activity_name = "Science Club"
        email = "never_registered@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not registered" in response.json()["detail"].lower()
    
    def test_unregister_double_unregister_returns_404(self, client):
        """
        Test: Unregister same student twice returns 404 on second attempt
        
        Arrange: Signup student, unregister once, prepare for second unregister
        Act: Unregister first time (success), unregister second time
        Assert: First 200, second 404
        """
        # Arrange
        activity_name = "Tennis Club"
        email = "tennis_player@mergington.edu"
        
        # Setup: Signup the student
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Act & Assert
        # First unregister should succeed
        first_response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        assert first_response.status_code == 200
        
        # Second unregister should fail
        second_response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        assert second_response.status_code == 404
        assert "not registered" in second_response.json()["detail"].lower()
    
    def test_signup_unregister_signup_flow(self, client):
        """
        Test: Full flow - Signup → Unregister → Signup again
        
        Arrange: Prepare activity and email
        Act: 
            1. Signup for activity
            2. Unregister from activity
            3. Signup again for same activity
        Assert: All three operations succeed (200, 200, 200)
        """
        # Arrange
        activity_name = "Gym Class"
        email = "gym_member@mergington.edu"
        
        # Act 1: First signup
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Act 2: Unregister
        response2 = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Act 3: Signup again
        response3 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200
        
        # Verify final state: participant is registered
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]


# ============================================================================
# Parametrized Tests (Multiple Scenarios)
# ============================================================================

class TestSignupMultipleActivities:
    """Parametrized tests for signup across multiple activities."""
    
    @pytest.mark.parametrize("activity_name", [
        "Chess Club",
        "Programming Class",
        "Gym Class",
        "Basketball Team",
        "Tennis Club",
    ])
    def test_signup_works_for_all_activities(self, client, activity_name):
        """
        Test: Signup endpoint works for each activity
        
        Arrange: Parametrize across 5 activities
        Act: POST signup for each activity
        Assert: All return 200
        """
        # Arrange
        email = f"student_{activity_name.replace(' ', '_')}@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity_name]["participants"]
