import json
from flask import Flask, render_template, request, redirect, flash, url_for

# Load clubs and competitions from JSON files
def loadClubs():
    with open('clubs.json') as c:
        listOfClubs = json.load(c)['clubs']
    return listOfClubs

def loadCompetitions():
    with open('competitions.json') as comps:
        listOfCompetitions = json.load(comps)['competitions']
    return listOfCompetitions

app = Flask(__name__)
app.secret_key = 'something_special'  # Change for security in production

# Load initial data
competitions = loadCompetitions()
clubs = loadClubs()

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Summary route to display club details
@app.route('/showSummary', methods=['POST'])
def showSummary():
    try:
        club = [club for club in clubs if club['email'] == request.form['email']][0]
        return render_template('welcome.html', club=club, competitions=competitions)
    except IndexError:
        flash("Email not found. Please try again.")
        return redirect(url_for('index'))

# Booking route
@app.route('/book/<competition>/<club>')
def book(competition, club):
    try:
        foundClub = [c for c in clubs if c['name'] == club][0]
        foundCompetition = [c for c in competitions if c['name'] == competition][0]
        return render_template('booking.html', club=foundClub, competition=foundCompetition)
    except IndexError:
        flash("Something went wrong - please try again")
        return render_template('welcome.html', club=club, competitions=competitions)

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

# TODO: Add route for points display

# Logout route
@app.route('/logout')
def logout():
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
