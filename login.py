from flask import Flask, render_template, request, redirect, jsonify, url_for, flash, Blueprint, Markup

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import User, Genre, TVShow, Base

from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

engine = create_engine('sqlite:///tvshows.db')
Base.metadata.bind = engine
# User.__table__.drop(engine)
DBSession = sessionmaker(bind=engine)
session = DBSession()

c_secret_json = open('client_secrets.json', 'r').read()
CLIENT_ID = json.loads(c_secret_json)['web']['client_id']

# create a blueprint, make code looks more structured 
mod = Blueprint('login', __name__, template_folder="/templates")


@mod.route('/login')
def login():
    # make a anti-forgery state token
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    # sava state token in session
    login_session['state'] = state
    return render_template('login.html',
                           login_session=login_session,
                           STATE=state)
@mod.route('/logout')
def logout():
    print '~~~~logout login_session', login_session
    flash('Logged out successfully.')
    if login_session['social'] == 'google':
        return gdisconnect();
    elif login_session['social'] == 'facebook':
        return fbdisconnect();


@mod.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # strip expire tag from access token
    token = result.split("&")[0]


    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]



    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    print '~~~~FB email', data['email']
    # The token must be stored in the login_session in order to properly logout, let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]
    login_session['social'] = 'facebook'

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash(("Now logged in as %s" % login_session['username']))
    return output

# @mod.route('/fbdisconnect')
def fbdisconnect():

    del login_session['access_token']
    del login_session['facebook_id']
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    del login_session['provider']

    # return "you have been logged out"
    return redirect('/')


@mod.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    request_state = request.args.get('state')
    print '~~~~gconnect \n', request_state
    if request_state != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.', 401))
        response.headers['Content-Type'] = 'application/json'
        return response

    # get authorization code from google
    code = request.data
    print '~~~~code', code
    # create a oauth flow object, then get a credentials object
    # from oauth flow
    try:
        flow = flow_from_clientsecrets('client_secrets.json', scope='')
        flow.redirect_uri = 'postmessage'
        credentials = flow.step2_exchange(code)
        print '~~~~~credentials', credentials
    except:
        response = make_response(json.dumps(
            'Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'test/plain'  # 'application/json'
        return response

    # validate access token got from credentials
    access_token = credentials.access_token
    print '~~~~~~access_token', access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' %
           access_token)
    http = httplib2.Http()
    result = json.loads(http.request(url, 'GET')[1])
    print '~~~~~result', result
    print '~~~~~-------', requests.get(url).json()
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response
    # trying to get credentials and gplus_id from
    # request's login_session
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    # if get
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # if not get, store the access token in
    # the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info from google apis
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    # save user info in login session
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['social'] = 'google'

    # see if user exists, if it doesn't make a new one
    # in database
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    # response = json.dumps('')
    return render_template('login_sucess.html', login_session=login_session)


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
# @mod.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    access_token = login_session.get('access_token')

    print '~~~~~disconnect credentials', login_session

    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    print '~~~~~disconnected result', h.request(url, 'GET')

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        # response = make_response(json.dumps('Successfully disconnected.'), 200)
        # response.headers['Content-Type'] = 'application/json'
        # return response
        return redirect('/')
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

    # return make_response(json.dumps('____che chee check'))


