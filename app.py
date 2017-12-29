#!/usr/bin/env python3
# encoding: utf-8

import os
import json
import urllib.parse

from geopy.distance import distance
from flask import (
	abort,
	Flask,
	url_for,
	redirect,
	render_template,
	request,
	session,
)

import poster
from poster import (
	InvalidPosterError,
	InvalidTokenError,
	PosterDeletedError,
	InvalidLocationError,
)
from util import config, token_urlsafe

app = Flask('digdug', static_url_path='/static')

app.debug = config['debug']
app.secret_key = config['secret_key']

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True


@app.before_request
def setup_tokens():
	session.setdefault('tokens', [])


@app.before_request
def csrf_protecc():
	if request.method == 'POST':
		token = session.pop('_csrf_token', None)
		if token is None or token != request.form.get('_csrf_token'):
			abort(403)
		else:
			# by default each value in request.form is a list
			# this gets only the first item from each
			request.form = request.form.to_dict(flat=True)
			# don't pass the token along to the database
			request.form.pop('_csrf_token', None)


def generate_csrf_token():
	if '_csrf_token' not in session:
		session['_csrf_token'] = token_urlsafe()
	return session['_csrf_token']


app.jinja_env.globals['csrf_token'] = generate_csrf_token


@app.route('/index')
def index():
	return render_template('index.html', posters=poster.db.values())


@app.route('/poster/<int:id>')
def view_poster(id):
	poster = get_poster(id)
	owns_poster = False

	for token in session['tokens']:
		if poster.validate(token):
			owns_poster = True
			break

	return render_template(
		'poster.html',
		poster=poster,
		owns_poster=owns_poster,
	)


@app.route('/create', methods=('POST', 'GET'))
def newpost():
	if request.method == 'GET':
		return render_template('create.html')

	try:
		p = poster.create_poster(**request.form)
	except InvalidLocationError:
		abort(400)
	session['tokens'].append(p.token)
	session.modified = True
	return redirect(get_poster_url(p.id))


@app.route('/edit/<int:id>', methods=('POST', 'GET'))
def edit(id):
	token = request.args.get('token')
	if request.method == 'GET' and 'token' in request.args:
		return render_template('edit.html', poster=get_poster(id, token))
	elif request.method == 'POST':
		return process_edit_request(id, token)
	else: # method == 'GET' but no token
		abort(403)

def process_edit_request(id, token):
	if token is None:
		abort(403)
	token = request.args.get('token')
	# we discard the value returned because we only need get_poster
	# for the exceptions it raises
	get_poster(id, token)
	if request.form.get('delete') == 'true':
		del poster.db[id]
		# go back home
		return redirect(get_host_url())
	try:
		poster.db.edit(id=id, token=token, **request.form)
	except InvalidLocationError:
		abort(400)
	return redirect(get_poster_url(id))

def get_poster(id, token=None):
	try:
		return poster.db.get_poster(id, token)
	except InvalidPosterError:
		abort(404)
	except InvalidTokenError:
		abort(403)
	except PosterDeletedError:
		abort(410)
	except InvalidLocationError:
		abort(400)

@app.route('/search')
def search():
	location, radius, unit = map(
		request.args.get,
		('location', 'radius', 'unit')
	)
	if location is None or radius is None:
		abort(400)
	radius = float(radius)
	unit = request.args.get('unit')
	try:
		return render_template(
			'search_results.html',
			posters=poster.db.search(location, radius, unit),
			unit=unit,
		)
	except InvalidLocationError:
		abort(400)


def get_host_url():
	# shame that I have to do this
	return request.headers.get('X-URI')


def get_poster_url(id):
	return get_host_url() + '/poster/%s' % id


def cast_form(d):
	d['lat'], d['long'] = map(float, (d['lat'], d['long']))


def main():
	app.run(
		host=os.getenv('IP', '0.0.0.0'),
		port=int(os.getenv('PORT', 5000))
	)


if __name__ == '__main__':
	main()
