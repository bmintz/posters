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

import util
import poster

app = Flask('digdug', static_url_path='/static')
app.debug = False
app.secret_key = 'Zf4je8VNbpfGHUHovvv6xWO2MOKQxhR7QSGi9eBcqSs'


@app.route('/index')
def index():
	return render_template('index.html', items=poster.db)

@app.route('/poster/<id>')
def view_poster(id):
	return render_template(
		'poster.html',
		poster=poster.db.get_poster(int(id)),
	)

@app.route('/create', methods=('POST', 'GET'))
def newpost():
	if request.method == 'GET':
		return render_template('create.html')
	session['tokens'] = session.get('tokens', [])

	# by default each value in request.form is a list
	# this gets only the first item from each
	form = request.form.to_dict(flat=True)
	cast_form(form)
	p = poster.create_poster(**form)
	session['tokens'].append(p.token)
	session.modified = True
	return redirect(get_host_url() + '/poster/{}'.format(p.id))


@app.route('/edit/<id>', methods=('POST', 'GET'))
def edit(id):
	id = int(id)
	if request.method == 'GET' and 'token' in request.args:
		token = request.args['token']
		try:
			return render_template(
				'edit.html',
				poster=poster.db.get_poster(id, token)
			)
		except ValueError:
			abort(403)
	elif request.method == 'POST':
		token = request.args.get('token')
		form = request.form.to_dict(flat=True)
		cast_form(form)
		poster.db.edit(id=id, token=token, **form)
		return redirect(get_host_url() + '/poster/%s' % id)
	else: # method == 'GET' but no token
		abort(403)

@app.route('/search')
def search():
	lat = float(request.args.get('lat'))
	long = float(request.args.get('long'))
	radius = float(request.args.get('radius'))
	unit = request.args.get('unit')
	return render_template(
		'search_results.html',
		items=poster.db.search(lat, long, radius, unit),
		unit=unit,
	)


def get_host_url():
	# shame that I have to do this
	return request.headers.get('X-URI')


@app.errorhandler(403)
def forbidden(e):
	return render_template('403.html'), 403


def cast_form(d):
	d['lat'], d['long'] = map(float, (d['lat'], d['long']))


def main():
	app.run(
		host=os.getenv('IP', '0.0.0.0'),
		port=int(os.getenv('PORT', 5000))
	)


if __name__ == '__main__':
	main()
