#!/usr/bin/env python3.8

# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#
from flask import Flask, render_template, request, redirect, url_for, jsonify, abort, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from flask_migrate import Migrate
import json
import dateutil.parser
import babel
import sys
from flask_wtf import Form
from werkzeug.debug import console
from forms import *

# ----------------------------------------------------------------------------#
# creating fyyur_db database if not exist.
# ----------------------------------------------------------------------------#
engine = create_engine("postgres://sameh:Sameh.Pierre@localhost:5432/fyyur_db")
if not database_exists(engine.url):
    create_database(engine.url)

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#
app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://sameh:Sameh.Pierre@localhost:5432/fyyur_db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#
class Show(db.Model):
    __tablename__ = 'shows'

    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), primary_key=True)
    start_time = db.Column(db.DateTime, nullable=True)


class Venue_Genre(db.Model):
    __tablename__ = 'venue_genres'
    id = db.Column(db.Integer, primary_key=True)
    genre_name = db.Column(db.String(128), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)


class Artist_Genre(db.Model):
    __tablename__ = 'artist_genres'
    id = db.Column(db.Integer, primary_key=True)
    genre_name = db.Column(db.String(128), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)


class Venue(db.Model):
    __tablename__ = 'venues'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    city = db.Column(db.String(256), nullable=False)
    state = db.Column(db.String(12), nullable=False)
    address = db.Column(db.String(512), nullable=False)
    phone = db.Column(db.String(32), nullable=False)
    seeking_talent = db.Column(db.Boolean, nullable=False)
    seeking_description = db.Column(db.String(), nullable=True)
    web_site = db.Column(db.String(512), nullable=True)
    facebook_link = db.Column(db.String(), nullable=True)
    image_link = db.Column(db.String(), nullable=True)
    genres = db.relationship('Venue_Genre', backref='genres', lazy=True, cascade="all, delete-orphan")
    venue_shows = db.relationship('Show', backref='venue_shows', lazy=True, cascade="all, delete-orphan")


class Artist(db.Model):
    __tablename__ = 'artists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    state = db.Column(db.String(12), nullable=False)
    city = db.Column(db.String(256), nullable=False)
    address = db.Column(db.String(512), nullable=False)
    phone = db.Column(db.String(32), nullable=False)
    seeking_venue = db.Column(db.Boolean, nullable=False)
    seeking_description = db.Column(db.String(), nullable=True)
    web_site = db.Column(db.String(), nullable=True)
    image_link = db.Column(db.String(), nullable=True)
    facebook_link = db.Column(db.String(), nullable=True)
    genres = db.relationship('Artist_Genre', backref='genres', lazy=True, cascade="all, delete-orphan")
    artist_shows = db.relationship('Show', backref='artist_shows', lazy=True, cascade="all, delete-orphan")


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#
def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#
@app.route('/')
def index():
    return render_template('pages/home.html')


@app.route('/venues')
def venues():
    data = []
    date_now = datetime.now()
    venue_all = Venue.query.with_entities(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()

    for v in venue_all:
        venues_cs = Venue.query.filter(Venue.city == v.city, Venue.state == v.state).all()
        venue_city = []
        for ve in venues_cs:
            venue_city += [{
                "id": ve.id,
                "name": ve.name,
                "num_upcoming_shows": Show.query.filter(Show.venue_id == ve.id, Show.start_time > date_now).count()
            }]

        data += [{
            "city": v.city,
            "state": v.state,
            "venues": venue_city
        }]

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/<venue_id>')
def get_venue(venue_id):
    date_now = datetime.now()
    upcoming_shows = Show.query.join(Venue).join(Artist).filter(Show.venue_id == venue_id,
                                                                Show.artist_id == Artist.id,
                                                                Show.start_time > date_now).all()
    past_shows = Show.query.join(Venue).join(Artist).filter(Show.venue_id == venue_id, Show.artist_id == Artist.id,
                                                            Show.start_time < date_now).all()

    upcoming_shows_data = []
    for show in upcoming_shows:
        upcoming_shows_data.append({
            'artist_name': show.artist_shows.name,
            'start_time': show.start_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'artist_image_link': show.artist_shows.image_link,
            'artist_id': show.artist_shows.id

        })

    past_show_data = []
    for p_show in past_shows:
        past_show_data.append({
            'artist_name': p_show.artist_shows.name,
            'start_time': p_show.start_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'artist_image_link': p_show.artist_shows.image_link,
            'artist_id': p_show.artist_shows.id
        })
    venue = Venue.query.get(venue_id)
    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.web_site,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_show_data,
        "upcoming_shows": upcoming_shows_data,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }
    return render_template('pages/show_venue.html', venue=data)


