import unittest

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from server import app, loadClubs, loadCompetitions

class IntegrationTestCase(unittest.TestCase):

    def setUp(self):
        # Set up test client
        self.client = app.test_client()
        self.client.testing = True

        # Load initial data
        self.clubs = loadClubs()
        self.competitions = loadCompetitions()

        # Ensure the first club has sufficient points
        self.clubs[0]['points'] = 15  # Assign enough points for the test

        # Ensure the competition has enough available spots
        self.competitions[0]['available_spots'] = 25  # Adjust as needed

        # Override the application's global data with test data
        import server
        server.clubs = self.clubs
        server.competitions = self.competitions


    def test_show_summary(self):
        # Simulate posting an email for login
        response = self.client .post('/showSummary', data={'email': self.clubs[0]['email']})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome', response.data)  # Check if welcome page is rendered

    def test_booking(self):
        # Log in and go to booking page
        self.client.post('/showSummary', data={'email': self.clubs[0]['email']})
        competition_name = self.competitions[0]['name']
        club_name = self.clubs[0]['name']

        # Simulate booking
        response = self.client.get(f'/book/{competition_name}/{club_name}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Book', response.data)  # Check if booking page is rendered

    def test_purchase_places(self):
        # Log in
        self.client.post('/showSummary', data={'email': self.clubs[0]['email']})
        
        # Simulate purchasing places
        response = self.client.post('/purchasePlaces', data={
            'competition': self.competitions[0]['name'],
            'club': self.clubs[0]['name'],
            'places': 3
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'booking complete', response.data)

    def test_insufficient_points(self):
        # Set the club's points to a low value to simulate insufficient points
        self.clubs[0]['points'] = 2
        # Update the application's data with the modified club points
        import server
        server.clubs = self.clubs

        # Simulate logging in
        self.client.post('/showSummary', data={'email': self.clubs[0]['email']})
        
        # Request a number of spots less than or equal to 12 but more than the club's points
        response = self.client.post('/purchasePlaces', data={
            'competition': self.competitions[0]['name'],
            'club': self.clubs[0]['name'],
            'places': '5'  # Requesting 5 spots with only 2 points
        })
        
        self.assertIn(b'Not enough points', response.data)


if __name__ == '__main__':
    unittest.main()
