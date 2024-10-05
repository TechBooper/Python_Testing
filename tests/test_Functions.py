import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from server import app, loadClubs, loadCompetitions
import unittest
import server  

class FunctionalTestCase(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

        # Reload clubs and competitions to ensure data is fresh for each test
        self.clubs = loadClubs()
        self.competitions = loadCompetitions()

        # Ensure the first club has 15 points for testing
        self.clubs[0]['points'] = 15

        # Ensure there are enough spots in the first competition
        self.competitions[0]['available_spots'] = 20

        # Override the application's global data with test data
        import server
        server.clubs = self.clubs
        server.competitions = self.competitions

        # Assert that the data is correctly loaded
        assert len(self.clubs) > 0, "Clubs data failed to load"
        assert len(self.competitions) > 0, "Competitions data failed to load"



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
        """Test successful purchase of places."""
        # Ensure the club has sufficient points
        self.clubs[0]['points'] = 15  # Sufficient points
        
        # Simulate logging in
        self.client.post('/showSummary', data={'email': self.clubs[0]['email']})
        
        # Try to book a valid number of spots
        response = self.client.post('/purchasePlaces', data={
            'competition': self.competitions[0]['name'],
            'club': self.clubs[0]['name'],
            'places': '3'  # Sufficient spots and points
        })
        
        # Validate that the booking is successful
        self.assertIn(b'Great - booking complete!', response.data)



    def test_purchase_places_insufficient_points(self):
        """Test purchase places failure due to insufficient points."""
        # Ensure the club has insufficient points
        self.clubs[0]['points'] = 2  # Not enough points for booking
        
        # Simulate logging in
        self.client.post('/showSummary', data={'email': self.clubs[0]['email']})
        
        # Try to book more places than points
        response = self.client.post('/purchasePlaces', data={
            'competition': self.competitions[0]['name'],
            'club': self.clubs[0]['name'],
            'places': '5'  # More spots than the club has points for
        })
        
        # Validate that the correct message is flashed
        self.assertIn(b'Not enough points', response.data)




    def test_purchase_places_exceeds_spot_limit(self):
        """Test purchase failure due to exceeding 12 spot limit."""
        # Ensure the club has sufficient points
        self.clubs[0]['points'] = 15  # Sufficient points
        
        # Simulate logging in
        self.client.post('/showSummary', data={'email': self.clubs[0]['email']})
        
        # Try to book more than 12 spots
        response = self.client.post('/purchasePlaces', data={
            'competition': self.competitions[0]['name'],
            'club': self.clubs[0]['name'],
            'places': '13'  # Exceeds the 12 spots limit
        })
        
        # Validate that the correct message is shown
        self.assertIn(b'Cannot book more than 12 spots', response.data)




    def test_invalid_email_login(self):
        """Test login attempt with an invalid email that is not in the club list."""
        invalid_email = "invalidemail@example.com"  # This email should not exist in clubs.json
        
        # Post the form with the invalid email and follow the redirect
        response = self.client.post('/showSummary', data={'email': invalid_email}, follow_redirects=True)
        
        # Ensure the status code is 200 after following the redirect
        self.assertEqual(response.status_code, 200)
        
        # Check that the flash message 'Email not found' is in the response data
        self.assertIn(b'Email not found', response.data)



    def test_logout(self):
        """Test user logout"""
        # Simulate logging in
        self.client.post('/showSummary', data={'email': self.clubs[0]['email']})
        
        # Now log out
        response = self.client.get('/logout', follow_redirects=True)
        
        # Check that after logout, the user is redirected to the home page with the correct text
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Please enter your secretary email to continue', response.data)

    
    def test_invalid_input_booking(self):
        self.client.post('/showSummary', data={'email': self.clubs[0]['email']})

        response = self.client.post('/purchasePlaces', data={
            'competition': self.competitions[0]['name'],
            'club': self.clubs[0]['name'],
            'places': 'abc'  # Non-numeric input
        })

    def test_booking_exceeds_available_spots(self):
        """Test booking more spots than are available in the competition."""
        # Simulate logging in first
        self.client.post('/showSummary', data={'email': self.clubs[0]['email']})

        competition = self.competitions[0]
        competition['available_spots'] = 5  # Set available spots to 5

        server.competitions = self.competitions  # Update server data

        # Attempt to book more spots than available
        response = self.client.post('/purchasePlaces', data={
            'competition': competition['name'],
            'club': self.clubs[0]['name'],
            'places': '10'  # Requesting 10 spots, only 5 available
        })

        self.assertIn(b'Not enough available spots', response.data)


if __name__ == '__main__':
    unittest.main()
