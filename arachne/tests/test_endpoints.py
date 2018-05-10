"""
Testing the endpoints called with the API
"""

import json
from mock import patch
from arachne.tests.BaseFlaskApp import BaseFlaskApp
from arachne.exceptions import EndpointException
from arachne.flaskapp import endpoint_evaluator


class TestFlaskEndpoints(BaseFlaskApp):

    def test_list_spiders_endpoint(self):
        resp = self.client.get('/')
        expected_resp = {
            'endpoints': {
                'abc': 'http://localhost/run-spider/abc',
                'pqr': 'http://localhost/run-spider/pqr'
            }
        }
        self.assertTrue(resp.data, expected_resp)

    @patch('arachne.endpoints.start_crawler')
    def test_run_spider_endpoint(self, mock_start_crawler):
        resp = self.client.get('/run-spider/abc')
        self.assertTrue(mock_start_crawler.called)
        client_config = self.client.application.config
        mock_start_crawler.assert_called_once_with('spiders.abc.ABC.ABC',
                                                   client_config,
                                                   {'TELNETCONSOLE_PORT': 2020})

        self.assertEquals(json.loads(resp.data),
                          {'home': 'http://localhost/',
                           'status': 'running',
                           'spider_name': 'abc'})

        resp = self.client.get('/run-spider/xyz')
        self.assertEquals(404, resp.status_code)

    def test_custom_endpoints(self):
        """
        Test the custom endpoints functionality
        """

        from arachne.tests.custom_endpoints import endpoint_invalid_method
        with self.assertRaises(EndpointException) as context:
            endpoint_evaluator(endpoint_invalid_method)

        self.assertTrue('Supplied methods for "endpoint_invalid_method" endpoint is invalid.' in str(context.exception))

    def test_custom_endpoint_no_url(self):

        from arachne.tests.custom_endpoints import endpoint_no_url
        with self.assertRaises(EndpointException) as context:
            endpoint_evaluator(endpoint_no_url)

        self.assertIn('Url for endpoint "endpoint_no_url" not supplied.', str(context.exception))

    def test_custom_endpoint_invalid_url(self):

        from arachne.tests.custom_endpoints import endpoint_invalid_url
        with self.assertRaises(EndpointException) as context:
            endpoint_evaluator(endpoint_invalid_url)

        self.assertEqual('Url for endpoint "endpoint_invalid_url" is not a string', str(context.exception))

    def test_custom_endpoint_default_method(self):

        from arachne.tests.custom_endpoints import endpoint_no_methods_supplied
        _, methods = endpoint_evaluator(endpoint_no_methods_supplied)

        self.assertEqual(methods, ['GET'])
