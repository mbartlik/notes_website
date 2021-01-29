import os
from os import path
import pymysql
import jwt
import datetime


ROOT = path.dirname(path.relpath(__file__)) # gets the location on computer of this directory

# info about signing into the google cloud sql database
db_user = 'root'
db_password = '1234'
db_name = 'master'
db_connection_name = 'maxs-note-keeper:us-east4:user-data'

jwt_key = "WIRPMNVPWO" # used for encoding and decoding json web token for authentication


# Given a username and password this function generates a json web token
# The token will be used for authentication throughout the application
def get_token(user_id):
	# get current time and add 6 hours to represent the time when the user's login expires
	current_time = datetime.datetime.now()
	time_to_expiration = datetime.timedelta(hours = 8)
	expiration_time = current_time + time_to_expiration
	expiration_string = expiration_time.strftime("%m/%d/%Y, %H:%M:%S") # convert to string to use in payload

	# generate payload which will be encoded into the jwt
	payload = {
		"user_id": user_id,
		"expiration_time": expiration_string
	}

	encoded = jwt.encode(payload, jwt_key, algorithm="HS256") # get jwt

	return encoded

# Given a token this method authenticates the user
def authenticate_token(token):
	decoded = jwt.decode(token, jwt_key, algorithms="HS256") # decode using the same key and algorithm to encode

	expiration = datetime.datetime.strptime(decoded["expiration_time"], '%m/%d/%Y, %H:%M:%S') # convert expiration to datetime

	# compare expiration to current time, if it is too late then logout
	if expiration < datetime.datetime.now():
		return -1

	return decoded["user_id"]

# Establishes connection with Google Cloud SQL database
def get_connection():
	# when deployed to app engine the 'GAE_ENV' variable will be set to 'standard'
	if os.environ.get('GAE_ENV') == 'standard':
		# use the local socket interface for accessing Cloud SQL
		unix_socket = '/cloudsql/{}'.format(db_connection_name)
		conn = pymysql.connect(user=db_user, password=db_password, unix_socket=unix_socket, db=db_name)
	else:
		# if running locally use the TCP connections instead
		# set up Cloud SQL proxy (cloud.google.com/sql/docs/mysql/sql-proxy)
		host = '127.0.0.1'
		conn = pymysql.connect(user=db_user, password=db_password, host=host, db=db_name)

	return conn


# Adds new user to the Google Cloud SQL database
def add_new_user(username, password):
	conn = get_connection()
	cur = conn.cursor()

	# insert the new user into the mysql database
	cur.execute('INSERT INTO users (username, password) VALUES (%s,%s)', (username, password))
	conn.commit()

	cur.execute('SELECT user_id FROM users WHERE username=%s', (username,))
	user_id = cur.fetchone()

	conn.close()

	return user_id[0]

# Returns a list of all usernames in the database
# For the purpose of checking if a username already exists when someone picks one
def get_usernames():
	conn = get_connection()
	cur = conn.cursor()

	cur.execute('SELECT username FROM users')
	usernames = cur.fetchall()
	conn.close()

	# usernames is a list of tuples in the form (('username_1', ), (username_2, ), ...)
	# must iterate through each and add just the username to a result list
	usernames_result = []
	for username_tuple in usernames:
		usernames_result.append(username_tuple[0])

	return usernames_result

# Checks if login credentials are valid
def check_login_credentials(username, password):
	conn = get_connection()
	cur = conn.cursor()

	cur.execute('SELECT user_id, password FROM users WHERE username=%s', (username, ))
	user_info = cur.fetchone()
	conn.close()

	if user_info == None or user_info[1] != password:
		return -1

	return user_info[0]

# Posts a note to the database
def post_note(note_title, note_content, user_id):
	conn = get_connection()
	cur = conn.cursor()

	cur.execute('INSERT INTO notes (note_title, note_content, user_id) values (%s,%s,%s)',(note_title, note_content, user_id))

	conn.commit()
	conn.close()

# Gets all notes that belong to a given user id
def get_notes(user_id):
	conn = get_connection()
	cur = conn.cursor()

	cur.execute('SELECT * FROM notes WHERE user_id=%s',(user_id,))

	notes = cur.fetchall()

	conn.commit()
	conn.close()

	return notes

# Gets a single note given a note id
def get_note(note_id):
	conn = get_connection()
	cur = conn.cursor()

	cur.execute('SELECT * FROM notes WHERE note_id=%s',(note_id,))

	note = cur.fetchone()

	conn.close()

	return note

# To edit a note given a certain note id
def edit_note_db(note_id, note_title, note_content):
	conn = get_connection()
	cur = conn.cursor()

	cur.execute('UPDATE notes SET note_title=%s, note_content=%s WHERE note_id=%s', (note_title, note_content, note_id))

	conn.commit()
	conn.close()






