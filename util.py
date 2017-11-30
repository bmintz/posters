#!/usr/bin/env python3

import base64
import os

DEFAULT_ENTROPY = 32  # number of bytes to return by default

def token_bytes(nbytes=None):
	"""Return a random byte string containing *nbytes* bytes.

	If *nbytes* is ``None`` or not supplied, a reasonable
	default is used.

	>>> token_bytes(16)  #doctest:+SKIP
	b'\\xebr\\x17D*t\\xae\\xd4\\xe3S\\xb6\\xe2\\xebP1\\x8b'

	"""
	if nbytes is None:
		nbytes = DEFAULT_ENTROPY
	return os.urandom(nbytes)


def token_urlsafe(nbytes=None):
	"""Return a random URL-safe text string, in Base64 encoding.

	The string has *nbytes* random bytes.  If *nbytes* is ``None``
	or not supplied, a reasonable default is used.

	>>> token_urlsafe(16)  #doctest:+SKIP
	'Drmhze6EPcv0fN_81Bj-nA'

	"""
	tok = token_bytes(nbytes)
	return base64.urlsafe_b64encode(tok).rstrip(b'=').decode('ascii')
