from flask import Flask
from flask import Flask, render_template, request, redirect, url_for, session
import os,re
import pymongo
import hashlib
from bson import ObjectId
import urllib.request
import urllib.parse
from flask_session import Session
from datetime import timedelta
app = Flask(__name__)
app.secret_key = os.urandom(12)
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=5)

# The maximum number of items the session stores
# before it starts deleting some, default 500
app.config['SESSION_FILE_THRESHOLD'] = 100

app.config['SECRET_KEY'] = 'minimeurl'

app.config['SESSION_TYPE'] = 'filesystem'

DEFAULT_CONNECTION_URL = "mongodb://localhost:27017/"
User_DB = "minimeUrl"
# Establish a connection with mongoDB
client = pymongo.MongoClient(DEFAULT_CONNECTION_URL)
#client = pymongo.MongoClient("mongodb+srv://admin:dbroot@cluster0.mkrgt.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
# Create a DB
UserdataBase = client[User_DB]
UserCol = UserdataBase["UserDb"]
collection = UserdataBase['minimeUrls']
#host="https://mini-me-url.herokuapp.com/"
host="http://localhost:5000/"

@app.route('/<short_url>')
def urlredirector(short_url):
    query1 = {'turl':str(short_url)}
    results = collection.find_one(query1)
    if results!=None:
        noofvisits(str(short_url))
        return redirect('https://'+results.get('OriginalUrl'))
    else:
        return "Error"
@app.route('/', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access

        username = request.form['username']
        password = request.form['password']

        query1 = {'Username':str(username),'password':str(password)}
        results = UserCol.find_one(query1)
        if results!=None:
            session['loggedin'] = True
            session['id'] = str(results.get('_id'))
            session['username'] = results.get('Username')
            # Redirect to home page
            if username=='admin':
                return render_template("admin.html")
            return redirect(url_for('home'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    return render_template('login.html', msg=msg)
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        query1 = {'Username': str(username), 'password': str(password)}
        results = UserCol.find_one(query1)
        if results != None:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            record = {'Username': str(username), 'password': str(password),'email':str(email)}
            UserCol.insert_one(record)
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)

@app.route('/home')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('home.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        Object = ObjectId(str(session['id']))
        # We need all the account info for the user so we can display it on the profile page
        query1 = {'_id':Object}
        results = UserCol.find_one(query1)
        Object = str(session['username'])
        query={'Username':Object}
        userdetails = collection.find(query)
        # Show the profile page with account info
        return render_template('profile.html', account=results, userinfo=userdetails)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/tinyurl',methods=['GET','POST'])
def tinyurl():
    if request.method=='POST':
        url=request.form.get('Url')
        ourl=url
        Username = str(session['username'])
        if 'https://' in url:
            url=url[8:]
        turl=isexist(url)
        if Username=='admin':
            try:
                urllib.request.urlopen(ourl)
                # Catching the exception generated
                if turl == None:
                    tinyurl = newUrl(url)
                    return render_template('admin.html', res='Minimized Url: {0}{1}'.format(host, tinyurl),)
                else:
                    return render_template('admin.html',
                                           res='Failed to add. URL already exists {0}{1}'.format(host, turl))
            except Exception :
                return render_template('admin.html', res='Failed to minimize. Url does not exist')
        else:
          try:
            urllib.request.urlopen(ourl)

            # Catching the exception generated
            if turl==None:
                tinyurl=newUrl(url)
                return render_template('home.html', urls='Minimized Url: {0}{1}'.format(host,tinyurl),username=Username)
            else:
                return render_template('home.html',urls='Failed to add. URL already exists {0}{1}'.format(host,turl),username=Username)
          except Exception :
            return render_template('home.html',urls='Failed to minimize. Url does not exist',username=Username)

@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))


def isexist(url):
    query1 = {'OriginalUrl':url}
    results = collection.find_one(query1)
    if results!=None:
       return results.get('turl')

def newUrl(url):
    Username = str(session['username'])
    hash=int(hashlib.sha1(url.encode("utf-8")).hexdigest(), 16) % (10 ** 8)
    string1 = ''
    print(hash)
    digits = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
    for i in range(8):
        string1 += digits[(hash % 10)]
        hash //= 10
    hash=string1[::-1]
    record = {'Username':Username,
        'OriginalUrl': url,
              'turl': host+'/'+hash,
              'nov': '1'}
    if collection.insert_one(record)!=None:
        return hash

def noofvisits(url):
    query1 = {"turl": url}
    results = collection.find_one(query1)
    if results != None:
        collection.update_one(query1, {'$set': {'nov': int(results.get('nov')) + 1}})

@app.route('/admin',methods=["GET","POST"])
def admin():
    print('Hello')
    if request.method=="POST":
        users=str(UserCol.count())
        results=collection.find({})
        noOfLinks=str(results.count())
        Highestvisits=0
        for i in results:
            if int(i.get('nov'))>int(Highestvisits):
                Highestvisits=str(i.get('nov'))
                olink=i.get('OriginalUrl')
                tlink=i.get("turl")
        return render_template("results.html",users=users,noflinks=noOfLinks,highest=Highestvisits,olink=olink,tlink=tlink,res=results)
    return render_template('admin.html')

if __name__ == "__main__":

    app.run(debug=True,host='0.0.0.0', port=5000)

