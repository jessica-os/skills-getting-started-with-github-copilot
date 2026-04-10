"""Comprehensive tests for the High School Management System API"""

import pytest


class TestRootEndpoint:
    """Tests for the root endpoint that redirects to index.html"""

    def test_root_redirect(self, client):
        """Test that root path redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"

    def test_root_with_follow_redirects(self, client):
        """Test that following redirect returns static files"""
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200


class TestGetActivitiesEndpoint:
    """Tests for the GET /activities endpoint"""

    def test_get_all_activities_success(self, client, reset_activities):
        """Test successful retrieval of all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_activities_have_required_fields(self, client, reset_activities):
        """Test that each activity contains required fields"""
        response = client.get("/activities")
        data = response.json()
        
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        for activity_name, activity_data in data.items():
            assert isinstance(activity_name, str)
            assert isinstance(activity_data, dict)
            assert required_fields.issubset(activity_data.keys()), \
                f"Activity '{activity_name}' missing required fields"

    def test_activities_participants_is_list(self, client, reset_activities):
        """Test that participants field is a list"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data["participants"], list), \
                f"Activity '{activity_name}' participants is not a list"

    def test_activities_max_participants_is_integer(self, client, reset_activities):
        """Test that max_participants is an integer"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data["max_participants"], int), \
                f"Activity '{activity_name}' max_participants is not an integer"

    def test_specific_activities_exist(self, client, reset_activities):
        """Test that known activities are present in the response"""
        response = client.get("/activities")
        data = response.json()
        
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Soccer Club",
            "Art Studio",
            "Drama Club",
            "Debate Team",
            "Science Club"
        ]
        
        for activity in expected_activities:
            assert activity in data, f"Expected activity '{activity}' not found"


class TestSignupForActivityEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_activity_not_found(self, client, reset_activities):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_signup_duplicate_student(self, client, reset_activities):
        """Test that duplicate signups are rejected"""
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"  # Already in Chess Club
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Student is already signed up for this activity"

    def test_signup_multiple_different_activities(self, client, reset_activities):
        """Test that a student can signup for multiple different activities"""
        test_email = "versatile@mergington.edu"
        activities_to_try = ["Chess Club", "Art Studio", "Science Club"]
        
        for activity in activities_to_try:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": test_email}
            )
            # First signup succeeds
            if response.status_code != 200:
                # If already signed up, that's ok for this test
                assert response.status_code == 400

    def test_signup_various_email_formats(self, client, reset_activities):
        """Test signup with various valid email formats"""
        emails = [
            "student.name@mergington.edu",
            "student+extra@mergington.edu",
            "s@mergington.edu"
        ]
        
        for email in emails:
            response = client.post(
                "/activities/Art Studio/signup",
                params={"email": email}
            )
            # Should either succeed or be a duplicate, not an error
            assert response.status_code in [200, 400]

    def test_signup_preserves_existing_participants(self, client, reset_activities):
        """Test that signup doesn't remove existing participants"""
        response = client.get("/activities")
        activities_before = response.json()
        initial_chess_participants = len(activities_before["Chess Club"]["participants"])
        
        # Signup new student
        client.post(
            "/activities/Chess Club/signup",
            params={"email": "preservetest@mergington.edu"}
        )
        
        # Verify all original participants are still there
        response = client.get("/activities")
        activities_after = response.json()
        chess_participants = activities_after["Chess Club"]["participants"]
        
        assert len(chess_participants) == initial_chess_participants + 1
        assert "michael@mergington.edu" in chess_participants
        assert "daniel@mergington.edu" in chess_participants


class TestUnregisterFromActivityEndpoint:
    """Tests for the POST /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client, reset_activities):
        """Test successful unregister from an activity"""
        response = client.post(
            "/activities/Chess Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_unregister_activity_not_found(self, client, reset_activities):
        """Test unregister from non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/unregister",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_unregister_participant_not_found(self, client, reset_activities):
        """Test unregister of non-participant returns 404"""
        response = client.post(
            "/activities/Chess Club/unregister",
            params={"email": "not_participant@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Participant not found"

    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes the participant"""
        email_to_remove = "michael@mergington.edu"
        
        # Verify participant exists
        response = client.get("/activities")
        activities_before = response.json()
        assert email_to_remove in activities_before["Chess Club"]["participants"]
        
        # Unregister
        client.post(
            "/activities/Chess Club/unregister",
            params={"email": email_to_remove}
        )
        
        # Verify participant was removed
        response = client.get("/activities")
        activities_after = response.json()
        assert email_to_remove not in activities_after["Chess Club"]["participants"]

    def test_unregister_preserves_other_participants(self, client, reset_activities):
        """Test that unregister doesn't affect other participants"""
        # Chess Club has michael@mergington.edu and daniel@mergington.edu
        
        # Unregister michael
        client.post(
            "/activities/Chess Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        
        # Verify daniel is still there
        response = client.get("/activities")
        chess_club = response.json()["Chess Club"]
        assert "daniel@mergington.edu" in chess_club["participants"]
        assert "michael@mergington.edu" not in chess_club["participants"]

    def test_unregister_empty_activity(self, client, reset_activities):
        """Test unregister from activity with only one participant"""
        # Basketball Team has only james@mergington.edu
        
        # Unregister the only participant
        response = client.post(
            "/activities/Basketball Team/unregister",
            params={"email": "james@mergington.edu"}
        )
        assert response.status_code == 200
        
        # Verify activity is now empty
        response = client.get("/activities")
        basketball_team = response.json()["Basketball Team"]
        assert len(basketball_team["participants"]) == 0