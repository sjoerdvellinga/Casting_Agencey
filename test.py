import os
import unittest
import json
import subprocess

from os import environ as env
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
# Overwrite these environment variables for automated testing
os.environ["FLASK_APP"] = "app.py"
os.environ["FLASK_DEBUG"] = "true"


from authlib.integrations.requests_client import OAuth2Session
from app import create_app, db
from model import Movie, Actor, Cast

class CastingAgency_TestCase(unittest.TestCase):

    @staticmethod
    def start_flask_testing_mode(self):
        subprocess.Popen(["flask", "run", "--testing"])

    def setUp(self):
        self.app = create_app("config.TestingConfig")  # Use the testing configuration
        self.client = self.app.test_client

        with self.app.app_context():
            db.create_all()

        act_firstname = "Bryce Dallas"
        act_lastname = "Howard"
        act_language = "EN"
        act_gender = "Female"
        mov_title = "Jurassic World Dominion"
        mov_release = 2022
        mov_language = "EN"
        cas_role = "Claire Dearing"


        self.actor_data = {
            "act_firstname": act_firstname,
            "act_lastname": act_lastname,
            "act_language": act_language,
            "act_gender": act_gender
        }

        self.movie_data = {
            "mov_title": mov_title,
            "mov_release": mov_release,
            "mov_language": mov_language
        }

        self.cast_data = {
            "cas_role": cas_role
        }

        self.headers = {
        }

        # Create an OAuth2Session
        oauth = OAuth2Session(
            client_id = self.app.config["AUTH0_CLIENT_ID"],
            client_secret = self.app.config["AUTH0_CLIENT_SECRET"],
            token_endpoint=f'https://{self.app.config["AUTH0_DOMAIN"]}/oauth/token'
        )

        # Fetch an access token
        token = oauth.fetch_token(
            token_url=f'https://{self.app.config["AUTH0_DOMAIN"]}/oauth/token',
            audience = self.app.config["API_AUDIENCE"],
            grant_type = 'client_credentials',
            algorithm = self.app.config["ALGORITHMS"]
        )

        self.access_token = token['access_token']
#        print("tokne = ", self.access_token)

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()


    def test_create_actor(self):
        res = self.client().post('/actor/create', json=self.actor_data, headers={
            "Authorization": f"Bearer {self.access_token}"})
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 201)
        
        # Check if "success" key is in the response
        try:
            self.assertTrue(data["success"])
        except KeyError:
            self.fail("Response does not contain 'success' key")

        self.assertEqual(data.get("act_firstname"), self.actor_data["act_firstname"])

    def test_create_movie(self):
        res = self.client().post('/movie/create', json=self.movie_data, headers={
            "Authorization": f"Bearer {self.access_token}"})
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 201)
        try:
            self.assertTrue(data["success"])
        except KeyError:
            self.fail("Response does not contain 'success' key")
        self.assertEqual(data["mov_title"], self.movie_data["mov_title"])

    def test_create_cast(self):
        actor = Actor(**self.actor_data)
        movie = Movie(**self.movie_data)
        
        with self.app.app_context():
            db.session.add(actor)
            db.session.add(movie)
            db.session.commit()

            db.session.refresh(actor)
            db.session.refresh(movie)
        
        cas_role = self.cast_data["cas_role"]
        
        cast_data = {
            "act_id": actor.act_id,
            "mov_id": movie.mov_id,
            "cas_role": cas_role
        }

        print("actor = ", cast_data["act_id"])
        print("movie = ", cast_data["mov_id"])
        print("role = ", cast_data["cas_role"])

        res = self.client().post('/cast/create', json=cast_data, headers={
            "Authorization": f"Bearer {self.access_token}"})
        data = json.loads(res.data)

        # Print the entire data content
        print("Response data:", data)

        # You can also check specific values within 'data'
        act_id_from_response = data.get("data", {}).get("act_id")
        mov_id_from_response = data.get("data", {}).get("mov_id")
        cas_role_from_response = data.get("data", {}).get("cas_role")

        # Now you can print or assert these values if needed
        print("act_id from response:", act_id_from_response)
        print("mov_id from response:", mov_id_from_response)
        print("cas_role from response:", cas_role_from_response)



        self.assertEqual(res.status_code, 201)
        try:
            self.assertTrue(data["success"])
        except KeyError:
            self.fail("Response does not contain 'success' key")

    def test_get_actor_portfolio(self):
        actor = Actor(**self.actor_data)
        movie = Movie(**self.movie_data)

        with self.app.app_context():
            db.session.add(actor)
            db.session.add(movie)
            db.session.commit()

            db.session.refresh(actor)
            db.session.refresh(movie)

            cas_role = self.cast_data["cas_role"]

            cast_data = {
                "act_id": actor.act_id,
                "mov_id": movie.mov_id,
                "cas_role": cas_role
            }

            cast = Cast(**cast_data)
            db.session.add(cast)
            db.session.commit()

            # Fetch the actor within the same application context
            actor_to_fetch = Actor.query.get(actor.act_id)

        with self.app.app_context():
            res = self.client().get(f'/actor/{actor_to_fetch.act_id}/movies')
            data = json.loads(res.data)
            self.assertEqual(res.status_code, 200)
            try:
                self.assertTrue(data["success"])
            except KeyError:
                self.fail("Response does not contain 'success' key")
            self.assertTrue(data["cast_list"])
            self.assertEqual(data["cast_list"][0]["title"], self.movie_data["mov_title"])

    def test_delete_actor(self):
        with self.app.app_context():
            actor = Actor(**self.actor_data)
            db.session.add(actor)
            db.session.commit()

            actor_to_delete = Actor.query.get(actor.act_id)

            res = self.client().delete(f'/actor/{actor_to_delete.act_id}', headers={
                "Authorization": f"Bearer {self.access_token}"})
            data = json.loads(res.data)
            self.assertEqual(res.status_code, 200)
            try:
                self.assertTrue(data["success"])
            except KeyError:
                self.fail("Response does not contain 'success' key")

    def test_delete_movie(self):
        with self.app.app_context():
            movie = Movie(**self.movie_data)
            db.session.add(movie)
            db.session.commit()

            movie_to_delete = Movie.query.get(movie.mov_id)

            res = self.client().delete(f'/movie/{movie_to_delete.mov_id}', headers={
                "Authorization": f"Bearer {self.access_token}"})
            if res.status_code == 200:
                data = json.loads(res.data)
                try:
                    self.assertTrue(data["success"])
                except KeyError:
                    self.fail("Response does not contain 'success' key")
            else:
                # Handle cases where the response status code is not 200 (e.g., movie not found)
                expected_status_code = 404  # Replace with the appropriate status code
                self.assertEqual(res.status_code, expected_status_code)

if __name__ == "__main__":
    os.environ["FLASK_ENV"] = "testing"
    unittest.main()