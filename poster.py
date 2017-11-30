#!/usr/bin/env python3
# encoding: utf-8

from collections import namedtuple as _namedtuple
import copy as _copy
from datetime import datetime as _datetime
import json as _json
import pickle as _pickle

from geopy.distance import distance as _distance
from geopy.format import format_degrees as _format_degrees
from geopy.geocoders import GoogleV3 as _GoogleV3

import util as _util

"""defines poster classes and utilities for interacting with the poster db"""

with open('config.json') as _conf:
	_CONFIG = _json.load(_conf)
_G = _GoogleV3(_CONFIG['api_keys']['google_maps_geocoding'])


def _get_filesize(file):
	old_pos = file.tell()
	file.seek(0, 2) # seek to the end of the file
	size = file.tell() # current position
	file.seek(old_pos) # go back to the beginning
	return size


def _create_file_if_non_existent(filename):
	try:
		return open(filename, 'ab')
	except FileNotFoundError:
		return open(filename, 'xb')


def time_at(*location):
	try:
		now = _datetime.now(tz=_G.timezone(location))
	except:
		now = _datetime.utcnow()
	return _datetime.strftime(now, '%Y-%m-%d %H:%M:%S UTC%z')


class Poster:
	fields = ['title', 'text', 'lat', 'long', 'location', 'author', 'date', 'last_modified']

	def __init__(self, title, location: str, text, author):
		self.title = title
		self.location = location
		self.get_latlong()
		self.text = text
		self.author = author

		self.id = len(db)
		self.token = _util.token_urlsafe()
		self.date = self.time_here()
		self.last_modified = None

	def get_latlong(self):
		result = _G.geocode((self.lat, self.long))
		if result is None:
			raise InvalidLocationError
		else:
			self.lat, self.long = result.point[:2]

	def distance(self, lat, long):
		return _distance((self.lat, self.long), (lat, long))

	def time_here(self):
		return time_at(self.lat, self.long)

	def validate(self, token=None):
		if token is not None:
			return token == self.token
		return True

	def edit(self, **kwargs):
		if not self.validate(kwargs['token']):
			raise InvalidTokenError
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
		# since these fields are generated automatically by __init__,
		# we have to set them ourselves
		p.id = d['id']
		p.token = d['token']
		p.date = d['date']
		p.last_modified = d['last_modified']

		return p

	def __iter__(self):
		yield from map(self.__getattribute__, self.fields)

class Database(dict):
	def __init__(self, filename='../db.pickle'):
		self.filename = filename

		self._initialize_db_if_nonexistent()
		with open(filename, 'rb') as db_file:
			self.update(_pickle.load(db_file))

	def _initialize_db_if_nonexistent(self):
		file = _create_file_if_non_existent(self.filename)
		with file:
			if _get_filesize(file) == 0:
				_pickle.dump({}, file)

	def get_poster(self, id, token=None):
		"""return a Poster object corresponding to the id.
		If token is passed, validate that token against the database.
		If the token is invalid, raise InvalidTokenError"""
		try:
			poster = self[id]
		except KeyError:
			raise InvalidPosterError
		else:
			if poster is None:
				raise PosterDeletedError
			elif poster.validate(token):
				return poster
			else:
				raise InvalidTokenError

	def values(self):
		for poster in super().values():
			if poster is not None:
				yield poster

	def search(self, lat, long, radius, unit):
		for poster in self.values():
			distance = getattr(poster.distance(lat, long), unit)
			if distance <= radius:
				# don't overwrite the .distance method in place
				poster = _copy.deepcopy(poster)
				poster.distance = round(distance, 2)
				poster.unit = unit
				yield poster

	def edit(self, **kwargs):
		id = kwargs['id']
		token = kwargs['token']
		if id in self:
			poster = self.get_poster(id)
		else:
			raise InvalidPosterError

		if poster.validate(token):
			poster.edit(**kwargs)
			self[id] = poster
		else:
			raise InvalidTokenError

		self.save()

	def save(self):
		with open(self.filename, 'wb') as f:
			# not sure why i have to do this
			_pickle.dump(_copy.deepcopy(self), f)

	def __delitem__(self, id):
		self[id] = None
		self.save()

	def add(self, poster):
		if poster.id in self:
			raise PosterExistsError
		self[poster.id] = poster
		self.save()

db = Database()

def create_poster(**kwargs):
	p = Poster(**kwargs)
	db.add(p)
	return p

class InvalidTokenError(Exception):
	pass

class InvalidPosterError(Exception):
	pass

class PosterExistsError(Exception):
	pass

class PosterDeletedError(Exception):
	pass
