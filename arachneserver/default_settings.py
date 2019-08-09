# This allows scrapy to dynamically assign port to crawler object
TELNETCONSOLE_PORT = None

# Export data to JSON or CSV
EXPORT_PATH = 'exports/'
EXPORT_JSON = False
EXPORT_CSV = False

# Logs can be turned on and off. Default directory is logs/
LOGS = False
LOGS_PATH = 'logs/'


# DEBUG setting for spiders always true
DEBUG = True

# common settings for each spider

DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy_user_agents.middlewares.RandomUserAgentMiddleware': 400,
}

SCRAPY_SETTINGS = {
    'EXTENSIONS': {
        'arachneserver.extensions.ApplicationData': 500
    }
}