@app.route('/artists')
def artists():
    data = Artist.query.with_entities(Artist.id, Artist.name).all()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/<artist_id>')
def get_artist(artist_id):
    date_now = datetime.now()
    upcoming_shows = Show.query.join(Artist).filter(Show.artist_id == artist_id, Show.venue_id == Venue.id,
                                                    Show.start_time > date_now).all()
    upcoming_shows_data = []
    for show in upcoming_shows:
        upcoming_shows_data.append({
            'venue_name': show.venue_shows.name,
            'start_time': show.start_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'venue_image_link': show.venue_shows.image_link,
            'venue_id': show.venue_shows.id
        })

    past_shows = Show.query.join(Artist).join(Venue).filter(Show.artist_id == artist_id, Show.venue_id == Venue.id,
                                                            Show.start_time < date_now).all()
    past_show_data = []
    for p_show in past_shows:
        past_show_data.append({
            'venue_name': p_show.venue_shows.name,
            'start_time': p_show.start_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'venue_image_link': p_show.venue_shows.image_link,
            'venue_id': p_show.venue_shows.id
        })

    artist = Artist.query.get(artist_id)
    data = {
        'id': artist.id,
        'name': artist.name,
        'genres': artist.genres,
        'address': artist.address,
        'city': artist.city,
        'state': artist.state,
        'phone': artist.phone,
        'website': artist.web_site,
        'facebook_link': artist.facebook_link,
        'seeking_talent': artist.seeking_venue,
        'seeking_description': artist.seeking_description,
        'image_link': artist.image_link,
        'past_shows': past_show_data,
        'upcoming_shows': upcoming_shows_data,
        'past_shows_count': len(past_shows),
        'upcoming_shows_count': len(upcoming_shows),
    }
    return render_template('pages/show_artist.html', artist=data)


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    try:
        venue = Venue()
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.address = request.form['address']
        venue.phone = request.form['phone']
        venue.facebook_link = request.form['facebook_link']
        venue.seeking_talent = True if request.form['seeking_talent'] == 'true' else False
        venue.seeking_description = request.form['seeking_description']
        venue.image_link = request.form['image_link']
        venue.web_site = request.form['website_link']
        db.session.add(venue)
        db.session.commit()

        venue_id = venue.id
        genres = request.form.getlist('genres')

        for genre in genres:
            v_genre = Venue_Genre()
            v_genre.venue_id = venue_id
            v_genre.genre_name = genre
            db.session.add(v_genre)
        db.session.commit()
        flash('Venue ' + venue.name + ' was successfully listed!')
    except():
        db.session.rollback()
        flash('Error: Venue ' + venue.name + ' has not listed!')
    finally:
        db.session.close()
        return render_template('pages/home.html')

    # on successful db insert, flash success

    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    try:
        artist = Artist()
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.address = request.form['address']
        artist.phone = request.form['phone']
        artist.facebook_link = request.form['facebook_link']
        artist.seeking_venue = True if request.form['seeking_venue'] == 'true' else False
        artist.seeking_description = request.form['seeking_description']
        artist.image_link = request.form['image_link']
        artist.web_site = request.form['website_link']
        db.session.add(artist)
        db.session.commit()

        artist_id = artist.id
        genres = request.form.getlist('genres')

        for genre in genres:
            a_genre = Artist_Genre()
            a_genre.artist_id = artist_id
            a_genre.genre_name = genre
            db.session.add(a_genre)
        db.session.commit()
        flash('Artist ' + artist.name + ' was successfully listed!')
    except BaseException as ex:
        db.session.rollback()
        flash('Something went wrong! please try again.')
    finally:
        db.session.close()
        return render_template('pages/home.html')

    # on successful db insert, flash success

    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/


@app.route('/shows')
def shows():
    shows_cs = Show.query.join(Venue).join(Artist).with_entities(Venue.id.label('venue_id'),
                                                                 Venue.name.label('venue_name'), Artist.id,
                                                                 Artist.name, Artist.image_link,
                                                                 Show.start_time).all()

    data = []

    for r in shows_cs:
        data.append({
            'artist_name': r.name,
            'venue_name': r.venue_name,
            'artist_id': r.id,
            'venue_id': r.venue_id,
            'artist_image_link': r.image_link,
            'start_time': r.start_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')  # .strftime("%m-%d-%Y, %H:%M:%S")
        })
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create', methods=['GET'])
def create_show_form():
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    try:
        venue_id = request.form['venue_id']
        artist_id = request.form['artist_id']
        start_time = request.form['start_time']
        show = Show()
        show.venue_id = venue_id
        show.artist_id = artist_id
        show.start_time = start_time
        db.session.add(show)
        db.session.commit()

        flash('Show was successfully listed')
        return render_template('pages/home.html')
    except():
        db.session.rollback()
        flash('Error: Show has not been listed!')
        return render_template('pages/home.html')
    finally:
        db.session.close()


