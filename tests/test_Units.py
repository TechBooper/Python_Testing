import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from server import book_spot


class BookingTestCase(unittest.TestCase):

    def test_successful_booking(self):
        competition = {"available_spots": 12}  # Fresh instance
        user = {"points": 5}  # Fresh instance for user dictionary
        spots_requested = 3

        result = book_spot(user, competition, spots_requested)

        self.assertEqual(result, "Booking successful")
        self.assertEqual(user["points"], 2)  # Points deducted correctly
        self.assertEqual(competition["available_spots"], 9)  # Spots deducted correctly

    def test_insufficient_points(self):

        competition = {"available_spots": 10}  # Fresh instance
        user = {"points": 2}  # Fresh instance
        spots_requested = 3

        result = book_spot(user, competition, spots_requested)

        self.assertEqual(result, "Not enough points")
        self.assertEqual(user["points"], 2)  # Points should not change
        self.assertEqual(competition["available_spots"], 10)  # Spots should not change

    def test_exceeds_spot_limit(self):
        competition = {"available_spots": 10}  # Fresh instance
        user = {"points": 10}  # Fresh instance
        spots_requested = 13

        result = book_spot(user, competition, spots_requested)

        self.assertEqual(result, "Cannot book more than 12 spots")
        self.assertEqual(user["points"], 10)  # Points should not change
        self.assertEqual(competition["available_spots"], 10)  # Spots should not change

    def test_booking_zero_spots(self):
        """Test booking zero spots."""
        competition = {"available_spots": 10}
        user = {"points": 10}
        spots_requested = 0

        result = book_spot(user, competition, spots_requested)

        self.assertEqual(result, "Number of spots requested must be greater than zero")
        self.assertEqual(user["points"], 10)  # Points should not change
        self.assertEqual(competition["available_spots"], 10)  # Spots should not change

    def test_booking_negative_spots(self):
        """Test booking a negative number of spots."""
        competition = {"available_spots": 10}
        user = {"points": 10}
        spots_requested = -3

        result = book_spot(user, competition, spots_requested)

        self.assertEqual(result, "Number of spots requested must be greater than zero")
        self.assertEqual(user["points"], 10)  # Points should not change
        self.assertEqual(competition["available_spots"], 10)  # Spots should not change

    def test_booking_non_integer_spots(self):
        """Test booking a non-integer number of spots."""
        competition = {"available_spots": 10}
        user = {"points": 10}
        spots_requested = "abc"  # Non-integer input

        result = book_spot(user, competition, spots_requested)

        self.assertEqual(result, "Invalid input for spots requested")
        self.assertEqual(user["points"], 10)  # Points should not change
        self.assertEqual(competition["available_spots"], 10)  # Spots should not change

    def test_booking_leads_to_negative_points(self):
        """Test that booking does not reduce user's points below zero."""
        competition = {"available_spots": 10}
        user = {"points": 5}
        spots_requested = 6  # User has fewer points than spots requested

        result = book_spot(user, competition, spots_requested)

        self.assertEqual(result, "Not enough points")
        self.assertEqual(user["points"], 5)  # Points should not change
        self.assertEqual(competition["available_spots"], 10)  # Spots should not change


if __name__ == "__main__":
    unittest.main()
