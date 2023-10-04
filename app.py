import sys

from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import UniqueConstraint, CheckConstraint


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://vellinga@127.0.0.1:5432/agency_model'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.config['DEBUG'] = True

class Movie(db.Model):
    """
    Represents a movie in the database.

    """

    __tablename__ = 'movies'
    mov_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    mov_title = db.Column(db.String(), nullable=False)
    mov_year = db.Column(db.String (4), nullable=False)
    mov_language = db.Column(db.String(2), nullable=True)

    def __repr__(self):
        return f'<Movie {self.mov_id} {self.mov_title} {self.mov_year} {self.mov_language}>'

class Actor(db.Model):
    """
    Represents an actor in the database.

    """

    __tablename__= 'actors'
    act_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    act_firstname = db.Column(db.String(25), nullable=False)
    act_lastname = db.Column(db.String(25), nullable=False)
    act_language = db.Column(db.String(2), nullable=True)
    act_gender = db.Column(db.String(6), nullable=True)

    def __repr__(self):
        return f'<Actor {self.act_id} {self.act_firstname} {self.act_lastname} {self.act_language} {self.act_gender}>'

class Cast(db.Model):
    """
    Represents amovie cast in the database.
    The movie cast are the actor who performed in the movie.

    """

    __tablename__ = 'casts'
    cas_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    mov_id = db.Column(db.Integer, db.ForeignKey('movies.mov_id'), nullable=False)
    act_id = db.Column(db.Integer, db.ForeignKey('actors.act_id'), nullable=False)
    cas_role = db.Column(db.String(35), nullable=True)

    # Amake sure the relation is unique, to enable consistant deleting movies.
    __table_args__ = (UniqueConstraint('mov_id', 'act_id'),)

    movie = db.relationship('Movie', backref=db.backref('casts', lazy=True))
    actor = db.relationship('Actor', backref=db.backref('casts', lazy=True))

    def __repr__(self):
        return f'<Cast {self.cas_id} {self.mov_id} {self.act_id} {self.cas_role}>'



def create_tables():
    with app.app_context():
        db.create_all()

# Get all movies where selected actor perfomed in.
def get_movies_by_actor_id(act_id):
    try:
        actor = Actor.query.get(act_id)

        if actor:
            # Use actor.casts to get the list of movies they have acted in
            movies = [cast.movie.mov_title for cast in actor.casts]
            return movies
        else:
            return None  # Return None if actor not found
        
    except SQLAlchemyError as act_retrieve_error:
        print(str(act_retrieve_error))
        return None


# Endpoint to add new movies to the database
@app.route('/movie/create', methods=['POST'])
def create_movie():
    body = {}
    try:
        data = request.get_json()
        mov_title = data.get('mov_title')
        mov_year = data.get('mov_year')
        mov_language = data.get('mov_language')

        if not mov_title or not mov_year:
            return jsonify({"error": "Mandatory value for either movie title or release year is missing."}), 400

        movie = Movie(mov_title=mov_title, mov_year=mov_year, mov_language=mov_language)
        db.session.add(movie)
        db.session.commit()

        body = {
            'mov_title': movie.mov_title,
            'mov_year': movie.mov_year,
            'mov_language': movie.mov_language
        }
        return jsonify(body), 201  # 201 - Movie created status for successful creation

    except Exception as e:
        db.session.rollback()
        print(str(e))
        return jsonify({"error": "Invalid request data in Movies"}), 400

    finally:
        db.session.close()


@app.route('/actor/create', methods=['POST'])
def create_actor():
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
        return jsonify(body), 201  # 201 - Artis created status for successful creation

    except Exception as e:
        db.session.rollback()
        print(str(e))
        return jsonify({"error": "Invalid request data in Actors"}), 400

    finally:
        db.session.close()

