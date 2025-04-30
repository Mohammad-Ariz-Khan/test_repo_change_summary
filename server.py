from flask import Flask, jsonify, request
import pyodbc
from flask_cors import CORS
import bcrypt
from werkzeug.security import generate_password_hash, check_password_hash

from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager

from datetime import datetime

from flask_cors import cross_origin
# Initialize Flask app
app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = "hello"  # Change this!
jwt = JWTManager(app)

# Enable CORS for all routes
# CORS(app)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})

# SQL Server connection parameters
server = 'localhost' 
database = 'BhavnaMovieBonanza' 
username = 'mak'    
password = '123'  
driver = '{ODBC Driver 17 for SQL Server}'

# Establish a connection to the SQL Server database
def get_db_connection():
    conn = pyodbc.connect(f'DRIVER={driver};'
                          f'SERVER={server};'
                          f'DATABASE={database};'
                          f'UID={username};'
                          f'PWD={password}')
    return conn
my_global_set = set()
# Fetch data from Admin table
# @app.route("/admin", methods=['GET'])
# def get_admin_data():
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()

#         # Query to get admin data
#         cursor.execute('SELECT username, password FROM admin')

#         # Fetch all rows
#         admins = []
#         for row in cursor.fetchall():
#             admin = {
#                 'username': row.username,
#                 'password': row.password  # Ensure passwords are hashed in real scenarios
#             }
#             admins.append(admin)

#         conn.close()
#         return jsonify({'admins': admins})

#     except Exception as e:
#         return jsonify({'message': f'Error: {str(e)}'}), 500

# # Fetch data from Users table
# @app.route("/users", methods=['GET'])
# def get_users_data():
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()

#         # Query to get users data
#         cursor.execute('SELECT UserName, Password FROM UserTable')

#         # Fetch all rows
#         users = []
#         for row in cursor.fetchall():
#             user = {
#                 'UserName': row.username,
#                 'Password': row.password  # Again, ensure passwords are hashed
#             }
#             users.append(user)

#         conn.close()
#         return jsonify({'users': users})

#     except Exception as e:
#         return jsonify({'message': f'Error: {str(e)}'}), 500


@app.route("/login", methods=['POST'])
def login():
    data = request.json  # Expecting a JSON payload with 'username' and 'password'
    username = data.get('username')
    password = data.get('password')

    try:
        # Establish database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check the Users table for the username
        cursor.execute('SELECT UserId, UserName, Password FROM UserTable WHERE UserName=?', (username,))
        user = cursor.fetchone()
        global rolevar
        if user:
            # Compare the hashed password
            if check_password_hash(user[2], password):  # user[2] contains the password
                # Fetch the RoleIden from RoleMatch based on UserIden
                cursor.execute('SELECT RoleIden FROM RoleMatch WHERE UserIden=?', (user[0],))
                role_match = cursor.fetchone()

                if role_match:
                    # Fetch the role name from the Roles table based on RoleIden
                    cursor.execute('SELECT RoleID, RolesName FROM Roles WHERE RoleId = ?', (role_match[0],))
                    role = cursor.fetchone()

                    if role and (role[0] == 1 or role[0] == 2):  # Check if the RoleId is 1 or 2
                        access_token = create_access_token(identity=str(user[0]))  # Create JWT token for the user
                        conn.close()
                        rolevar = role[1]
                        # return jsonify({'message': 'User authenticated', 'role': role[1], 'access_token': access_token}), 200
                        return jsonify({'message': 'User authenticated', 'role': role[1], 'access_token': access_token, 'user_id': user[0]}), 200

                    else:
                        conn.close()
                        return jsonify({'message': 'User does not have a valid role'}), 403
                else:
                    conn.close()
                    return jsonify({'message': 'Role not found for user'}), 404
            else:
                conn.close()
                return jsonify({'message': 'Invalid username or password'}), 401
        else:
            conn.close()
            return jsonify({'message': 'Invalid username or password'}), 401
        

    except Exception as e:
        conn.close()
        return jsonify({'message': f'Error: {str(e)}'}), 500




