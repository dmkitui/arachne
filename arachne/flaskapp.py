import os
import sys
from flask import Flask
from scrapy import version_info as SCRAPY_VERSION
from arachne.exceptions import SettingsException, EndpointException
from arachne.endpoints import list_spiders_endpoint, run_spider_endpoint
from inspect import getmembers, isfunction
from funcsigs import signature


def endpoint_evaluator(endpoint):
    """
    Function to evaluate endpoint functions and and return the url and methods if they comply
    :param endpoint: The endpoint function to be allowed.
    :return: url and methods specified in the function
    """
    args = signature(endpoint).parameters

    try:
        url = args['url'].default
    except KeyError:
        raise EndpointException('Url for endpoint "{}" not supplied.'.format(endpoint.__name__))

    if not isinstance(url, str):
        raise EndpointException('Url for endpoint "{}" is not a string'.format(endpoint.__name__))

    try:
        methods = args['methods'].default
    except KeyError:
        # default method 'GET' is applied.
        methods = ['GET']

    allowed_methods = ['PUT', 'GET', 'POST', 'DELETE', 'PATCH']
    for method in methods:
        if method not in allowed_methods:
            raise EndpointException('Supplied methods for "{}" endpoint is invalid.'
                                    'Allowed methods are PUT, GET, POST, DELETE, PATCH'.format(endpoint.__name__))

    return url, methods


class Arachne(Flask):

    def __init__(self, import_name=__package__,
                 settings='settings.py', **kwargs):
        """Initialize the flask app with the settings variable. Load config
        from the settings variable and test if the all the
        directories(for exports & logs) exists. Finally bind the endpoints for
        the flask application to control the spiders

        .. version 0.5.0:
            Initialize Flask config with `CRAWLER_PROCESS` object if scrapy
            version is 1.0.0 or greater
        """
        super(Arachne, self).__init__(import_name, **kwargs)
        self.settings = settings

        self.load_config()
        self.validate_spider_settings()

        # create directories
        self.check_dir(self.config['EXPORT_JSON'],
                       self.config['EXPORT_PATH'],
                       'json/')
        self.check_dir(self.config['EXPORT_CSV'],
                       self.config['EXPORT_PATH'],
                       'json/')
        self.check_dir(self.config['LOGS'], self.config['LOGS_PATH'], '')

        # from scrapy's version_info initialize Flask app
        # for version before 1.0.0 you don't need to init crawler_process
        if SCRAPY_VERSION >= (1, 0, 0):
            self._init_crawler_process()

        # initialize endpoints for API
        self._init_url_rules()

    def run(self, host=None, port=None, debug=None, **options):
        super(Arachne, self).run(host, port, debug, **options)

    def load_config(self):
        """Default settings are loaded first and then overwritten from
        personal `settings.py` file
        """
        self.config.from_object('arachne.default_settings')

        if isinstance(self.settings, dict):
            self.config.update(self.settings)
        else:
            if os.path.isabs(self.settings):
                pyfile = self.settings
            else:
                abspath = os.path.abspath(os.path.dirname(sys.argv[0]))
                pyfile = os.path.join(abspath, self.settings)
            try:
                self.config.from_pyfile(pyfile)
            except IOError:
                # assume envvar is going to be used exclusively
                pass
            except:
                raise

        # overwrite settings with custom environment variable
        envvar = 'ARACHNE_SETTINGS'
        if os.environ.get(envvar):
            self.config.from_envvar(envvar)

    def check_dir(self, config_name, export_path, folder):
        """Check if the directory in the config variable exists
        """
        if config_name:
            cwd = os.getcwd()
            export_dir = cwd + '/' + export_path + folder
            if not os.path.exists(export_dir):
                raise SettingsException('Directory missing ', export_dir)

    def validate_spider_settings(self):
        try:
            spider_settings = self.config['SPIDER_SETTINGS']
        except:
            raise SettingsException('SPIDER_SETTINGS missing')
        if not isinstance(spider_settings, list):
            raise SettingsException('SPIDER_SETTINGS must be a dict')

    def _init_url_rules(self):
        """Attach the endpoints to run spiders and list the spiders
        that are available in the API
        """
        self.add_url_rule('/run-spider/<spider_name>', view_func=run_spider_endpoint)
        self.add_url_rule('/', view_func=list_spiders_endpoint)

        try:
            import custom_endpoints as custom_endpoint_file
        except ImportError:
            # No custom endpoints file specified
            return

        self.add_custom_endpoints(custom_endpoint_file)

    def add_custom_endpoints(self, custom_endpoint_file):
        """
        Method to add user defined endpoints if available. User defined endpoints are to be specified in a file
        called 'custom_endpoints.py' in the root directory. The method definitions are to be in the format:
            def method_name(**args, url=endpoint_url, method=endpoint_method)
        where:
            endpoint_url: A string representing the endpoint url
            endpoint_method: list containing allowed methods. If none are provided, the endpoint method defaults to GET.
        :return: None.
        """

        endpoints = (fn for fn in getmembers(custom_endpoint_file) if
                     isfunction(fn[1]) and fn[1].__module__ == custom_endpoint_file.__name__)
        for endpoint in endpoints:
            if callable(endpoint[1]):
                url, methods = endpoint_evaluator(endpoint[1])
                self.add_url_rule(url, view_func=endpoint[1], methods=methods)

    def _init_crawler_process(self):
        from scrapy.crawler import CrawlerProcess
        self.config['CRAWLER_PROCESS'] = CrawlerProcess()