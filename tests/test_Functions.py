import sys
import os
import unittest

# Add the parent directory to the path so we can import server
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from server import app
import server  # Import server to access server.clubs and server.competitions

class FunctionalTestCase(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        server.app.testing = True  # Ensure the server is aware of testing mode

        # Base data for clubs and competitions
        self.base_clubs = [
            {
                "name": "Simply Lift",
                "email": "john@simplylift.co",
                "points": "15"  # Use string for consistency with JSON data
            },
            {
                "name": "Iron Temple",
                "email": "admin@irontemple.com",
                "points": "4"
            },
            {
                "name": "She Lifts",
                "email": "kate@shelifts.co.uk",
                "points": "12"
            }
        ]

        self.base_competitions = [
            {
                "name": "Spring Festival",
                "date": "2025-03-27 10:00:00",
                "numberOfPlaces": "20"  # Use string for consistency with JSON data
            },
            {
                "name": "Fall Classic",
                "date": "2025-10-22 13:30:00",
                "numberOfPlaces": "13"
            }
        ]

        # Directly assign the test data to server.clubs and server.competitions
        server.clubs.clear()
        server.clubs.extend([club.copy() for club in self.base_clubs])
        server.competitions.clear()
        server.competitions.extend([comp.copy() for comp in self.base_competitions])

    def test_points_page_public_access(self):
        """Test that the points page is accessible to the public."""
        response = self.client.get("/points")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Points", response.data)  # Adjust based on actual content of points.html

    def test_show_summary(self):
        """Test that the welcome page is displayed after logging in with a valid email."""
        response = self.client.post(
            "/showSummary", data={"email": server.clubs[0]["email"]}, follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome", response.data)

    def test_booking_page(self):
        """Test that the booking page loads properly."""
        # Simulate logging in first
        self.client.post("/showSummary", data={"email": server.clubs[0]["email"]})

        # Attempt to book a place
        competition_name = server.competitions[0]["name"]
        club_name = server.clubs[0]["name"]
        response = self.client.get(f"/book/{competition_name}/{club_name}")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"How many places?", response.data)

    def test_purchase_places_success(self):
        """Test successful purchase of places."""

        # Ensure the club has sufficient points
        server.clubs[0]["points"] = "15"

        # Simulate logging in
        self.client.post("/showSummary", data={"email": server.clubs[0]["email"]})

        # Try to book a valid number of spots
        response = self.client.post(
            "/purchasePlaces",
            data={
                "competition": server.competitions[0]["name"],
                "club": server.clubs[0]["name"],
                "places": "3",  # Sufficient spots and points
            },
            follow_redirects=True
        )

        # Validate that the booking is successful
        self.assertIn(b"Great-booking complete!", response.data)

    def test_purchase_places_insufficient_points(self):
        """Test purchase places failure due to insufficient points."""

        # Ensure the club has insufficient points
        server.clubs[0]["points"] = "2"  # Not enough points for booking

        # Simulate logging in
        self.client.post("/showSummary", data={"email": server.clubs[0]["email"]})

        # Try to book more places than points
        response = self.client.post(
            "/purchasePlaces",
            data={
                "competition": server.competitions[0]["name"],
                "club": server.clubs[0]["name"],
                "places": "5",  # More spots than the club has points for
            },
            follow_redirects=True
        )

        # Validate that the correct message is flashed
        self.assertIn(b"Not enough points", response.data)

    def test_purchase_places_exceeds_spot_limit(self):
        """Test purchase failure due to exceeding 12 spot limit."""

        # Ensure the club has sufficient points
        server.clubs[0]["points"] = "15"  # Sufficient points

        # Simulate logging in
        self.client.post("/showSummary", data={"email": server.clubs[0]["email"]})

        # Try to book more than 12 spots
        response = self.client.post(
            "/purchasePlaces",
            data={
                "competition": server.competitions[0]["name"],
                "club": server.clubs[0]["name"],
                "places": "13",  # Exceeds the 12 spots limit
            },
            follow_redirects=True
        )

        # Validate that the correct message is shown
        self.assertIn(b"Cannot book more than 12 spots", response.data)

    def test_invalid_email_login(self):
        """Test login attempt with an invalid email that is not in the club list."""

        invalid_email = "invalidemail@example.com"  # This email should not exist in clubs.json

        # Post the form with the invalid email and follow the redirect
        response = self.client.post(
            "/showSummary", data={"email": invalid_email}, follow_redirects=True
        )

        # Ensure the status code is 200 after following the redirect
        self.assertEqual(response.status_code, 200)

        # Check that the flash message 'Email not found' is in the response data
        self.assertIn(b"Email not found", response.data)

    def test_logout(self):
        """Test user logout."""

        # Simulate logging in
        self.client.post("/showSummary", data={"email": server.clubs[0]["email"]})

        # Now log out
        response = self.client.get("/logout", follow_redirects=True)

        # Check that after logout, the user is redirected to the home page with the correct text
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Please enter your secretary email to continue", response.data)

    def test_invalid_input_booking(self):
        """Test booking with invalid input (non-numeric places)."""

        # Simulate logging in
        self.client.post("/showSummary", data={"email": server.clubs[0]["email"]})

        response = self.client.post(
            "/purchasePlaces",
            data={
                "competition": server.competitions[0]["name"],
                "club": server.clubs[0]["name"],
                "places": "abc",  # Non-numeric input
            },
            follow_redirects=True
        )

        self.assertIn(b"Invalid input for number of spots", response.data)

    def test_booking_exceeds_available_spots(self):
        """Test booking more spots than are available in the competition."""

        # Set available spots to 5
        server.competitions[0]["numberOfPlaces"] = "5"

        # Simulate logging in first
        self.client.post("/showSummary", data={"email": server.clubs[0]["email"]})

        # Attempt to book more spots than available
        response = self.client.post(
            "/purchasePlaces",
            data={
                "competition": server.competitions[0]["name"],
                "club": server.clubs[0]["name"],
                "places": "10",  # Requesting 10 spots, only 5 available
            },
            follow_redirects=True
        )

        self.assertIn(b"Not enough available spots", response.data)

    def test_booking_negative_places(self):
        """Test booking with negative number of places."""

        # Simulate logging in
        self.client.post("/showSummary", data={"email": server.clubs[0]["email"]})

        # Attempt to book negative spots
        response = self.client.post(
            "/purchasePlaces",
            data={
                "competition": server.competitions[0]["name"],
                "club": server.clubs[0]["name"],
                "places": "-3",  # Negative number of places
            },
            follow_redirects=True
        )

        self.assertIn(b"Number of spots requested must be greater than zero", response.data)

if __name__ == "__main__":
    unittest.main()