@app.route("/allmovies", methods=['GET'])
@jwt_required()
def get_all_movies():
    try:
        current_user_id = get_jwt_identity()  # Get the user_id from the JWT token
        conn = get_db_connection()
        cursor = conn.cursor()

        global rolevar
        # Check the user's role, assuming you have a field in JWT or user info to identify if the user is an admin
        # Here, for simplicity, we are assuming you can determine the role of the user based on their user_id
        cursor.execute('SELECT UserId FROM UserTable WHERE UserId = ?', (current_user_id,))
        user_role = cursor.fetchone()

        if not user_role:
            conn.close()
            return jsonify({'message': 'User not found'}), 404

        # If the user is an admin, return all movies
        if rolevar == 'Admin':
            cursor.execute('SELECT MovieId, Title, Description, Genre, ReleaseDate FROM MoviesList')
            movies = []
            for row in cursor.fetchall():
                movie_id = row[0]
                title = row[1]
                description = row[2]
                genre = row[3]
                release_date = row[4]  # This is the line to check for datetime

                # Check if release_date is a datetime object
                if isinstance(release_date, datetime):
                    release_date = release_date.strftime('%Y-%m-%d')  # Format as YYYY-MM-DD

                movie = {
                    'MovieId': movie_id,
                    'Title': title,
                    'Description': description,
                    'Genre': genre,
                    'ReleaseDate': release_date  # Now correctly formatted
                }
                movies.append(movie)
            conn.close()
            return jsonify({'allmovies': movies})

        # If the user is a regular user, return their personal movie list
        cursor.execute('''
            SELECT m.MovieId, m.Title, m.Description, m.Genre, m.ReleaseDate, p.Status, p.Rating
            FROM PersonalMoviesList p
            JOIN MoviesList m ON p.MovieId = m.MovieId
            WHERE p.UserId = ?
        ''', (current_user_id,))

        personal_movies = []
        global my_global_set
        for row in cursor.fetchall():
            release_date = row[4]
            if isinstance(release_date, datetime):
                release_date = release_date.strftime('%Y-%m-%d')
            my_global_set.add(row[1])    
            personal_movie = {
                'MovieId': row[0],
                'Title': row[1],
                'Description': row[2],
                'Genre': row[3],
                'ReleaseDate': release_date,
                'Status': row[5],
                'Rating': row[6]
            }
            personal_movies.append(personal_movie)
        conn.close()

        if personal_movies:
            return jsonify({'personal_movies': personal_movies}), 200
        else:
            return jsonify({'message': 'No personal movies found for this user'}), 404

    except Exception as e:
        conn.close()
        return jsonify({'message': f'Error: {str(e)}'}), 500

    
    
@app.route("/allmoviestoaddbyuser", methods=['GET'])
@jwt_required()
def get_all_movies_user_add():
    try:
        current_user_id = get_jwt_identity()  # Get the user_id from the JWT token
        conn = get_db_connection()
        cursor = conn.cursor()

        global rolevar
        # Check the user's role, assuming you have a field in JWT or user info to identify if the user is an admin
        cursor.execute('SELECT UserId FROM UserTable WHERE UserId = ?', (current_user_id,))
        user_role = cursor.fetchone()

        global my_global_set
        if not user_role:
            conn.close()
            return jsonify({'message': 'User not found'}), 404

        # SQL query to fetch movies with average rating
        query = '''
            SELECT m.MovieId, m.Title, m.Description, m.Genre, m.ReleaseDate, 
                   COALESCE(ar.AverageRating, 0) AS AverageRating
            FROM MoviesList m
            LEFT JOIN MovieAverageRatings ar ON m.MovieId = ar.MovieId
        '''
        cursor.execute(query)
        movies = cursor.fetchall()

        # If no movies found, return an empty list
        if not movies:
            return jsonify({'movies': []}), 200

        # Filter out movies where the title is in the global set
        filtered_movies = [
            movie for movie in movies if movie[1] not in my_global_set
        ]

        # If after filtering there are no movies left, return an empty list
        if not filtered_movies:
            return jsonify({'movies': []}), 200

        # Create the movie list only with filtered movies
        movie_list = [{
            "MovieId": movie[0],
            "Title": movie[1],
            "Description": movie[2],
            "Genre": movie[3],
            "ReleaseDate": movie[4],
            "AverageRating": movie[5]
        } for movie in filtered_movies]

        # Return the filtered list of movies
        return jsonify({'movies': movie_list}), 200

    except Exception as e:
        conn.close()
        return jsonify({'message': f'Error: {str(e)}'}), 500
    finally:
        conn.close()
        my_global_set.clear()




