import os
import sys
import logging
import csv
from flask import Flask
from arachneserver.exceptions import SettingsException, EndpointException
from arachneserver.default_endpoints import list_spiders_endpoint, run_spider_endpoint
from inspect import getmembers, isfunction
from funcsigs import signature
from importlib import import_module

SPIDER_STATUS = {}


def spiders_info(action=None):
    """
    Method to read and load data about spiders that have run or write to file spider statistics of a just completed
    spider run.
    :param action: The options are 'read' for reading spider data from file, or 'write' so as to write to file
    information
    about a spider that has just completed running. Parameters read or written to file are:
        spider_name: name of the spider that has ran.
        last_run: Last time it completed running.
        avg_time: The time the spider took to complete.
        exit_code: The reason the spider completed e.g 'finished' - means it completed well.
        TODO: - Evalutate and document other exit_code 's
    :return: None.
    """
    spider_data_file = os.path.abspath(os.path.dirname(__file__)) + '/spider_data.csv'
    if action == 'read':
        with open(spider_data_file, 'r') as csv_file:
            field_names = ['spider_name', 'last_run', 'avg_time', 'running', 'exit_code']
            reader = csv.DictReader(csv_file, fieldnames=field_names, delimiter='|')
            for row in reader:
                key = row.pop('spider_name', None)
                SPIDER_STATUS[key] = dict(row)

    elif action == 'write':
        with open(spider_data_file, 'w') as csv_file:
            field_names = ['spider_name', 'last_run', 'avg_time', 'running', 'exit_code']
            csv_writer = csv.DictWriter(csv_file, fieldnames=field_names, delimiter='|')
            for spider, spider_data, in SPIDER_STATUS.items():
                spider_data['spider_name'] = spider
                csv_writer.writerow(spider_data)


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


class ArachneServer(Flask):

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
        super(ArachneServer, self).__init__(import_name, **kwargs)
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

        self._init_crawler_process()

        # initialize endpoints for API
        self._init_url_rules()

    def run(self, host=None, port=None, debug=None, **options):
        super(ArachneServer, self).run(host, port, debug, **options)

    def load_config(self):
        """Default settings are loaded first and then overwritten from
        personal `settings.py` file
        """
        self.config.from_object('arachneserver.default_settings')

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
        except KeyError:
            raise SettingsException('SPIDER_SETTINGS missing')
        if not isinstance(spider_settings, list):
            raise SettingsException('SPIDER_SETTINGS must be a dict')

    def _init_url_rules(self):
        """Attach the default endpoints (run spiders and list the spiders
        that are available in the API) and evaluate for all user defined endpoints and attach them.
        """
        # Attach default endpoints first
        self.add_url_rule('/run-spider/<spider_name>', view_func=run_spider_endpoint)
        self.add_url_rule('/', view_func=list_spiders_endpoint)

        all_spiders = self.config['SPIDER_SETTINGS']

        # Evaluate and attach all endpoints for the individual spiders.
        for spider in all_spiders:
            try:
                endpoint_file = spider['endpoint_location']
            except KeyError:
                # No endpoint file specified
                logging.warning('Endpoints for {} not specified.'.format(spider['spider'].upper()))
                continue

            try:
                custom_endpoint_file = import_module(endpoint_file)
                logging.debug('Endpoints for {} loaded'.format(spider['spider'].upper()))
            except ImportError:
                # Specified custom endpoints file could not be loaded
                logging.warning('Specified endpoints file  for {} could not be loaded'.format(spider['spider'].upper()))
                continue

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
        spiders_info(action='read')
