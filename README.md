# Casting_Agencey
Final project for Udacity FSND

Flask application to adminstrate for The Casting Agency, which movies produced, which actors working with as well as which actors perofrmed in movie an which role they performed.

## Table of Contents

- [Getting Started](#getting_Started)
  - [Installing Dependencies](#Installing_Dependencies)
  - [PIP_Dependencies](#PIP_Dependencies)
  - [Key_Dependencies](#Key_Dependencies)
  - [Running_the_server](#Running_the_server)
- [Endpoints](#endpoints)
- [Error_Handling](#Error_Handling)
- [Authentication](#authentication)

## Getting_Started
### Installing_Dependencies
Python 3.7
Follow instructions to install the latest version of python for your platform in the python docs

### PIP_Dependencies
Once you have your virtual environment setup and running, install dependencies by naviging to the /backend directory and running:
pip install -r requirements.txt
This will install all of the required packages we selected within the requirements.txt file.

### Key_Dependencies
Flask 
is a lightweight backend microservices framework. Flask is required to handle requests and responses.

SQLAlchemy and Flask-SQLAlchemy 
are libraries to handle the lightweight sqlite database. Since we want you to focus on auth, we handle the heavy lift for you in ./src/database/models.py. We recommend skimming this code first so you know how to interface with the Drink model.

jose 
JavaScript Object Signing and Encryption for JWTs. Useful for encoding, decoding, and verifying JWTS.

### Running_the_server
Each time you open a new terminal session, run:
$ export FLASK_APP=api.py;

To run the server, execute:
$flask run --reload
- The --reload flag will detect file changes and restart the server automatically.

## Endpoints

### /movie/create (method:POST)

Add a new movie to the database

Example $ curl http://127.0.0.1:500/movie/create

"Content-Type: application/json" 
Body:
    {
        "mov_title": {{mov_title}},
        "mov_release": {{mov_release}},
        "mov_language": {{mov_language}}
    }

RESPONSE:
{
    "data": {
        "mov_language": "{{mov_language}}",
        "mov_release": "{{mov_release}}",
        "mov_title": "{{mov_title}}"
    },
    "mov_title": "{{mov_title}}",
    "success": true
}


### /actor/create (method: POST)

Add a new actor to the database

Example $ curl http://127.0.0.1:500/actor/create

"Content-Type: application/json" 
Body:
    {
        "act_firstname": "{{act_firstname}}",
        "act_lastname": "{{act_lastname}}",
        "act_language": "{{act_language}}",
        "act_gender": "{{act_gender}}"
    }

RESPONSE:
{
    "act_firstname": "{{act_firstname}}",
    "data": {
        "act_firstname": "{{act_firstname}}",
        "act_lastname": "{{act_lastname}}",
        "act_language": "{{act_language}}",
        "act_gender": "{{act_gender}}"
    },
    "success": true
}

### /update_movie_title/{{mov_id}} (method:POST)

Update the tile of a movie

"Content-Type: application/json" 
Body:
    {
        "newTitle": "{{new_title}}"
    }

RESPONSE:
{
    "success": true
}

### /cast/create (method:POST)

Maintain the cast for a movie.
Note: 1 actor can play multiple roles in one movie.
(In Coming to America, Eddy Murphy played Prince Akeem + Clarence + Saul + Randy Watoson)

"Content-Type: application/json" 
Body:
    {
        "mov_id": {{mov_id}},
        "act_id": {{act_id}},
        "cas_role": {{cas_role}}
    }

RESPONSE:
{
    "data": {
        "mov_id": {{mov_id}},
        "act_id": {{act_id}},
        "cas_role": {{cas_role}}
    },
    "success": true
}

### movie/{{mov_id}}/cast (method:GET)

Retrieve the complete cast of a movie

RESPONSE:
{
    "cast_list": [
        {
            "act_firstname": {{act_firstname}},
            "act_id": {{act_id}},
            "act_lastname": {{act_lastname}},
            "cas_role": "cas_role"
        },
        {
            "act_firstname": {{act_firstname}},
            "act_id": {{act_id}},
            "act_lastname": {{act_lastname}},
            "cas_role": "cas_role"
        }
    ],
    "success": true
}

### /actor/{{act_id}}/casts (method:GET)

Retrieve movies and roles for a specific actor



RESPONSE:
{
    "cast_list": [
        {
            "role": "Character 1",
            "title": "Postman 04a"
        }
    ],
    "success": true
}

### /movie/{{mov_id}}/cast/delete/{{act_id}} (method:)

Remove an actor from a movie cast

RESPONSE:
    {
        "message": "Actor removed from the cast list",
        "success": true
    }

### /actor/{{act_id}} (method: DELETE)

Delete an actor from the database

RESPONSE:
    {
        "success": true
    }

### /movies/{{mov_id}} (method:)

Add a new movie to the database

RESPONSE:
    {
        "success": true
    }


## Error_Handling

Errors are returned as JSON objects:

Example:
$ curl http://127.0.0.1:5000/NotValid

{ "error": 404,
"message": "resource not found",
"success": false
}

Other returned error codes:

400: Invalid input data
    -> Actor already in this movie's cast
    -> Invalid request data in actor
    -> Invalid request data in movie
404: Resource not found
    -> Movie not found
    -> Actor not found
    -> Movie or actor not found
    -> Cast not found
405: Method not allowed
409: Duplicate entry. Cast already exists.
422: Unprocessable
500: Failed to create cast
    -> Database error
    -> Failed to delete actor from the cast list
    -> Failed to create cast due to database integrity error
    -> Failed to create cast

## Authentication
User need to register in Auth0. An admin will assign the relevant role to the user in Auth0.

Logon link: <<to be maintained after deploying app on Heroku>>

Roles: 
1. Executive Producer
  "permissions": [
        "delete:actor",
        "delete:movie",
        "post:actor",
        "post:actor-cast",
        "post:cast",
        "post:movie",
        "read:actor_portfolio",
        "read:actors",
        "read:cast",
        "read:movies",
        "update:movie"
    ]
2. Casting Director
"permissions": [
        "post:actor-cast",
        "post:cast",
        "read:actor_portfolio",
        "read:actors",
        "read:cast",
        "read:movies",
        "update:movie"
    ]
3. Casting Assistent
    "permissions": [
        "read:actors",
        "read:cast",
    ]

For Testing via website, 3 test users are provided:
1. Executive@tacture.com (Uda^Executive)
2. Director@tacture.com (Uda^Director)
3. Assistent@tacture.com (Uda^Assistent)