# Delete movies
@app.route('/movies/<int:mov_id>', methods=['DELETE'])
def delete_movie(mov_id):
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
    except SQLAlchemyError as e:
        db.session.rollback()
        print(str(e))
        return jsonify({"success": False, "error": "Database error"}), 500
    finally:
        db.session.close()

# Rename movies
@app.route('/update_movie_title/<int:mov_id>', methods=['POST'])
def update_movie_title(mov_id):
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

    except SQLAlchemyError as e:
        db.session.rollback()
        print(str(e))
        return jsonify({"success": False, "error": "Database error"})

    finally:
        db.session.close()

# Delete actor
@app.route('/actor/<int:act_id>', methods=['DELETE'])
def delete_actor(act_id):
    try:
        actor = Actor.query.get(act_id)

        if actor:
            db.session.delete(actor)
            db.session.commit()
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Actor was not found in database'}), 404
    except SQLAlchemyError as e:
        db.session.rollback()
        print(str(e))
        return jsonify({"success": False, "error": "Database error"}), 500
    finally:
        db.session.close()

@app.route('/')
def index():
   movies = Movie.query.all()
   actors = Actor.query.all()
   return render_template('index.html', movies=movies, actors=actors)

# Route to assign actors to movie casts.
@app.route('/movie/<int:mov_id>/cast/add/<int:act_id>', methods=['POST'])
def add_actor_to_cast(mov_id, act_id):
    try:
        print(f"Received mov_id: {mov_id}, act_id: {act_id}")
        movie = Movie.query.get(mov_id)
        actor = Actor.query.get(act_id)

        if movie and actor:
            # Check if the combination of movie_id and actor_id already exists
            existing_cast = Cast.query.filter_by(mov_id=mov_id, act_id=act_id).first()
            if existing_cast:
                return jsonify({'success': False, 'error': 'Actor is already in the cast'}), 400

            cast = Cast(movie=movie, actor=actor)
            db.session.add(cast)
            db.session.commit()
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Movie or actor not found'}), 404
    except SQLAlchemyError as e:
        db.session.rollback()
        print(str(e))
        return jsonify({"success": False, "error": "Database error"}), 500
    finally:
        db.session.close()

@app.route('/cast')
def show_cast():
    movies = Movie.query.all()
    return render_template('cast.html', movies=movies)


@app.route('/movie/<int:mov_id>/cast')
def get_movie_cast(mov_id):
    try:
        movie = Movie.query.get(mov_id)
        if movie:
            cast_list = []
            for cast_entry in movie.casts:
                cast_dict = {
                    "act_id": cast_entry.actor.act_id,
                    "act_firstname": cast_entry.actor.act_firstname,
                    "act_lastname": cast_entry.actor.act_lastname
                }
                cast_list.append(cast_dict)        
            return jsonify({'success': True, 'cast_list': cast_list})
        else:
            return jsonify({'success': False, 'error': 'Movie not found'}), 404
    except SQLAlchemyError as e:
        db.session.rollback()
        print(str(e))
        return jsonify({"success": False, "error": "Database error"}), 500
    finally:
        db.session.close()

@app.route('/actor')
def show_actor():
    actors = Actor.query.all()
    return render_template('portfolio.html', actors=actors)

@app.route('/actor/<int:act_id>/movies')
def get_actor_portfolio(act_id):

    movies = get_movies_by_actor_id(act_id)

    if movies is not None:
        return jsonify(success=True, cast_list=movies)
    else:
        return jsonify(success=False, message='Failed to retrieve movies')

@app.route('/movie/<int:mov_id>/cast/delete/<int:act_id>', methods=['POST'])
def delete_actor_from_cast(mov_id, act_id):
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
    except SQLAlchemyError as e:
        db.session.rollback()
        print(str(e))
        return jsonify({'success': False, 'message': 'Failed to delete actor from the cast list'}), 500
    finally:
        db.session.close()

#always include this at the bottom of your code
if __name__ == '__main__':
   create_tables()  # Initialize the database tables
   app.run(host="0.0.0.0", port=3000)