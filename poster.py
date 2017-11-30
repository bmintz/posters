#!/usr/bin/env python3
# encoding: utf-8

from collections import namedtuple as _namedtuple
from datetime import datetime as _datetime
import json as _json

from geopy.distance import distance as _distance
from geopy.format import format_degrees as _format_degrees
from geopy.geocoders import GoogleV3 as _GoogleV3

import util as _util

"""defines poster classes and utilities for interacting with the poster db"""

_G = _GoogleV3()


def _get_filesize(file):
	old_pos = file.tell()
	file.seek(0, 2) # seek to the end of the file
	size = file.tell() # current position
	file.seek(old_pos) # go back to the beginning
	return size


def _create_file_if_non_existent(filename):
	try:
		return open(filename, 'a')
	except FileNotFoundError:
		return open(filename, 'x')


def time_at(*location):
	try:
		now = _datetime.now(tz=_G.timezone(location))
	except:
		now = _datetime.utcnow()
	return _datetime.strftime(now, '%Y-%m-%d %H:%M:%S UTC%z')


class Poster:
	fields = ['title', 'text', 'lat', 'long', 'author', 'date', 'last_modified']

	def __init__(self, title, lat, long, text, author):
		self.title = title
		self.lat, self.long = lat, long
		self.text = text
		self.author = author

		self.id = db[-1]['id']+1 if len(db) > 1 else 0
		self.token = _util.token_urlsafe()
		self.date = self.time_here()
		self.last_modified = None

	def distance(self, lat, long):
		return _distance((self.lat, self.long), (lat, long))

	def time_here(self):
		return time_at(self.lat, self.long)

	def validate(self, id, token=None):
		id_valid = id == self.id
		if token is not None:
			return token == self.token and id_valid
		else:
			return id_valid

	def edit(self, **kwargs):
		self.validate(kwargs['id'], kwargs['token'])
		for field in self.fields:
			new_val = kwargs.get(field)
			if new_val is not None:
				setattr(self, field, new_val)
		self.last_modified = self.time_here()

	def as_dict(self):
		d = {}
		for field, value in zip(self.fields, iter(self)):
			d[field] = value
		d.update({
			'token': self.token,
			'id': self.id,
		})
		return d

	@classmethod
	def from_dict(cls, d):
		p = Poster(
			**{k: d[k] for k in set(cls.fields) - {'date', 'last_modified'}}
		)
		p.id = d['id']
		p.token = d['token']
		p.date = d['date']
		p.last_modified = d['last_modified']

		return p

	def __iter__(self):
		yield from map(self.__getattribute__, self.fields)

class Database(list):
	def __init__(self, filename='db.json'):
		self.filename = filename

		self._initialize_db_if_nonexistent()
		with open(filename) as db_file:
			self.extend(_json.load(db_file))

	def _initialize_db_if_nonexistent(self):
		file = _create_file_if_non_existent(self.filename)
		with file:
			if _get_filesize(file) == 0:
				_json.dump([], file)
				#pass

	def get_poster(self, id, token=None):
		"""return a Poster object corresponding to the id.
		If token is passed, validate that token against the database.
		If the token is invalid, raise InvalidTokenError"""
		try:
			poster = Poster.from_dict(self[id])
		except IndexError:
			raise InvalidPosterError
		else:
			if poster.validate(id, token):
				return poster
			else:
				raise InvalidTokenError

	def search(self, lat, long, radius, unit):
		for poster in map(Poster.from_dict, self):
			distance = getattr(poster.distance(lat, long), unit)
			if distance <= radius:
				poster.distance = round(distance, 2)
				poster.unit = unit
				yield poster

	def edit(self, **kwargs):
		id = kwargs['id']
		token = kwargs['token']
		if id in range(len(self)):
			poster = self.get_poster(id)
			if not poster.validate(id, token):
				raise InvalidTokenError
			else:
				poster.edit(**kwargs)
				self[id] = poster.as_dict()
		self.save()

	def save(self):
		with open(self.filename, 'w') as f:
			_json.dump(self[:], f)

	def append(self, poster):
		super().append(poster.as_dict())
		self.save()

db = Database()

def create_poster(**kwargs):
	lat, long = float(kwargs['lat']), float(kwargs['long'])
	p = Poster(**kwargs)
	db.append(p)
	return p

class InvalidTokenError(Exception):
	pass

class InvalidPosterError(Exception):
	pass