@app.route('/venue/<venue_id>/edit', methods=['GET'])
def edit_venue_form(venue_id):
    venue_data = Venue.query.get(venue_id)
    venue_genre = Venue_Genre.query.filter(Venue_Genre.venue_id == venue_id).all()

    form = VenueEdit(obj=venue_data)
    form.seeking_talent.data = 'true' if venue_data.seeking_talent == True else 'false'
    form.genres.data = [v.genre_name for v in venue_genre]
    form.state.data = [venue_data.state]

    return render_template('forms/edit_venue.html', form=form, venue=venue_data)


@app.route('/venues/<venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    try:
        venue = Venue.query.get(venue_id)
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.address = request.form['address']
        venue.phone = request.form['phone']
        venue.facebook_link = request.form['facebook_link']
        venue.seeking_talent = True if request.form['seeking_talent'] == 'true' else False
        venue.seeking_description = request.form['seeking_description']
        venue.image_link = request.form['image_link']
        venue.web_site = request.form['website_link']

        genres = request.form.getlist('genres')

        venue_genre = Venue_Genre.query.filter(Venue_Genre.venue_id == venue_id).all()
        for v_g in venue_genre:
            db.session.delete(v_g)

        for g in genres:
            venue_genres = Venue_Genre()
            venue_genres.venue_id = venue_id
            venue_genres.genre_name = g
            db.session.add(venue_genres)

        db.session.commit()

        flash('Venue ' + venue.name + ' was successfully updated!')
        return render_template('pages/home.html')
    except():
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()


@app.route('/artists/<artist_id>/edit', methods=['GET'])
def edit_artist_form(artist_id):
    artist_data = Artist.query.get(artist_id)
    artist_genre = Artist_Genre.query.filter(Artist_Genre.artist_id == artist_id).all()

    form = ArtistForm(obj=artist_data)
    form.genres.data = [a.genre_name for a in artist_genre]
    form.seeking_venue.data = 'true' if artist_data.seeking_venue == True else 'false'
    form.state.data = [artist_data.state]

    return render_template('forms/edit_artist.html', form=form, artist=artist_data)


@app.route('/artists/<artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    try:
        artist = Artist.query.get(artist_id)
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.address = request.form['address']
        artist.phone = request.form['phone']
        artist.facebook_link = request.form['facebook_link']
        artist.seeking_venue = True if request.form['seeking_venue'] == 'true' else False
        artist.seeking_description = request.form['seeking_description']
        artist.image_link = request.form['image_link']
        artist.web_site = request.form['website_link']

        genres = request.form.getlist('genres')

        artist_genre = Artist_Genre.query.filter(Artist_Genre.artist_id == artist_id).all()
        for a_g in artist_genre:
            db.session.delete(a_g)

        for g in genres:
            artist_genres = Artist_Genre()
            artist_genres.artist_id = artist_id
            artist_genres.genre_name = g
            db.session.add(artist_genres)

        db.session.commit()

        flash('Artist ' + artist.name + ' was successfully updated!')
        return render_template('pages/home.html')
    except BaseException:
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        flash('Venue has been deleted successfully!')
    except():
        db.rollback()
        flash('Error: Venue has not been deleted, please try again!')
    finally:
        db.session.close()
        return redirect(url_for('venues'))


@app.route('/artist/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
    try:
        artist = Artist.query.get(artist_id)
        db.session.delete(artist)
        flash('Artist has been deleted successfully!')
    except():
        db.session.rollback()
        flash('Error: Artist has not been deleted!')
    finally:
        db.session.close()
        return redirect(url_for('artists'))


@app.route('/venues/search', methods=['POST'])
def search_venues():
    key_word = request.form.get('search_term')
    venues = Venue.query.filter(Venue.name.ilike('%' + key_word + '%')).with_entities(Venue.id, Venue.name).all()
    data = {
        "count": len(venues),
        "data": venues
    }
    return render_template('pages/search_venues.html', results=data,
                           search_term=key_word)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    key_word = request.form.get('search_term')
    artists = Artist.query.filter(Artist.name.ilike('%' + key_word + '%')).with_entities(Artist.id, Artist.name).all()
    data = {
        "count": len(artists),
        "data": artists
    }
    return render_template('pages/search_venues.html', results=data,
                           search_term=key_word)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()
