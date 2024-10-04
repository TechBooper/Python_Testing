import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from server import app, loadClubs, loadCompetitions
import unittest

class FunctionalTestCase(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

        # Load clubs and competitions for testing
        self.clubs = loadClubs()
        self.competitions = loadCompetitions()

    def test_points_page_public_access(self):
        response = self.client.get('/points')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Points', response.data)  # Adjust based on actual content of points.html


    def test_show_summary(self):
        """Test that the welcome page is displayed after logging in with a valid email"""
        response = self.client.post('/showSummary', data={'email': self.clubs[0]['email']})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome', response.data)

    def test_booking_page(self):
        """Test that the booking page loads properly"""
        # Simulate logging in first
        self.client.post('/showSummary', data={'email': self.clubs[0]['email']})

        # Attempt to book a place
        competition_name = self.competitions[0]['name']
        club_name = self.clubs[0]['name']
        response = self.client.get(f'/book/{competition_name}/{club_name}')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Book', response.data)

    def test_purchase_places_success(self):
        """Test successful purchase of places"""
        self.client.post('/showSummary', data={'email': self.clubs[0]['email']})
        
        response = self.client.post('/purchasePlaces', data={
            'competition': self.competitions[0]['name'],
            'club': self.clubs[0]['name'],
            'places': '3'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Great - booking complete!', response.data)

    def test_purchase_places_insufficient_points(self):
        """Test purchase places failure due to insufficient points"""
        self.client.post('/showSummary', data={'email': self.clubs[0]['email']})

        # Attempt to purchase more places than points available
        response = self.client.post('/purchasePlaces', data={
            'competition': self.competitions[0]['name'],
            'club': self.clubs[0]['name'],
            'places': '100'  # More than the club's points
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Not enough points', response.data)

    def test_purchase_places_exceeds_spot_limit(self):
        """Test purchase failure due to exceeding 12 spot limit"""
        self.client.post('/showSummary', data={'email': self.clubs[0]['email']})

        # Attempt to book more than 12 spots 
        response = self.client.post('/purchasePlaces', data={
            'competition': self.competitions[0]['name'],
            'club': self.clubs[0]['name'],
            'places': '13'
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You cannot book more than 12 places in total for this competition.', response.data)

    def test_invalid_email_login(self):
        """Test login attempt with an invalid email that is not in the club list"""
        invalid_email = "invalidemail@example.com"  # This email should not exist in clubs.json
        response = self.client.post('/showSummary', data={'email': invalid_email})
        
        # Ensure the response redirects to the home page (login failed)
        self.assertEqual(response.status_code, 302)
        
        # Follow the redirect and check if the error message is displayed
        response = self.client.get(response.location, follow_redirects=True)
        self.assertIn(b'Email not found', response.data)  # Ensure error message is shown

    def test_logout(self):
        """Test user logout"""
        # Simulate logging in
        self.client.post('/showSummary', data={'email': self.clubs[0]['email']})
        
        # Now log out
        response = self.client.get('/logout', follow_redirects=True)
        
        # Check that after logout, the user is redirected to the home page with the correct text
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Please enter your secretary email to continue', response.data)


if __name__ == '__main__':
    unittest.main()
