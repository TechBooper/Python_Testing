from locust import HttpUser, TaskSet, task, between

# Data for testing
club_email = "john@simplylift.co"
competition_name = "Spring_Festival"
club_name = "Simply_Lift"


class UserBehavior(TaskSet):
    """
    Defines a set of user behaviors for testing various actions on the website,
    such as viewing pages, logging in, and booking places.
    """

    @task(1)
    def view_index(self):
        """
        Simulate viewing the home page (index).

        This task sends a GET request to the root URL ('/').
        """
        self.client.get("/")

    @task(2)
    def login(self):
        """
        Simulate logging in as a club secretary.

        This task sends a POST request to the '/showSummary' route with the club's email data.
        """
        self.client.post("/showSummary", data={"email": club_email})

    @task(3)
    def view_competition(self):
        """
        Simulate viewing the competition booking page after login.

        This task sends a GET request to the booking page for a specific competition and club.
        """
        self.client.get(f"/book/{competition_name}/{club_name}")

    @task(4)
    def book_places(self):
        """
        Simulate booking places for a competition.

        This task sends a POST request to the '/purchasePlaces' route,
        where the club attempts to book 2 places for a given competition.
        """
        self.client.post(
            "/purchasePlaces",
            data={"competition": competition_name, "club": club_name, "places": "2"},
        )

    @task(5)
    def view_points_leaderboard(self):
        """
        Simulate viewing the public points leaderboard.

        This task sends a GET request to the '/points' route to display the leaderboard.
        """
        self.client.get("/points")


class WebsiteUser(HttpUser):
    """
    Represents a simulated user of the website for load testing.

    Each user runs tasks defined in the 'UserBehavior' class and waits between 1 to 5 seconds between tasks.
    """

    tasks = [UserBehavior]
    wait_time = between(
        1, 5
    )  # Simulate users waiting between 1 to 5 seconds between tasks
