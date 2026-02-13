"""Tests for the High School Management System API"""
import sys
from pathlib import Path

# Add the src directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_dict(self):
        """Test that /activities returns a dictionary of activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_get_activities_contains_expected_fields(self):
        """Test that activities have expected fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_details in activities.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)

    def test_get_activities_has_chess_club(self):
        """Test that Chess Club activity exists"""
        response = client.get("/activities")
        activities = response.json()
        assert "Chess Club" in activities


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_for_activity_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Programming%20Class/signup?email=test@mergington.edu",
            follow_redirects=False
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_activity_not_found(self):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/NonExistent/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_registration(self):
        """Test that duplicate registration is prevented"""
        email = "duplicate@test.edu"
        activity = "Gym%20Class"
        
        # First signup should succeed
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_returns_success_message(self):
        """Test that signup returns a success message"""
        response = client.post(
            "/activities/Tennis%20Club/signup?email=newstudent@test.edu"
        )
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "newstudent@test.edu" in result["message"]
        assert "Tennis Club" in result["message"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""

    def test_unregister_success(self):
        """Test successful unregistration from an activity"""
        email = "unregister@test.edu"
        
        # First sign up
        signup_response = client.post(
            f"/activities/Debate%20Team/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Then unregister
        response = client.delete(
            f"/activities/Debate%20Team/signup?email={email}"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_not_signed_up(self):
        """Test unregistering from activity when not signed up"""
        response = client.delete(
            "/activities/Science%20Club/signup?email=notregistered@test.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_activity_not_found(self):
        """Test unregistering from non-existent activity"""
        response = client.delete(
            "/activities/NotAnActivity/signup?email=test@test.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_removes_participant(self):
        """Test that unregistering actually removes the participant"""
        email = "tempstudent@test.edu"
        activity_name = "Basketball%20Team"
        
        # Sign up
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Verify they're signed up
        activities = client.get("/activities").json()
        assert email in activities["Basketball Team"]["participants"]
        
        # Unregister
        client.delete(f"/activities/{activity_name}/signup?email={email}")
        
        # Verify they're removed
        activities = client.get("/activities").json()
        assert email not in activities["Basketball Team"]["participants"]


class TestEdgeCases:
    """Tests for edge cases and validation"""

    def test_multiple_signups_and_unregisters(self):
        """Test multiple signup and unregister operations"""
        email = "cycletest@test.edu"
        activity = "Painting%20Studio"
        
        # Sign up
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response1.status_code == 200
        
        # Unregister
        response2 = client.delete(f"/activities/{activity}/signup?email={email}")
        assert response2.status_code == 200
        
        # Sign up again should work
        response3 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response3.status_code == 200

    def test_activities_list_immutable_between_requests(self):
        """Test that activities exist across multiple requests"""
        response1 = client.get("/activities")
        activities1 = response1.json()
        
        response2 = client.get("/activities")
        activities2 = response2.json()
        
        # Both responses should have the same initial activities
        assert "Chess Club" in activities1
        assert "Chess Club" in activities2
