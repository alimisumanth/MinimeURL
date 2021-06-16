from flask import Flask, render_template, request, redirect, url_for, session
import os
import re
import pymongo
import hashlib
from bson import ObjectId
import urllib.request
import urllib.parse
from datetime import timedelta

app = Flask(__name__)
app.secret_key = os.urandom(12)
app.config['SESSION_PERMANENT'] = True  # This makes the flask session to be active even if we close the browser
app.config['SESSION_TYPE'] = 'filesystem'  # FileSystemSessionInterface
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=5)  # Life time of permanent session

# The maximum number of items the session stores
# before it starts deleting some, default 500
app.config['SESSION_FILE_THRESHOLD'] = 100

app.config['SECRET_KEY'] = 'minimeurl'

app.config['SESSION_TYPE'] = 'filesystem'

DEFAULT_CONNECTION_URL = "mongodb://localhost:27017/"  # MongoDB connection URL
User_DB = "minimeUrl"  # MongoDB User database name
# Establish a connection with mongoDB
# client = pymongo.MongoClient(DEFAULT_CONNECTION_URL)
client = pymongo.MongoClient('mongodb://localhost:27017/')
# Create a DB
UserdataBase = client[User_DB]
UserCol = UserdataBase["UserDb"]
collection = UserdataBase['minimeUrls']
# host="https://mini-me-url.herokuapp.com/"  # Heroku URL
host = "http://localhost:5000/"  # LocalHost URL


@app.route('/<short_url>')
def urlredirector(short_url):
    """This method is called whenever shortened url is hit from browser.
   It takes the url and removes host from it and searches for the
   original URL based on the shortened URL"""
    query1 = {'turl': host + str(short_url)}  # Query to search in MongoDB database
    results = collection.find_one(query1)     # Finding the URL
    if results != None:                       # checks if returned URL is valid or none
        noofvisits(str(short_url))            # method call for incrementing the number of visits column in database
        return redirect('https://' + results.get('OriginalUrl'))  # redirecting to Original URL
    else:                                     # called when returned query is none
        return "Error"                        # Return an error message


@app.route('/', methods=['GET', 'POST'])
def login():
    """This is the root method and it will redirect to login/register page"""
    # Output message if something goes wrong...
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access

        username = request.form['username']  # retrieving username from loginpage
        password = request.form['password']  # retrieving password from loginpage

        query1 = {'Username': str(username), 'password': str(password)}  # Query to check username and password in Database
        results = UserCol.find_one(query1)   # finding the results
        if results != None:                  # check if returned result is valid or not
            session['loggedin'] = True       # Setting user logged in parameter to True in session
            session['id'] = str(results.get('_id'))  # Assigning session ID
            session['username'] = results.get('Username')  # Assigning Username to session
            # Redirect to home page
            if username == 'admin':           # Check if user is admit
                return render_template("admin.html")  # return admin page if user is admin
            return redirect(url_for('home'))  # return home page for non admin user
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    return render_template('login.html', msg=msg)  # Redirecting to login page with message


@app.route('/register', methods=['GET', 'POST'])
def register():
    """This method is used too register a new user"""
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']  # retrieving username from registration page
        password = request.form['password']  # retrieving password from registration page
        email = request.form['email']        # retrieving email from registration page
        query1 = {'Username': str(username), 'password': str(password)}
        results = UserCol.find_one(query1)  # Query to check if user already exists
        if results != None:  # chech if user already exists
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):  # email validation
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):  # username validation
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:  # Check for validation
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            record = {'Username': str(username), 'password': str(password), 'email': str(email)}
            UserCol.insert_one(record)  # creating a new user
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)  # redirecting to registration page with message


@app.route('/home')
def home():
    """This gets called when user is logged in"""
    # Check if user is logged in
    if 'loggedin' in session:  # Check for user login status
        # User is logged in show them the home page
        return render_template('home.html', username=session['username'])
    # User is not logged in redirect to login page
    return redirect(url_for('login'))