@app.route("/addmov", methods=['POST'])
@jwt_required()
def add_movie_to_personal_list():
    try:
        current_user_id = get_jwt_identity()  # Get the user_id from the JWT token
        data = request.json
        movie_id = data[0].get('MovieID')  # Get the MovieId from the request body

        # Ensure that the MovieId is provided
        if not movie_id:
            return jsonify({'message': 'MovieId is required'}), 400

        # Establish a connection to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if the movie already exists in the user's personal list
        cursor.execute('''SELECT * FROM PersonalMoviesList WHERE UserId = ? AND MovieId = ?''', 
                       (current_user_id, movie_id))
        existing_entry = cursor.fetchone()

        if existing_entry:
            conn.close()
            return jsonify({'message': 'Movie already in personal list'}), 400

        # Insert the movie into the user's personal movie list
        cursor.execute('''INSERT INTO PersonalMoviesList (UserId, MovieId, Status, Rating) 
                          VALUES (?, ?, ?, ?)''', 
                       (current_user_id, movie_id, 'Change', 0))
        conn.commit()  # Commit the transaction

        # Recalculate the average rating for the MovieId
        cursor.execute('''
            SELECT AVG(Rating) 
            FROM PersonalMoviesList 
            WHERE MovieId = ?
        ''', (movie_id,))
        avg_rating = cursor.fetchone()[0]

        # If no ratings remain, set the average to 0
        if avg_rating is None:
            avg_rating = 0

        # Check if the movie exists in the MovieAverageRatings table
        cursor.execute('''SELECT * FROM MovieAverageRatings WHERE MovieId = ?''', (movie_id,))
        movie_avg_entry = cursor.fetchone()

        # If movie exists in MovieAverageRatings table, update it
        if movie_avg_entry:
            cursor.execute('''
                UPDATE MovieAverageRatings 
                SET AverageRating = ? 
                WHERE MovieId = ?
            ''', (avg_rating, movie_id))
        else:
            # If movie doesn't exist, insert the new entry
            cursor.execute('''
                INSERT INTO MovieAverageRatings (MovieId, AverageRating) 
                VALUES (?, ?)
            ''', (movie_id, avg_rating))

        conn.commit()  # Commit the transaction
        conn.close()

        return jsonify({'message': 'Movie added to personal list successfully and average rating updated'}), 201

    except Exception as e:
        conn.close()
        return jsonify({'message': f'Error: {str(e)}'}), 500





@app.route("/movies", methods=['POST'])
def add_movie():
    try:
        data = request.json  # Get data from the request body
        
        title = data.get('title')
        description = data.get('description')
        genre = data.get('genre')  # Get the genre
        releaseDate = data.get('releaseDate')  # Get the release date

        # Ensure that all required fields are present
        if not title or not description or not genre or not releaseDate:
            return jsonify({'message': 'All fields (title, description, genre, release date) are required'}), 400

        # Establish a connection to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert the new movie into the MoviesList table
        cursor.execute(''' 
            INSERT INTO MoviesList (Title, Description, Genre, ReleaseDate) 
            VALUES (?, ?, ?, ?)
        ''', (title, description, genre, releaseDate))  # Only passing the 4 required fields

        conn.commit()  # Commit the transaction
        conn.close()
        print("201")
        return jsonify({'message': 'Movie added successfully'}), 201

    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500



@app.route("/movies/with_avg_rating", methods=["GET"])
@jwt_required()
def get_movies_with_avg_rating():
    try:
        # Get the user ID from the JWT token
        current_user_id = get_jwt_identity()

        # Database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # SQL query to fetch movies with average rating
        query = '''
            SELECT m.MovieId, m.Title, m.Description, m.Genre, m.ReleaseDate, 
                   COALESCE(ar.AverageRating, 0) AS AverageRating
            FROM MoviesList m
            LEFT JOIN MovieAverageRatings ar ON m.MovieId = ar.MovieId
        '''
        cursor.execute(query)
        movies = cursor.fetchall()

        # If no movies found, return an empty list
        if not movies:
            return jsonify({'movies': []}), 200

        # Format the result to JSON-friendly format
        movie_list = [{
            "MovieId": movie[0],
            "Title": movie[1],
            "Description": movie[2],
            "Genre": movie[3],
            "ReleaseDate": movie[4],
            "AverageRating": movie[5]
        } for movie in movies]

        return jsonify({'movies': movie_list}), 200

    except Exception as e:
        # Log the exception for debugging purposes
        print(f"Error: {str(e)}")
        return jsonify({'message': f'Error: {str(e)}'}), 500



