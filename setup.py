from setuptools import setup, find_packages

install_requires = [
    "Scrapy>=1.5.0",
    "Flask>=0.10.1",
    "Twisted>=15.4.0",
    "scrapy-user-agents>=0.1.1",
    "six>=1.10.0",
    "funcsigs>=1.0.2"
]

setup(
    name='ArachneServer',
    version='1.0.2',
    author='dmkitui',
    author_email='dmkitui@gmail.com',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    test_suite='arachneserver.tests',
    url='https://github.com/dmkitui/arachneserver',
    license='BSD',
    description='API for Scrapy spiders',
    long_description=open('README.md').read(),
    install_requires=install_requires,
)
