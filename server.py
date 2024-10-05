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
    """
    Route for booking a competition spot by the club.
    """
    if not session.get("logged_in"):
        flash("You must be logged in to book.")
        return redirect(url_for("index"))

    competition = competition.replace("_", " ")
    club = club.replace("_", " ")

    foundClub = next((c for c in clubs if c["name"] == club), None)
    foundCompetition = next((c for c in competitions if c["name"] == competition), None)

    if foundClub and foundCompetition:
        return render_template("booking.html", club=foundClub, competition=foundCompetition)
    else:
        flash("Club or competition not found.")
        return redirect(url_for("index"))


# Purchase places route
@app.route('/purchasePlaces', methods=['POST'])
def purchasePlaces():
    competition = [c for c in competitions if c['name'] == request.form['competition']][0]
    club = [c for c in clubs if c['name'] == request.form['club']][0]
    placesRequired = int(request.form['places'])
    
    if placesRequired <= int(competition['numberOfPlaces']):
        competition['numberOfPlaces'] = int(competition['numberOfPlaces']) - placesRequired
        flash('Great - booking complete!')
    else:
        flash('Not enough places available.')
    
    return render_template('welcome.html', club=club, competitions=competitions)

# TODO: Add route for points display

# Logout route
@app.route('/logout')
def logout():
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
