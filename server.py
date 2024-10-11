import json
from flask import Flask, render_template, request, redirect, flash, url_for, session
import portalocker
import os

# Get the current directory of the script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load clubs and competitions from JSON files
def loadClubs():
    clubs_path = os.path.join(BASE_DIR, "clubs.json")
    with open(clubs_path) as c:
        data = json.load(c)
        listOfClubs = data.get('clubs', [])
        if not listOfClubs:
            raise ValueError("Clubs data is empty or invalid.")
    return listOfClubs

def loadCompetitions():
    competitions_path = os.path.join(BASE_DIR, "competitions.json")
    with open(competitions_path, "r") as comps_file:
        competitions_data = json.load(comps_file)
    listOfCompetitions = competitions_data.get("competitions", [])
    if not listOfCompetitions:
        raise ValueError("Competitions data is empty or invalid.")
    return listOfCompetitions

app = Flask(__name__)
app.secret_key = "something_special"  # Change for security in production

# Load initial data
competitions = loadCompetitions()
clubs = loadClubs()

# Home route
@app.route("/")
def index():
    return render_template("index.html")

# Summary route to display club details
@app.route("/showSummary", methods=["POST"])
def showSummary():
    global clubs
    global competitions

    email = request.form.get("email")

    if not email:
        flash("Email field is required.")
        return redirect(url_for("index"))

    club = next((club for club in clubs if club["email"] == email), None)

    if club:
        session["logged_in"] = True
        session["club"] = club["name"]
        return render_template("welcome.html", club=club, competitions=competitions)
    else:
        flash("Email not found. Please try again.")
        return redirect(url_for("index"))

# Booking route
@app.route("/book/<competition>/<club>")
def book(competition, club):
    if not session.get("logged_in"):
        flash("You must be logged in to book.")
        return redirect(url_for("index"))

    global clubs
    global competitions

    competition = competition.replace("_", " ")
    club = club.replace("_", " ")

    foundClub = [c for c in clubs if c["name"] == club]
    foundCompetition = [c for c in competitions if c["name"] == competition]

    if foundClub and foundCompetition:
        return render_template(
            "booking.html", club=foundClub[0], competition=foundCompetition[0]
        )
    else:
        flash("Club or competition not found.")
        return redirect(url_for("index"))

# Purchase places route
@app.route("/purchasePlaces", methods=["POST"])
def purchasePlaces():
    global clubs
    global competitions

    competition_name = request.form["competition"].replace("_", " ")
    club_name = request.form["club"]

    competition = next((c for c in competitions if c["name"] == competition_name), None)
    club = next((c for c in clubs if c["name"] == club_name), None)

    if not competition or not club:
        flash("Competition or club not found.")
        return redirect(url_for("index"))

    try:
        spots_requested = int(request.form["places"])
        if spots_requested <= 0:
            flash("Number of spots requested must be greater than zero")
            return render_template("welcome.html", club=club, competitions=competitions)
    except ValueError:
        flash("Invalid input for number of spots")
        return render_template("welcome.html", club=club, competitions=competitions)

    booking_result = book_spot(club, competition, spots_requested)

    if booking_result == "Booking successful":
        updateCompetitions(competitions)
        updateClubs(clubs)
        flash("Great-booking complete!")
    else:
        flash(booking_result)

    return render_template("welcome.html", club=club, competitions=competitions)

# Update the clubs JSON file
def updateClubs(clubs):
    if not app.testing:
        clubs_path = os.path.join(BASE_DIR, "clubs.json")
        with open(clubs_path, "w") as c:
            json.dump({"clubs": clubs}, c, indent=4)

# Update the competitions JSON file
def updateCompetitions(competitions):
    if not app.testing:
        competitions_path = os.path.join(BASE_DIR, "competitions.json")
        with open(competitions_path, "w") as comps_file:
            portalocker.lock(comps_file, portalocker.LOCK_EX)  # Exclusive lock for writing
            json.dump({"competitions": competitions}, comps_file, indent=4)

# Helper function to book spots
def book_spot(user, competition, spots_requested):
    try:
        spots_requested = int(spots_requested)
    except ValueError:
        return "Invalid input for spots requested"

    if spots_requested <= 0:
        return "Number of spots requested must be greater than zero"

    if spots_requested > 12:
        return "Cannot book more than 12 spots"

    try:
        available_places = int(competition["numberOfPlaces"])
    except (ValueError, KeyError):
        return "Invalid competition data"

    if available_places < spots_requested:
        return "Not enough available spots"

    if int(user["points"]) < spots_requested:
        return "Not enough points"

    # Deduct points and reduce available spots if all checks passed
    user["points"] = str(int(user["points"]) - spots_requested)
    competition["numberOfPlaces"] = str(available_places - spots_requested)

    return "Booking successful"

# Route to display club points
@app.route("/points")
def displayPoints():
    global clubs
    return render_template("points.html", clubs=clubs)

# Logout route
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