@app.route('/profile')
def profile():
    """This method gets called when ever user want to know the details"""
    # Check if user is loggedin
    if 'loggedin' in session:
        objects = ObjectId(str(session['id']))
        # We need all the account info for the user so we can display it on the profile page
        query1 = {'_id': objects}
        results = UserCol.find_one(query1)
        objects = str(session['username'])
        query = {'Username': objects}
        userdetails = collection.find(query)
        # Show the profile page with account info
        return render_template('profile.html', account=results, userinfo=userdetails)
    # User is not logged in redirect to login page
    return redirect(url_for('login'))


@app.route('/tinyurl', methods=['GET', 'POST'])
def tinyurl():
    """Whenever a new request for shortening url is submitted this method takes the url and returns minimised URL"""
    if request.method == 'POST':
        url = request.form.get('Url')  # Retrieving originalURL from user request
        ourl = url
        Username = str(session['username'])  # Assigning the user to the URL to keep track
        if 'https://' in url:
            url = url[8:]  # Removing http
        turl = isexist(url)  # method call to check if URL already exists
        if Username == 'admin':  # check if user is admin
            try:
                urllib.request.urlopen(ourl)
                # Catching the exception generated
                if turl == None:  # check if url is valid
                    tinyurl = newUrl(url)   # Method call for creating a new request to minimise URL
                    return render_template('admin.html',
                                           res='Minimized Url: {0}{1}'.format(host, tinyurl), )  # redirecting to admin page with minimized URL
                else:
                    return render_template('admin.html',
                                           res='Failed to add. URL already exists {0}{1}'.format(host,
                                                                                                 turl))  # If URL already exists it
            except Exception:
                return render_template('admin.html',
                                       res='Failed to minimize. Url does not exist')  # If any error occurs
        else:
            try:
                urllib.request.urlopen(ourl)

                # Catching the exception generated
                if turl == None:  # check if url is valid
                    tinyurl = newUrl(url)  # Method call for creating a new request to minimise URL
                    return render_template('home.html', urls='Minimized Url: {0}{1}'.format(host, tinyurl),
                                           username=Username)  # redirecting to admin page with minimized URL
                else:
                    return render_template('home.html',
                                           urls='Failed to add. URL already exists {0}{1}'.format(host, turl),
                                           username=Username)  # If URL already exists it
            except Exception:
                return render_template('home.html', urls='Failed to minimize. '
                                                         'Url does not exist', username=Username)  # If any error occurs


@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    # Redirect to login page
    return redirect(url_for('login'))


def isexist(url):
    """Method to check if URL already exists in database"""
    query1 = {'OriginalUrl': url}
    results = collection.find_one(query1)  # finding the results
    if results != None:  # Check to find if url exists or not
        return results.get('turl')


def newUrl(url):
    """Method to handle new request for URL minimization"""
    Username = str(session['username'])  # Retrieving Username
    url_hash = int(hashlib.sha1(url.encode("utf-8")).hexdigest()
                   , 16) % (10 ** 8)  # Generating Hash code for URL
    string1 = ''
    digits = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
    for i in range(8):
        string1 += digits[(url_hash % 10)]  # Converting hashcode to characters
        url_hash //= 10
    url_hash = string1[::-1]
    record = {'Username': Username,
              'OriginalUrl': url,
              'turl': host + url_hash,
              'nov': '1'}  # Query to insert new record
    if collection.insert_one(record) != None:
        return url_hash


def noofvisits(url):
    """Method t keep track of number of visits for a ShortenedURL in Database"""
    query1 = {"turl": host + url}
    results = collection.find_one(query1)
    if results != None:
        collection.update_one(query1,
                              {'$set': {'nov': int(results.get('nov')) + 1}})  # Incrementing the value of visits


@app.route('/admin', methods=["GET", "POST"])
def admin():
    """Method for handling admin requests"""
    if request.method == "POST":
        users = str(UserCol.count())
        results = collection.find({})
        noOfLinks = str(results.count())
        Highestvisits = 0
        for i in results:
            if int(i.get('nov')) > int(Highestvisits):
                Highestvisits = str(i.get('nov'))
                olink = i.get('OriginalUrl')
                tlink = i.get("turl")
        return render_template("results.html", users=users, noflinks=noOfLinks, highest=Highestvisits, olink=olink,
                               tlink=tlink, res=results)
    return render_template('admin.html')


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
