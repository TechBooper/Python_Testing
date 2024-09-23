import json
from flask import Flask, render_template, request, redirect, flash, url_for, session
import portalocker

# Load clubs and competitions from JSON files
def loadClubs():
    """
    Load the list of clubs from the 'clubs.json' file.
    
    Returns:
        list: List of clubs loaded from the JSON file.
    """
    with open('C:/Users/Marwane/Documents/GitHub/Python_Testing/clubs.json') as c:
        listOfClubs = json.load(c)['clubs']
    return listOfClubs

def loadCompetitions():
    """
    Load the list of competitions from the 'competitions.json' file with a shared lock for reading.
    
    Returns:
        list: List of competitions loaded from the JSON file.
    """
    with open('C:/Users/Marwane/Documents/GitHub/Python_Testing/competitions.json', 'r') as comps_file:
        portalocker.lock(comps_file, portalocker.LOCK_SH)  # Shared lock for reading
        listOfCompetitions = json.load(comps_file)['competitions']
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
    Route to show the summary of the club based on the provided email.
    
    Returns:
        Rendered template of the welcome page if the club is found, or redirects to the home page if not.
    """
    club = [club for club in clubs if club['email'] == request.form['email']]
    if club:
        club = club[0]
        session['logged_in'] = True
        session['club'] = club['name']
        return render_template('welcome.html', club=club, competitions=competitions)
    else:
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
    competition = [c for c in competitions if c['name'] == competition_name]
    club = [c for c in clubs if c['name'] == request.form['club']]

    if competition and club:
        competition = competition[0]
        club = club[0]
        placesRequired = int(request.form['places'])

        if 'bookings' not in competition:
            competition['bookings'] = {}

        alreadyBookedByClub = competition['bookings'].get(club['name'], 0)

        if placesRequired + alreadyBookedByClub > 12:
            flash('You cannot book more than 12 places in total for this competition.')
        elif placesRequired <= int(competition['available_spots']):
            if int(club['points']) >= placesRequired:
                competition['available_spots'] -= placesRequired
                club['points'] -= placesRequired
                competition['bookings'][club['name']] = alreadyBookedByClub + placesRequired
                updateCompetitions()
                updateClubs()
                flash('Great - booking complete!')
            else:
                flash('Not enough points.')
        else:
            flash('Not enough places available.')
    else:
        flash("Competition or club not found.")
    
    return render_template('welcome.html')

# Update the clubs JSON file
def updateClubs():
    """
    Update the 'clubs.json' file with the current state of clubs.
    """
    with open('clubs.json', 'w') as c:
        json.dump(clubs, c, indent=4)

# Update the competitions JSON file
def updateCompetitions():
    """
    Update the 'competitions.json' file with the current state of competitions.
    """
    with open('C:/Users/Marwane/Documents/GitHub/Python_Testing/competitions.json', 'w') as comps_file:
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
    if spots_requested > 12:
        return "Cannot book more than 12 spots"
    
    if user['points'] < spots_requested:
        return "Not enough points"
    
    if competition['available_spots'] < spots_requested:
        return "Not enough available spots"
    
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
