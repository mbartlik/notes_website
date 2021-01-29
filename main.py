from flask import Flask, render_template, request, flash, url_for, redirect
from models import *


app = Flask(__name__) # creates server object
app.config['SECRET_KEY'] = 'GEBGREIFQ'

# Login page
@app.route('/', methods=["GET","POST"])
def login():
	if request.method == "POST":
		username = request.form['username']
		password = request.form['password']

		# check login info, if correct then redirect else display error
		user_id = check_login_credentials(username,password)
		if user_id != -1:
			token = get_token(user_id)
			return redirect(url_for('home', token=token))
		else:
			flash('Invalid username or password')

	return render_template('login.html', token="-1")


# Create account page
@app.route('/create-account', methods=["GET","POST"])
def create_account():

	if request.method == "POST":
		valid_fields = True # set to false if any invalid fields

		# get form data
		username = request.form['username']
		password = request.form['password']
		confirm_password = request.form['confirm_password']

		# check for valid form data
		if username in get_usernames():
			valid_fields = False
			flash('Sorry that username already exists')
		elif username == "" or password == "":
			valid_fields = False
			flash('Make sure all fields are filled out')
		elif password != confirm_password:
			valid_fields = False
			flash('Make sure your passwords match')
		elif len(password) < 4:
			valid_fields = False
			flash('Your password needs to be at least 4 characters')
		elif len(username) < 4:
			valid_fields = False
			flash('Your username needs to be at least 4 character')

		if valid_fields:
			new_user_id = add_new_user(username,password)

			# get token from new user id
			token = get_token(new_user_id)

			print(new_user_id)

			return redirect(url_for('home', token=token))

	# this will execute if going to this page for the first time (GET request) or if invalid fields
	return render_template('create_account.html', token="-1")


# Home page
@app.route('/home/<token>')
def home(token):
	# this means the user is not logged in yet
	if token == "-1":
		return redirect(url_for('login'))

	# check for valid token
	user_id = authenticate_token(token)
	if user_id == -1:
		flash('Your session has expired, login again')
		return redirect(url_for('login'))

	notes = get_notes(user_id)
	print(notes)

	return render_template('home.html', token=token, notes=notes)


# Endpoint to create a new note
@app.route('/new-note/<token>', methods=['GET','POST'])
def new_note(token):

	# check for valid token
	user_id = authenticate_token(token)
	if user_id == -1:
		flash('Your session has expired, login again')
		return redirect(url_for('login'))

	if request.method == 'POST':
		note_title = request.form['note_title']
		note_content = request.form['note_content']

		# check for valid fields
		valid_fields = True
		if note_title == "":
			flash('Make sure to give your note a title')
			valid_fields = False
		elif note_content == "":
			flash('Make sure to write a note')
			valid_fields = False

		# only post note and redirect if fields are valid
		if valid_fields:
			post_note(note_title, note_content, user_id)
			return redirect(url_for('home', token=token))

	return render_template('new_note.html', token=token)

# Endpoint to display a note
@app.route('/note/<int:note_id>/<token>')
def show_note(note_id, token):
	# check for valid token
	user_id = authenticate_token(token)
	if user_id == -1:
		flash('Your session has expired, login again')
		return redirect(url_for('login'))

	note = get_note(note_id) # note is in format (note_id, note_title, note_content, user_id)

	return render_template('show_note.html', token=token, note=note)

# Endpoint to edit a note
@app.route('/edit_note/<int:note_id>/<token>', methods=["GET","POST"])
def edit_note(note_id, token):

	# if the request method is post then they submitted an edited note
	if request.method == 'POST':
		new_title = request.form['note_title']
		new_content = request.form['note_content']
		edit_note_db(note_id, new_title, new_content)
		return redirect(url_for('show_note', note_id=note_id, token=token))

	note = get_note(note_id)
	return render_template('edit_note.html', token=token, note=note)

if __name__ == '__main__':
	app.run(debug=True)



# start cloud sql proxy on local - ./cloud_sql_proxy -instances=maxs-note-keeper:us-east4:user-data=tcp:3306


# need to check existing usernames
