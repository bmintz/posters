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
from util import config

app = Flask('digdug', static_url_path='/static')

app.debug = config['debug']
app.secret_key = config['secret_key']


@app.route('/index')
def index():
	return render_template('index.html', posters=poster.db.values())

@app.route('/poster/<id>')
def view_poster(id):
	return render_template(
		'poster.html',
		poster=get_poster(int(id)),
	)

@app.route('/create', methods=('POST', 'GET'))
def newpost():
	if request.method == 'GET':
		return render_template('create.html')
	session['tokens'] = session.get('tokens', [])

	# by default each value in request.form is a list
	# this gets only the first item from each
	form = request.form.to_dict(flat=True)
	p = poster.create_poster(**form)
	session['tokens'].append(p.token)
	session.modified = True
	return redirect(get_host_url() + '/poster/{}'.format(p.id))


@app.route('/edit/<id>', methods=('POST', 'GET'))
def edit(id):
	id = int(id)
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
	form = request.form.to_dict(flat=True)
	try:
		poster.db.edit(id=id, token=token, **form)
	except InvalidLocationError:
		abort(400)
	return redirect(get_host_url() + '/poster/%s' % id)

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


def cast_form(d):
	d['lat'], d['long'] = map(float, (d['lat'], d['long']))


def main():
	app.run(
		host=os.getenv('IP', '0.0.0.0'),
		port=int(os.getenv('PORT', 5000))
	)


if __name__ == '__main__':
	main()
