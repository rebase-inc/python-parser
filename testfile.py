# pylint: disable=bad-whitespace, missing-docstring

import os
import sys
import logging
import requests
import cookielib

import json as jsonlib # alias to avoid requests name collision

from contextlib import contextmanager

import spiral.exceptions
from spiral.tools import ProgressWrapper
from spiral.utils import parse_server_error, defaults

LOGGER = logging.getLogger('spiral.webclient')
JSON_LOGGER = logging.getLogger('spiral-json')

# TODO: remove_unicode() is long gone, and json_decode() isn't used anywhere. Okay to remove?
# def json_decode(jstr):
# 	json_obj = json.loads(jstr)
# 	return remove_unicode(json_obj)

def json_encode(jobj):
	return jsonlib.dumps(jobj)

# resource grabbing for pyinstaller
def resource_path(relative):
	try:
		base_path = sys._MEIPASS # pylint: disable=protected-access, no-member
	except AttributeError:
		base_path = os.path.abspath('.')
	return os.path.join(base_path, relative)

def find_cacert():
	cert_path = requests.certs.where()
	if os.path.exists(cert_path):
		return cert_path
	cert_path = resource_path('cacert.pem')
	if os.path.exists(cert_path):
		return cert_path
	else:
		raise spiral.exceptions.SSLCertMissing

class ResourceClient(object):
	def __init__(self, cookie_file, host, port = "443", protocol = None):
		if protocol == None and port == "443":
			protocol = "https"
		if protocol == None:
			protocol = "http"

		self.certfile = find_cacert()
		self.host = host
		self.port = port
		self.protocol = protocol
		self.url = self.protocol + '://' + self.host + ':' + str(self.port)
		self.prefix = self.protocol + "://" + self.host + ":" + str(self.port)
		self.cookie_file = cookie_file
		self.cookies = cookielib.MozillaCookieJar(cookie_file)
		self.session = requests.Session()
		self.adapter = requests.adapters.HTTPAdapter(max_retries=3)
		self.session.mount('http://', self.adapter)
		self.session.mount('https://', self.adapter)
		self.session.cookies = self.cookies
		self.session.headers.update({'X-Requested-With': 'XMLHttpRequest'})
		self.json_headers = {'accept': 'application/json',
						'content-type': 'application/json'}
		try:
			self.cookies.load()
		except IOError:
			self.cookies.save()

	@contextmanager
	def requests_exceptions(self):
		''' translate requests exceptions to spiral exceptions. '''
		try:
			yield
		except requests.exceptions.ConnectionError as exc:
			raise spiral.exceptions.ConnectionError(self.url)
		except requests.exceptions.HTTPError as e:
			parse_server_error(e)
		except requests.exceptions.URLRequired:
			raise spiral.exceptions.URLRequired()
		except requests.exceptions.TooManyRedirects:
			raise spiral.exceptions.TooManyRedirects(self.url)
		except requests.exceptions.Timeout:
			raise spiral.exceptions.Timeout(self.url)

	def get_username(self):
		username = self.get_cookie('userid')
		if username:
			return username
		else:
			raise spiral.exceptions.NotLoggedIn

	def get_cookie(self, name):
		for cookie in self.cookies:
			if cookie.name == name and cookie.domain.startswith(self.host):
				return cookie.value
		return None

	def huge_put(self, path, src):
		''' upload big file, returns response object from requests library '''
		url = self.url + path
		file_obj = ProgressWrapper(open(src, 'rb'))
		with self.requests_exceptions():
			response = self.session.put(
					url,
					data = file_obj,
					timeout = defaults.http_timeout,
					verify = self.certfile)
			LOGGER.debug(response.text)
			response.raise_for_status()

		file_obj.final_print()
		self.session.cookies.save()
		return response

	def huge_get(self, path, extra_headers=None):
		if not extra_headers:
			extra_headers = {}
		url = self.url + path
		with self.requests_exceptions():
			response = self.session.get(
					url,
					stream = True,
					headers = extra_headers,
					timeout = defaults.http_timeout,
					verify = self.certfile)
			LOGGER.debug('Streaming GET from {}'.format(url))
			self.session.cookies.save()
			response.raise_for_status()
			filename = response.headers['Content-disposition'].split('=')[1]

		return (filename, response.raw)

	def get(self, path, json=True, extra_headers=None, log=False, **extra):
		if not extra_headers:
			extra_headers = {}
		url = self.url + path
		headers = dict(list(self.json_headers.items() + extra_headers.items()))
		with self.requests_exceptions():
			response = self.session.get(
					url,
					headers = headers,
					verify = self.certfile,
					timeout = defaults.http_timeout,
					**extra)
			LOGGER.debug('GET from {}'.format(url))
			LOGGER.debug(response.text)
			self.session.cookies.save()
			response.raise_for_status()

		if log:
			LOGGER.debug(response.text)
			JSON_LOGGER.info(response.text)

		if json:
			return response.json()
		else:
			return response.text

	def put(self, path, data, json=True, **extra):
		url = self.url + path
		with self.requests_exceptions():
			response = self.session.put(
					url,
					data = data,
					headers = self.json_headers,
					verify = self.certfile,
					timeout = defaults.http_timeout,
					**extra)
			LOGGER.debug('PUT of {} to {}'.format(data, url))
			LOGGER.debug(response.text)
			self.session.cookies.save()
			response.raise_for_status()

		if json:
			return response.json()
		else:
			return response.text

	def post(self, path, data, json=True, **extra):
		url = self.url + path
		with self.requests_exceptions():
			response = self.session.post(
					url,
					data = json_encode(data),
					verify = self.certfile,
					headers = self.json_headers,
					timeout = defaults.http_timeout,
					**extra)
			LOGGER.debug('POST of {} to {}'.format(data, url))
			LOGGER.debug(response.text)
			self.session.cookies.save()
			response.raise_for_status()

		if json:
			return response.json()
		else:
			return response.text

	def silent_post(self, path, data, **extra):
		try:
			url = self.url + path
			self.session.post(
					url,
					data = json_encode(data),
					verify = self.certfile,
					headers = self.json_headers,
					timeout = defaults.http_timeout,
					**extra)
			self.session.cookies.save()
		except requests.exceptions as e:
			LOGGER.debug(e)

	def delete(self, path, json=True, **extra):
		url = self.url + path
		with self.requests_exceptions():
			response = self.session.delete(
					url,
					headers = self.json_headers,
					verify = self.certfile,
					timeout = defaults.http_timeout,
					**extra)
			LOGGER.debug('DELETE at {}'.format(url))
			LOGGER.debug(response.text)
			self.session.cookies.save()
			response.raise_for_status()

		if json:
			return response.json()
		else:
			return response.text