@app.route("/movies/update/<int:id>", methods=['PUT'])
@jwt_required()
def update_movie(id):
    try:
        # Get the user ID from the JWT token
        current_user_id = get_jwt_identity()

        # Get updated data from the request body
        data = request.json
        status = data.get('status')  # Updated Status
        rating = data.get('rating')  # Updated Rating

        # Ensure that all required fields are present
        if status is None or rating is None:
            return jsonify({'message': 'Status and Rating are required'}), 400

        # Establish a connection to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the movie exists in the PersonalMoviesList for the current user
        cursor.execute('''SELECT * FROM PersonalMoviesList WHERE UserId = ? AND MovieId = ?''', 
                       (current_user_id, id))
        existing_entry = cursor.fetchone()

        if not existing_entry:
            conn.close()
            return jsonify({'message': 'Movie not found in personal list'}), 404

        # Update the Status and Rating in PersonalMoviesList
        cursor.execute('''UPDATE PersonalMoviesList
                          SET Status = ?, Rating = ?
                          WHERE UserId = ? AND MovieId = ?''', 
                       (status, rating, current_user_id, id))
        conn.commit()  # Commit the transaction

        # Recalculate the average rating for the MovieId
        cursor.execute('''
            SELECT AVG(Rating) 
            FROM PersonalMoviesList 
            WHERE MovieId = ?
        ''', (id,))
        avg_rating = cursor.fetchone()[0]

        # If no ratings remain, set the average to 0
        if avg_rating is None:
            avg_rating = 0

        # Check if the movie exists in the MovieAverageRatings table
        cursor.execute('''SELECT * FROM MovieAverageRatings WHERE MovieId = ?''', (id,))
        movie_avg_entry = cursor.fetchone()

        # If movie exists in MovieAverageRatings table, update it
        if movie_avg_entry:
            cursor.execute('''
                UPDATE MovieAverageRatings 
                SET AverageRating = ? 
                WHERE MovieId = ?
            ''', (avg_rating, id))
        else:
            # If movie doesn't exist, insert the new entry
            cursor.execute('''
                INSERT INTO MovieAverageRatings (MovieId, AverageRating) 
                VALUES (?, ?)
            ''', (id, avg_rating))

        conn.commit()  # Commit the transaction
        conn.close()

        return jsonify({'message': 'Movie updated successfully and average rating updated'}), 200

    except Exception as e:
        conn.close()
        return jsonify({'message': f'Error: {str(e)}'}), 500




@app.route("/movies/delete/<int:id>", methods=['DELETE'])
@jwt_required()
def delete_movie(id):
    conn = None
    try:
        current_user_id = get_jwt_identity()  # Get the user_id from the JWT token

        # Establish a connection to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Delete the movie from the PersonalMoviesList
        cursor.execute('DELETE FROM PersonalMoviesList WHERE UserId = ? AND MovieId = ?', 
                       (current_user_id, id))
        conn.commit()  # Commit the transaction

        # Recalculate the average rating for the MovieId
        cursor.execute('''SELECT AVG(Rating) FROM PersonalMoviesList WHERE MovieId = ?''', (id,))
        avg_rating = cursor.fetchone()[0]

        # If no ratings remain, set the average to 0
        if avg_rating is None:
            avg_rating = 0

        # Check if the movie exists in the MovieAverageRatings table
        cursor.execute('''SELECT * FROM MovieAverageRatings WHERE MovieId = ?''', (id,))
        movie_avg_entry = cursor.fetchone()

        # If movie exists in MovieAverageRatings table, update it
        if movie_avg_entry:
            # If the new average rating is 0, delete the row from MovieAverageRatings
            if avg_rating == 0:
                cursor.execute('''DELETE FROM MovieAverageRatings WHERE MovieId = ?''', (id,))
                conn.commit()
                return jsonify({'message': 'Movie deleted from personal list and row removed from MovieAverageRatings (average rating is 0)'}), 200
            else:
                cursor.execute('''UPDATE MovieAverageRatings SET AverageRating = ? WHERE MovieId = ?''', (avg_rating, id))
                conn.commit()
                return jsonify({'message': 'Movie deleted from personal list and average rating updated'}), 200
        else:
            # If movie doesn't exist in MovieAverageRatings table, insert the new entry
            cursor.execute('''INSERT INTO MovieAverageRatings (MovieId, AverageRating) VALUES (?, ?)''', (id, avg_rating))
            conn.commit()
            return jsonify({'message': 'Movie deleted from personal list and average rating inserted'}), 200

    except Exception as e:
        # Catch any errors and return the message
        if conn:
            conn.rollback()  # Rollback if an error occurs
        return jsonify({'message': f'Error: {str(e)}'}), 500

    finally:
        # Ensure that the database connection is always closed
        if conn:
            conn.close()




# Route for signing up a new user (with hashed password)
@app.route("/signup", methods=['POST'])
def signup():
    try:
        data = request.json  # Expecting a JSON payload with 'username' and 'password'
        username = data.get('username')
        password = data.get('password')

        # Hash the password before storing it
        # hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())\
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user already exists in the Users table
        cursor.execute('SELECT * FROM UserTable WHERE username=?', (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            return jsonify({'message': 'Username already taken'}), 400

        # Insert the new user into the Users table
        cursor.execute('INSERT INTO UserTable (UserName, Password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()

        conn.close()
        return jsonify({'message': 'User signed up successfully'}), 201

    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

if __name__ == "__main__":
    app.run(debug=True)
