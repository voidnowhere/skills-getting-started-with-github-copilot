"""
Pytest configuration and shared fixtures for API tests.

This module provides pytest fixtures that set up test infrastructure:
- app: Fresh FastAPI app instance per test
- client: TestClient bound to the app fixture
- sample_activities: Initial app state snapshot
"""

import pytest
from starlette.testclient import TestClient
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path
import os


@pytest.fixture(scope="function")
def app():
    """
    FIXTURE: Create a fresh FastAPI app instance for each test.
    
    Scope: function (creates new instance per test)
    Purpose: Ensure test isolation - each test gets a clean in-memory state
    
    Returns:
        FastAPI: App instance with fresh activities dictionary
    """
    
    # Create a new FastAPI app instance
    test_app = FastAPI(
        title="Mergington High School API",
        description="API for viewing and signing up for extracurricular activities"
    )
    
    # Mount static files
    current_dir = Path(__file__).parent.parent  # Go up one level from tests/ to project root
    static_dir = os.path.join(current_dir, "src", "static")
    if os.path.exists(static_dir):
        test_app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # Fresh in-memory activity database for this test
    activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Competitive basketball training and games",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["james@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Learn tennis skills and participate in friendly matches",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:00 PM",
            "max_participants": 16,
            "participants": ["sarah@mergington.edu", "alex@mergington.edu"]
        },
        "Drama Club": {
            "description": "Perform in theatrical productions and develop acting skills",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 25,
            "participants": ["grace@mergington.edu", "lucas@mergington.edu"]
        },
        "Art Class": {
            "description": "Explore painting, drawing, and sculpture techniques",
            "schedule": "Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["nina@mergington.edu"]
        },
        "Debate Team": {
            "description": "Develop argumentation and public speaking skills through debates",
            "schedule": "Mondays and Fridays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["thomas@mergington.edu", "victoria@mergington.edu"]
        },
        "Science Club": {
            "description": "Conduct experiments and explore advanced scientific concepts",
            "schedule": "Tuesdays, 3:30 PM - 5:00 PM",
            "max_participants": 16,
            "participants": ["ryan@mergington.edu", "jessica@mergington.edu"]
        }
    }
    
    # Define routes on the test app
    @test_app.get("/")
    def root():
        return RedirectResponse(url="/static/index.html")
    
    @test_app.get("/activities")
    def get_activities():
        return activities
    
    @test_app.post("/activities/{activity_name}/signup")
    def signup_for_activity(activity_name: str, email: str):
        """Sign up a student for an activity"""
        # Arrange: Validate activity exists
        if activity_name not in activities:
            raise HTTPException(status_code=404, detail="Activity not found")
        
        # Arrange: Get the specific activity
        activity = activities[activity_name]
        
        # Arrange: Validate student is not already signed up
        if email in activity["participants"]:
            raise HTTPException(status_code=400, detail="Student already signed up for this activity")
        
        # Act: Add student
        activity["participants"].append(email)
        
        # Assert: Return success message
        return {"message": f"Signed up {email} for {activity_name}"}
    
    @test_app.delete("/activities/{activity_name}/unregister")
    def unregister_participant(activity_name: str, email: str):
        """Remove a student from an activity"""
        # Arrange: Validate activity exists
        if activity_name not in activities:
            raise HTTPException(status_code=404, detail="Activity not found")
        
        # Arrange: Get the activity
        activity = activities[activity_name]
        
        # Arrange: Validate student is registered
        if email not in activity["participants"]:
            raise HTTPException(status_code=404, detail="Student is not registered for this activity")
        
        # Act: Remove student
        activity["participants"].remove(email)
        
        # Assert: Return success message
        return {"message": f"Unregistered {email} from {activity_name}"}
    
    return test_app


@pytest.fixture(scope="function")
def client(app):
    """
    FIXTURE: Create a TestClient bound to the app fixture.
    
    Scope: function (depends on app fixture)
    Purpose: Provides HTTP client for making requests to the test app
    
    Args:
        app: Fresh FastAPI app instance from app fixture
        
    Returns:
        TestClient: HTTP client for testing endpoints
    """
    return TestClient(app)


@pytest.fixture(scope="function")
def sample_activities():
    """
    FIXTURE: Return initial activities state for validation.
    
    Scope: function
    Purpose: Provides expected initial state for assertions
    
    Returns:
        dict: Dictionary with activity names and expected initial participant counts
    """
    return {
        "Chess Club": 2,
        "Programming Class": 2,
        "Gym Class": 2,
        "Basketball Team": 1,
        "Tennis Club": 2,
        "Drama Club": 2,
        "Art Class": 1,
        "Debate Team": 2,
        "Science Club": 2,
    }
