ArachneServer
==============
[![Build Status](https://travis-ci.org/dmkitui/arachneserver.svg?branch=master)](https://travis-ci.org/dmkitui/arachneserver)
[![Coverage Status](https://coveralls.io/repos/github/dmkitui/arachneserver/badge.svg?branch=master)](https://coveralls.io/github/dmkitui/arachneserver?branch=master)
[![Maintainability](https://api.codeclimate.com/v1/badges/637b135299638812096d/maintainability)](https://codeclimate.com/github/dmkitui/arachneserver/maintainability)

ArachneServer provides a wrapper around your scrapy ``Spider`` object to run them through a flask app. All you have to do is customize ``SPIDER_SETTINGS`` in the settings file.


Installation
============
You can install **ArachneServer** from pip

	pip install ArachneServer


Sample settings
===============
This is sample settings file for spiders in your project. The settings file should be called **settings.py** in the root of your project for **ArachneServer** to find it and looks like this::

	# settings.py file
	SPIDER_SETTINGS = [
		{
			'endpoint': 'dmoz',
			'location': 'spiders.DmozSpider',
			'endpoints_location: 'spiders.DmozSpider_endpoints'
			'spider': 'DmozSpider'    
		}
	]

Usage
=====
It looks very similar to a flask app but since **Scrapy** depends on the python **twisted** package, we need to run our flask app with **twisted**::

	from twisted.web.wsgi import WSGIResource
	from twisted.web.server import Site
	from twisted.internet import reactor
	from arachneserver import ArachneServer

	app = ArachneServer(__name__)

	resource = WSGIResource(reactor, reactor.getThreadPool(), app)
	site = Site(resource)
	reactor.listenTCP(8080, site)

	if __name__ == '__main__':
		reactor.run()

Endpoints
=========

Two default endpoints are provided for every spider:
   1. **'/'** - List all spiders.
   2. **'/run-spider/<spider_name>'** - To run the specified spider.

Specify additional endpoints for each spider and update the respective SPIDER_SETTINGS dictionary's `endpoints_location` to point to the correct path to the endpoints file.

