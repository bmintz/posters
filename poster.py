#!/usr/bin/env python3
# encoding: utf-8

from collections import namedtuple as _namedtuple
import copy as _copy
from datetime import datetime as _datetime
import pickle as _pickle

from flask_sqlalchemy import SQLAlchemy
from geopy.exc import GeopyError as _GeopyError
from geopy.distance import distance as _distance
from geopy.geocoders import GoogleV3 as _GoogleV3

from util import config
import util as _util

"""defines poster classes and utilities for interacting with the poster db"""

_geocoder = _GoogleV3(config['api_keys']['google_maps_geocoding'])
_timezone_encoder = _GoogleV3(config['api_keys']['google_maps_timezone'])

db = SQLAlchemy()

class Poster(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(280), nullable=False)
	location = db.Column(db.String(128), nullable=False)
	lat = db.Column(db.Float, db.FetchedValue(), nullable=False)
	long = db.Column(db.Float, db.FetchedValue(), nullable=False)
	text = db.Column(db.Text, nullable=True)
	author = db.Column(db.String(128), nullable=False)
	date = db.Column(
		db.Date,
		server_default=self.now,
		db.FetchedValue(),
		nullable=False
	)
	last_modified = db.Column(
		db.Date,
		server_default=self.now,
		onupdate=self.now,
		db.FetchedValue(),
		nullable=True
	)

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.geocode()

	def geocode(self):
		self.lat, self.long = geocode(self.location)

	def now(self):
		try:
			return _datetime.now(
				tz=_timezone_encoder.timezone(self.lat, self.long)
			)
		except _GeopyError:
			return _datetime.utcnow()

	def geocode(self, location):
		try:
			result = _geocoder.geocode(location)
		except:
			raise InvalidLocationError
		if result is None:
			raise InvalidLocationError
		return result.point[:2]


class InvalidTokenError(Exception):
	pass

class InvalidPosterError(Exception):
	pass

class PosterExistsError(Exception):
	pass

class PosterDeletedError(Exception):
	pass

class InvalidLocationError(Exception):
	pass
