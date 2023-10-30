from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import UniqueConstraint, CheckConstraint

db = SQLAlchemy()

class Movie(db.Model):
    """
    Represents a movie in the database.

    """

    __tablename__ = 'movies'
    mov_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    mov_title = db.Column(db.String(30), nullable=False)
    mov_release = db.Column(db.Integer, CheckConstraint('mov_release >= 1920 AND mov_release <= 2030'), nullable=True)
    mov_language = db.Column(db.String(2), nullable=True)

    __table_args__ = (UniqueConstraint('mov_id', 'mov_title', 'mov_release'),)
    
    def __repr__(self):
        return f'<Movie {self.mov_id} {self.mov_title} {self.mov_release} {self.mov_language}>'

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
    __table_args__ = (UniqueConstraint('mov_id', 'act_id', 'cas_role'),)

    movie = db.relationship('Movie', backref=db.backref('casts', lazy=True))
    actor = db.relationship('Actor', backref=db.backref('casts', lazy=True))

    def __repr__(self):
        return f'<Cast {self.cas_id} {self.mov_id} {self.act_id} {self.cas_role}>'

def create_tables():
    with db.app.app.context():
        db.create_all()

# Get all movie casts where selected actor was part of.
def queryCastByActor(act_id):
    try:
        actor = Actor.query.get(act_id)

        if actor:
            # Use actor.casts to get the list of movies they have acted in
            casts = [
                {"title": cast.movie.mov_title, "role": cast.cas_role}
                for cast in actor.casts
            ]
            return casts
        else:
            return None  # Return None if actor not found

    except SQLAlchemyError as act_retrieve_error:
        print(str(act_retrieve_error))
        return None


# Get all movies where selected actor performed in.
def queryMovieByActor(act_id):
    try:
        actor = Actor.query.get(act_id)

        if actor:
            # Use actor.casts to get the list of movies they have acted in
            movies = [
                {"title": cast.movie.mov_title, "role": cast.cas_role}
                for cast in actor.casts
            ]
            return movies
        else:
            return None  # Return None if actor not found

    except SQLAlchemyError as act_retrieve_error:
        print(str(act_retrieve_error))
        return None