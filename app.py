#!/usr/bin/env python3
# encoding: utf-8

import os
import json

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
		print('sending static create.htm')
		return app.send_static_file('create.htm')
	else:
		session['tokens'] = session.get('tokens', [])
		session.new = True

		# by default each value in request.form is a list
		# this gets only the first item from each
		form = request.form.to_dict(flat=True)
		p = poster.create_poster(**form)
		session['tokens'].append(p.token)
		session.modified = True
		return redirect('/poster/{}'.format(p.id))


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
		poster.db.edit(id=id, token=token, **request.form.to_dict(flat=True))
		return render_template('poster.html', poster=poster.db.get_poster(id, token))
	else: # method == 'GET' but no token
		abort(403)

@app.route('/search')
def search():
	args = list(map(request.args.get), ('lat', 'long', 'radius'))
	return render_template('search_results.html', **poster.search(*args))


# Trường wanted it. Whatever.
@app.route('/12yos')
def twelve_yos():
	return 'Chào mừng các em đến năm học mới!'


@app.errorhandler(403)
def forbidden(e):
	return render_template('403.html'), 403

def main():
	app.run(
		host=os.getenv('IP', '0.0.0.0'),
		port=int(os.getenv('PORT', 5000))
	)


if __name__ == '__main__':
	main()
