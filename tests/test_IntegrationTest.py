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
        self.client.post('/showSummary', data={'email': self.clubs[0]['email']})
        
        response = self.client.post('/purchasePlaces', data={
            'competition': self.competitions[0]['name'],
            'club': self.clubs[0]['name'],
            'places': 100  
        })
        
        self.assertIn(b'Not enough points', response.data)  

if __name__ == '__main__':
    unittest.main()
