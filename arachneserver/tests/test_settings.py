SPIDER_SETTINGS = [{
    'endpoint': 'abc',
    'location': 'spiders.abc.ABC',
    'endpoint_location': 'spiders.abc.ABC_endpoint',
    'spider': 'ABC',
    'scrapy_settings': {
        'TELNETCONSOLE_PORT': 2020
    }
}, {
    'endpoint': 'pqr',
    'location': 'spiders.pqr.PQR',
    #'endpoint_location': 'spiders.pqr.PQR_endpoint',
    'spider': 'PQR',
}]

SECRET_KEY = 'secret_test_key'
TESTING = True
SCRAPY_SETTINGS = {
    'TELNETCONSOLE_PORT': 3030
}
