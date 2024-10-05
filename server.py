import json
from flask import Flask, render_template, request, redirect, flash, url_for, session
import portalocker
import os

# Get the current directory of the script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load clubs and competitions from JSON files
def loadClubs():
    """
    Load the list of clubs from the 'clubs.json' file.
    
    Returns:
        list: List of clubs loaded from the JSON file.
    """
    clubs_path = os.path.join(BASE_DIR, 'clubs.json')
    with open(clubs_path) as c:
        listOfClubs = json.load(c)  # No need to access with ['clubs']
    return listOfClubs

def loadCompetitions():
    """
    Load the list of competitions from the 'competitions.json' file with a shared lock for reading.
    
    Returns:
        list: List of competitions loaded from the JSON file.
    """
    # Get the absolute path to the competitions.json file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    competitions_path = os.path.join(base_dir, 'competitions.json')
    
    # Load the competitions dictionary from the JSON file
    with open(competitions_path, 'r') as comps_file:
        competitions_data = json.load(comps_file)
    
    # Extract the list of competitions from the dictionary
    listOfCompetitions = competitions_data.get('competitions', [])
    
    # Ensure that we have loaded a list of competitions
    if not listOfCompetitions:
        raise ValueError("Competitions data is empty or invalid.")
    
    return listOfCompetitions

app = Flask(__name__)
app.secret_key = 'something_special'  # Change for security in production

# Load initial data
competitions = loadCompetitions()
clubs = loadClubs()

# Home route
@app.route('/')
def index():
    """
    Route for the home page.
    
    Returns:
        Rendered template for the home page.
    """
    return render_template('index.html')

# Summary route to display club details
@app.route('/showSummary', methods=['POST'])
def showSummary():
    """
    Route to show the summary of the club based on the provided email/Secretary.
    
    Returns:
        Rendered template of the welcome page if the club is found, or redirects to the home page if not.
    """
    # Load the clubs and competitions from the JSON files
    clubs = loadClubs()
    competitions = loadCompetitions()

    # Retrieve email from the request form
    email = request.form.get('email')
    
    if not email:
        flash("Email field is required.")
        return redirect(url_for('index'))

    # Find the club based on the email provided in the form
    club = next((club for club in clubs if club['email'] == email), None)
    
    if club:
        # If the club is found, log them in and display the welcome page
        session['logged_in'] = True
        session['club'] = club['name']  # Alternatively, you can store the whole club

        # Ensure competitions data is passed to the template
        return render_template('welcome.html', club=club, competitions=competitions)
    else:
        # If no club is found, flash an error and redirect to the home page
        flash("Email not found. Please try again.")
        return redirect(url_for('index'))





# Booking route
@app.route('/book/<competition>/<club>')
def book(competition, club):
    """
    Route for booking a competition spot by the club.
    
    Args:
        competition (str): Name of the competition.
        club (str): Name of the club.
    
    Returns:
        Rendered booking page if valid, otherwise redirects to home.
    """
    if not session.get('logged_in'):
        flash("You must be logged in to book.")
        return redirect(url_for('index'))
    
    competition = competition.replace("_", " ")  
    club = club.replace("_", " ") 

    foundClub = [c for c in clubs if c['name'] == club]
    foundCompetition = [c for c in competitions if c['name'] == competition]

    if foundClub and foundCompetition:
        return render_template('booking.html', club=foundClub[0], competition=foundCompetition[0])
    else:
        flash("Club or competition not found.")
        return redirect(url_for('index'))

# Purchase places route
@app.route('/purchasePlaces', methods=['POST'])
def purchasePlaces():
    """
    Route to handle the purchase of competition spots by a club.
    
    Returns:
        Rendered template for the welcome page with a booking status message.
    """
    competition_name = request.form['competition'].replace("_", " ")
    club_name = request.form['club']

    # Find the competition and club
    competition = next((c for c in competitions if c['name'] == competition_name), None)
    club = next((c for c in clubs if c['name'] == club_name), None)

    if not competition or not club:
        flash("Competition or club not found.")
        return redirect(url_for('index'))

    # Attempt to convert the input to integer and handle invalid input
    try:
        spots_requested = int(request.form['places'])
        if spots_requested <= 0:
            flash('Number of spots requested must be greater than zero')
            return render_template('welcome.html', club=club, competitions=competitions)
    except ValueError:
        flash('Invalid input for number of spots')
        return render_template('welcome.html', club=club, competitions=competitions)

    # Use the book_spot helper function to handle booking logic
    booking_result = book_spot(club, competition, spots_requested)

    if booking_result == "Booking successful":
        updateCompetitions()
        updateClubs()
        flash('Great - booking complete!')
    else:
        flash(booking_result)
    
    return render_template('welcome.html', club=club, competitions=competitions)




# Update the clubs JSON file
def updateClubs():
    """
    Update the 'clubs.json' file with the current state of clubs.
    """
    clubs_path = os.path.join(BASE_DIR, 'clubs.json')
    with open(clubs_path, 'w') as c:
        json.dump(clubs, c, indent=4)

# Update the competitions JSON file
def updateCompetitions():
    """
    Update the 'competitions.json' file with the current state of competitions.
    """
    competitions_path = os.path.join(BASE_DIR, 'competitions.json')
    with open(competitions_path, 'w') as comps_file:
        portalocker.lock(comps_file, portalocker.LOCK_EX)  # Exclusive lock for writing
        json.dump({'competitions': competitions}, comps_file, indent=4)

# Helper function to book spots
def book_spot(user, competition, spots_requested):
    """
    Helper function to handle spot booking logic for a user in a competition.
    
    Args:
        user (dict): The club attempting to book spots.
        competition (dict): The competition where spots are being booked.
        spots_requested (int): The number of spots requested.
    
    Returns:
        str: Result of the booking attempt.
    """
    try:
        spots_requested = int(spots_requested)
    except ValueError:
        return "Invalid input for spots requested"

    if spots_requested <= 0:
        return "Number of spots requested must be greater than zero"

    if spots_requested > 12:
        return "Cannot book more than 12 spots"

    if competition['available_spots'] < spots_requested:
        return "Not enough available spots"

    if user['points'] < spots_requested:
        return "Not enough points"

    # Deduct points and reduce available spots if all checks passed
    user['points'] -= spots_requested
    competition['available_spots'] -= spots_requested

    return "Booking successful"





# Route to display club points
@app.route('/points')
def displayPoints():
    """
    Route to display the points of all clubs.
    
    Returns:
        Rendered template for the points page showing all clubs.
    """
    return render_template('points.html', clubs=clubs)

# Logout route
@app.route('/logout')
def logout():
    """
    Route to handle user logout and session clearance.
    
    Returns:
        Redirect to the home page after logging out.
    """
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
