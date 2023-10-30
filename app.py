# template: https://{{YOUR_DOMAIN}}/authorize?audience={{API_IDENTIFIER}}&response_type=token&client_id={{YOUR_CLIENT_ID}}&redirect_uri={{YOUR_CALLBACK_URI}}
# test URL: https://dev-xruf6cbo0o6usc80.eu.auth0.com/authorize?audience=https://127.0.0.1:5000/&response_type=token&client_id=4BAMLmkcfrShUDQ8VYiWWUj7DLOENF2w&redirect_uri=https://127.0.0.1:5000/



from os import environ as env
from dotenv import load_dotenv
load_dotenv()

import sys
import json
from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth
from flask import Flask, render_template, request, redirect, url_for, jsonify, abort, session
from flask_migrate import Migrate
from flask_cors import CORS
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from flask_sqlalchemy import SQLAlchemy

from model import db, create_tables, Movie, Actor, Cast
from model import queryCastByActor, queryMovieByActor

from auth import AuthError, requires_auth

#----------------------------------------------------------------------------#
# Auth0 test
#----------------------------------------------------------------------------#

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    app.secret_key = env.get("APP_SECRET_KEY")

    if test_config:
        app.config.from_object(test_config) 
        print("Testing Mode")
    else:
        app.config.from_object("config.ProductionConfig")
        print("Production Mode")

    print("applied db URL = ", app.config['SQLALCHEMY_DATABASE_URI'])
    
    CORS(app)
    db.init_app(app)
    migrate = Migrate(app, db)

    oauth = OAuth(app)
    oauth.register(
        "auth0",
        client_id=env.get("AUTH0_CLIENT_ID"),
        client_secret=env.get("AUTH0_CLIENT_SECRET"),
        client_kwargs={
            "scope": "openid profile email",
        },
        server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
    )

    @app.route("/login")
    def login():
        return oauth.auth0.authorize_redirect(
            redirect_uri=url_for("callback", _external=True, _scheme='https')
        )

    @app.route("/callback", methods=["GET", "POST"])
    def callback():
        token = oauth.auth0.authorize_access_token()
        session["user"] = token
        print(token)
        return redirect("/")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(
            "https://" + env.get("AUTH0_DOMAIN")
            + "/v2/logout?"
            + urlencode(
                {
                    "returnTo": url_for("index", _external=True, _scheme='https'),
                    "client_id": env.get("AUTH0_CLIENT_ID"),
                },
                quote_via=quote_plus,
            )
        )
        

    # Homepage
    @app.route('/')
    #@requires_auth('read:actors')
    def index():
        movies = Movie.query.all()
        actors = Actor.query.all()
        return render_template('index.html', movies=movies, actors=actors, session=session.get('user'), pretty=json.dumps(session.get('user'), indent=4))


    #----------------------------------------------------------------------------#
    # Movies
    #----------------------------------------------------------------------------#

    # Endpoint to add new movies
    @app.route('/movie/create', methods=['POST'])
    @requires_auth('post:movie')
    def create_movie(payload):
        body = {}
        try:
            data = request.get_json()
            print("Received JSON data:", data)
            mov_title = data.get('mov_title')
            mov_release = data.get('mov_release')
            mov_language = data.get('mov_language')

            print("Title = ", mov_title)
            print("Release = ", mov_release)
            print("Language = ", mov_language)

            if not mov_title or not mov_release:
                return jsonify({"error": "Mandatory value for either movie title or release year is missing."}), 400

            movie = Movie(mov_title=mov_title, mov_release=mov_release, mov_language=mov_language)
            db.session.add(movie)
            db.session.commit()

            body = {
                'mov_title': movie.mov_title,
                'mov_release': movie.mov_release,
                'mov_language': movie.mov_language
            }
            return jsonify({"success": True, "mov_title": movie.mov_title, "data": body}), 201

        except Exception as err_mov_crt:
            db.session.rollback()
            print(str(err_mov_crt))
            return jsonify({"error": "Invalid request data in Movies"}), 400

        finally:
            db.session.close()

    # Endpoint to delete movies
    @app.route('/movies/<int:mov_id>', methods=['DELETE'])
    @requires_auth('delete:movie')
    def delete_movie(payload, mov_id):
        try:
            movie = Movie.query.get(mov_id)

            if movie:
                # Delete associated cast entries
                Cast.query.filter_by(mov_id=mov_id).delete()

                # Now, delete the movie
                db.session.delete(movie)
                db.session.commit()
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Movie not found in database'}), 404
        except SQLAlchemyError as err_mov_del:
            db.session.rollback()
            print(str(err_mov_del))
            return jsonify({"success": False, "error": "Database error"}), 500
        finally:
            db.session.close()

    # Endpoint to rename movies
    @app.route('/update_movie_title/<int:mov_id>', methods=['POST'])
    @requires_auth('update:movie')
    def update_movie_title(payload,  mov_id):
        try:
            new_title = request.json.get('newTitle')

            # Fetch the movie record from the database using movie_id
            movie = Movie.query.get(mov_id)

            if movie:
                # Update the movie title
                movie.mov_title = new_title
                db.session.commit()
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": "Movie not found"})

        except SQLAlchemyError as err_mov_titl:
            db.session.rollback()
            print(str(err_mov_titl))
            return jsonify({"success": False, "error": "Database error"})

        finally:
            db.session.close()

    #----------------------------------------------------------------------------#
    # Actors
    #----------------------------------------------------------------------------#


    # Endpoint to add new actors
    @app.route('/actor/create', methods=['POST'])
    @requires_auth('post:actor')
    def create_actor(payload):
        body = {}
        try:
            data = request.get_json()
            act_firstname = data.get('act_firstname')
            act_lastname = data.get('act_lastname')
            act_language = data.get('act_language')
            act_gender = data.get('act_gender')

            if not act_firstname or not act_lastname:
                return jsonify({"error": "Invalid request data in Actors"}), 400

            actor = Actor(act_firstname=act_firstname, act_lastname=act_lastname, act_language=act_language, act_gender=act_gender)
            db.session.add(actor)
            db.session.commit()

            body = {
                'act_firstname': actor.act_firstname,
                'act_lastname': actor.act_lastname,
                'act_language': actor.act_language,
                'act_gender': actor.act_gender
            }
            return jsonify({"success": True, "act_firstname": actor.act_firstname, "data": body}), 201

        except Exception as err_act_crt:
            db.session.rollback()
            print(str(err_act_crt))
            return jsonify({"error": "Invalid request data in Actors"}), 400

        finally:
            db.session.close()

    # Endpoint to get actors
    @app.route('/actor', methods=['GET'])
    @requires_auth('read:actors')
    def show_actor(payload):
        actors = Actor.query.all()
        return render_template('portfolio.html', actors=actors, session=session.get('user'), pretty=json.dumps(session.get('user'), indent=4))

    @app.route('/actor/<int:act_id>/movies')
    def get_actor_portfolio(act_id):

        movies = queryMovieByActor(act_id)

        if movies is not None:
            return jsonify(success=True, cast_list=movies)
        else:
            return jsonify(success=False, message='Failed to retrieve movies')

    # Delete actor
    @app.route('/actor/<int:act_id>', methods=['DELETE'])
    @requires_auth('delete:actor')
    def delete_actor(payload, act_id):
        try:
            actor = Actor.query.get(act_id)

            if actor:
                db.session.delete(actor)
                db.session.commit()
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Actor not found'}), 404
        except SQLAlchemyError as err_act_del:
            db.session.rollback()
            print(str(err_act_del))
            return jsonify({"success": False, "error": "Database error"}), 500
        finally:
            db.session.close()

    #----------------------------------------------------------------------------#
    # Casts
    #----------------------------------------------------------------------------#

    # Endpoint to retrieve movie cast.
    '''
    Endpoint for website rendering. Not an API end-point
    '''
    @app.route('/cast', methods=['GET'])
    @requires_auth('read:cast')
    def show_cast(payload):

        movies = Movie.query.all()
        return render_template('cast.html', movies=movies, session=session.get('user'), pretty=json.dumps(session.get('user'), indent=4))

    # Endpoint to assign actors to movie casts.
    @app.route('/movie/<int:mov_id>/cast/add/<int:act_id>', methods=['POST'])
    @requires_auth('post:actor-cast')
    def add_actor_to_cast(mov_id, act_id, cas_role):
        try:
            #print(f"Received mov_id: {mov_id}, act_id: {act_id}, cas_role: {cas_role}")
            movie = Movie.query.get(mov_id)
            actor = Actor.query.get(act_id)
            role = Cast.query.get(cas_role)

            if movie and actor:
                # Check if the combination of movie_id and actor_id already exists
                existing_cast = Cast.query.filter_by(mov_id=mov_id, act_id=act_id).first()
                if existing_cast:
                    return jsonify({'success': False, 'error': "Actor is already in this movie's cast"}), 400

                cast = Cast(movie=movie, actor=actor, role=role)
                db.session.add(cast)
                db.session.commit()
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Movie or actor not found'}), 404
        except SQLAlchemyError as error_assing_act:
            db.session.rollback()
            print(str(error_assing_act))
            return jsonify({"success": False, "error": "Database error"}), 500
        finally:
            db.session.close()



    # Endpoint to retrieve movie cast in data dictionairy format.
    @app.route('/movie/<int:mov_id>/cast', methods=['GET'])
    @requires_auth('read:cast')
    def get_movie_cast(payload, mov_id):
        try:
            movie = Movie.query.get(mov_id)

            # Check if the movie exists
            if not movie:
                return jsonify({'success': False, 'error': 'Movie not found'}), 404

            cast_list = []

            for cast_entry in movie.casts:
                cast_dict = {
                    "act_id": cast_entry.actor.act_id,
                    "act_firstname": cast_entry.actor.act_firstname,
                    "act_lastname": cast_entry.actor.act_lastname,
                }

                if cast_entry.cas_role is not None:  # Access cas_role directly from cast_entry
                    cast_dict["cas_role"] = cast_entry.cas_role

                cast_list.append(cast_dict)

            return jsonify({'success': True, 'cast_list': cast_list})

        except SQLAlchemyError as err_mov_cast:
            # Handle database errors
            db.session.rollback()
            print(str(err_mov_cast))
            return jsonify({"success": False, "error": "Database error"}), 500

        except Exception as e:
            # Handle other exceptions
            print("An error occurred:", str(e))
            return jsonify({'success': False, 'error': str(e)})



        finally:
            db.session.close()

    # Endpoint to get cast/movie portofolio for actor
    @app.route('/actor/<int:act_id>/casts', methods=['GET'])
    @requires_auth('read:actor_portfolio')
    def get_actor_casts(payload, act_id):

        casts = queryCastByActor(act_id)

        if casts is not None:
            return jsonify(success=True, cast_list=casts)
        else:
            return jsonify(success=False, message='Failed to retrieve movies')

    # Endpoint to remove actor from a cast
    @app.route('/movie/<int:mov_id>/cast/delete/<int:act_id>', methods=['POST'])
    @requires_auth('delete:actor')
    def delete_actor_from_cast(payload, mov_id, act_id):
        try:
            movie = Movie.query.get(mov_id)
            actor = Actor.query.get(act_id)

            if movie and actor:
                # Check if the combination of movie_id and actor_id exists in the cast list
                cast_entry = Cast.query.filter_by(mov_id=mov_id, act_id=act_id).first()

                if cast_entry:
                    db.session.delete(cast_entry)
                    db.session.commit()
                    return jsonify({'success': True, 'message': 'Actor removed from the cast list'}), 200
                else:
                    return jsonify({'success': False, 'message': 'Actor not found in the cast list'}), 404
            else:
                return jsonify({'success': False, 'message': 'Movie or actor not found'}), 404
        except SQLAlchemyError as err_cas_act_del:
            db.session.rollback()
            print(str(err_cas_act_del))
            return jsonify({'success': False, 'message': 'Failed to delete actor from the cast list'}), 500
        finally:
            db.session.close()

    # Endpoint maintain which actor performed which role in a specific movie.
    @app.route('/cast/create', methods=['POST'])
    @requires_auth('post:cast')
    def create_cast(payload):
        print("Received data:", request.data)
        try:
            data = request.get_json()
            mov_id = data.get('mov_id')
            act_id = data.get('act_id')
            cas_role = data.get('cas_role')

            print("movie id  = ", mov_id)
            print("actor_id = ", act_id)
            print("cast id = ", cas_role)

            if not mov_id or not act_id or not cas_role:
                return jsonify({"error": "Please provide all required information."}), 400

            # Check if the combination already exists in the 'casts' table
            existing_cast = Cast.query.filter_by(mov_id=mov_id, act_id=act_id, cas_role=cas_role).first()

            if existing_cast:
                return jsonify({"error": "Duplicate entry. Cast already exists."}), 409

            cast = Cast(mov_id=mov_id, act_id=act_id, cas_role=cas_role)
            db.session.add(cast)
            db.session.commit()

            # Return the created cast data in the response
            response_body = {
                "success": True,
                "data": {
                    "mov_id": cast.mov_id,
                    "act_id": cast.act_id,
                    "cas_role": cast.cas_role,
                    # Add other relevant cast data fields here
                }
            }
            return jsonify(response_body), 201

        except IntegrityError as err_dt_integ:
            db.session.rollback()
            print(str(err_dt_integ))
            return jsonify({"error": "Failed to create cast due to database integrity error."}), 500
        
        except ValueError as value_err:
            db.session.rollback()
            print(str(value_err))
            return jsonify({"error": "Invalid input data."}), 400

        except Exception as err_cas_crt:
            db.session.rollback()
            print(str(err_cas_crt))
            return jsonify({"error": "Failed to create cast."}), 500

        finally:
            db.session.close()

    # Error handling for invalid requests
    @app.route('/NotValid', methods=['GET'])
    def not_valid():
        response = {
            "error": 404,
            "message": "resource not found",
            "success": False
        }
        return jsonify(response), 404
    
    # Error Handler for Authentication
    @app.errorhandler(AuthError)
    def unauthorized(e):
        return jsonify({
            "success": False,
            "error": e.status_code,
            "description": e.error["description"],
            "code": e.error["code"],
        }), e.status_code

    return app

app = create_app()

# Maintain port
if __name__ == '__main__':
    create_tables()  # Initialize the database tables
    app.run(host="0.0.0.0", port=3000)