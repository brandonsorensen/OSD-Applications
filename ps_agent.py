"""
This module servers as an interface for querying the PowerSchool
database. It defines a function obtaining an PowerSchool token
from the environment and a class that uses said token to fetch
a query from a given URL. Additionally, there are four
:class:`PowerQuery` objs that simply call the four PowerQueries
available to the Apex plugin. In practice, these are the functions that
compose the API.

The :data:`course2program_code`, aptly named, maps a course code as
defined in the documentation provided by Apex Learning to their
respective program codes.
"""

import json
import logging
import os
import sys
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

import requests


course2program_code = {
    616: 'Z1707458',
    615: 'Z7250853',
    501: 'Z9065429',
    601: 'Z1001973'
}


class PowerQuery(object):
    """
    Represents a PowerQuery call to the PowerSchool server. A
    PowerQuery is a custom SQL statement that is defined in by a
    PowerSchool plugin XML file. Four are defined for the Apex Learning
    Plugin, and can be accessed by appending the following four key
    words to PowerSchool URL + :data:`BASE_QUERY_URL` combination:

        - classrooms
        - enrollment
        - students
        - teachers

    These stock PowerQuery objects are defined in this :mod:`ps_agent`
    module.

    :cvar BASE_QUERY_URL: the base URL schema for location the Apex
        PowerQueries.
    """

    PS_URL = 'https://powerschool.sd351.k12.id.us/'
    BASE_QUERY_URL = '/ws/schema/query/com.classchoice.school.'

    def __init__(self, url_ext, description=None):
        # type: (str, str)
        """
        :param str url_ext: the extension that, appended to the `PS_URL`
            environment variable and `BASE_URL` as defined above,
            composes the URL
        """
        self.url_ext = url_ext
        if description is not None:
            self.__doc__ = description

    def fetch(self, page_size=0):
        # type: (int) -> dict
        """
        Obtains an access token and calls a PowerQuery at a given url,
        limiting it to `page_size` results.

        :param int page_size: how many results to return, 0 = all
        :raises PSEmptyQueryException: when no results are returned
        :return: the JSON object returned by the PowerQuery
        """
        logger = logging.getLogger(__name__)
        logger.debug('Fetching PowerQuery with extension ' + str(self.url_ext))
        token = get_ps_token()
        header = get_header(token,
                            custom_args={'Content-Type': 'application/json'})
        payload = {'pagesize': page_size}
        url = urljoin(self.PS_URL, self.BASE_QUERY_URL + self.url_ext)

        r = requests.post(url, headers=header, params=payload)
        logger.debug('PowerQuery returns with status ' + str(r.status_code))
        try:
            return r.json()['record']
        except KeyError as e:
            if e.args[0] == 'record':
                raise PSEmptyQueryException(url)
            raise e

    def __call__(self, page_size=0):
        # type: (int) -> dict
        """Calls the fetch method."""
        return self.fetch(page_size=page_size)


fetch_sections = PowerQuery('sections')
fetch_students = PowerQuery('students')
fetch_all_courses = PowerQuery('current_courses')


def get_ps_token():
    # type: () -> str
    """
    Gets the PowerSchool access token from the PowerSchool server using
    the following environment variables:

        - PS_CLIENT_ID: the given client ID for the PowerSchool plugin
        - PS_CLIENT_SECRET: the secret code

    :return: an access token for the PowerSchool server
    """
    header = {
        'Content-Type': "application/x-www-form-urlencoded;charset=UTF-8'"
    }
    cred_path = os.path.join(get_script_path(), 'powerschool-credentials.json')
    if not os.path.isfile(cred_path):
        raise EnvironmentError('PowerSchool credentials are not in the '
                               'environment.')
    creds = json.load(open(cred_path, 'r'))
    url = urljoin(PowerQuery.PS_URL, '/oauth/access_token')

    payload = {
        'grant_type': 'client_credentials',
        'client_id': creds['PS_CLIENT_ID'],
        'client_secret': creds['PS_CLIENT_SECRET']
    }

    r = requests.post(url, headers=header, data=payload)
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        raise PSNoConnectionError()

    return r.json()['access_token']


def get_header(token, custom_args=None):
    # type: (str, dict) -> dict
    header = {
        'Authorization': 'Bearer {}'.format(token),
        'Accept': 'application/json'
    }

    if custom_args is not None:
        header.update(custom_args)
    return header


def get_script_path():
    try:
        return os.path.dirname(os.path.realpath(__file__))
    except NameError:
        return os.path.dirname(os.path.realpath(sys.argv[0]))


def flatten_ps_json(json_obj):
    # type: (dict) -> dict
    """Takes the 3D dict returned by PowerSchool and flattens it into 1D."""
    flattened = {}
    for table in json_obj['tables'].values():
        flattened.update(table)
    return flattened


class PSException(Exception):

    def __str__(self):
        return 'An unexpected error occurred when attempting to interface' \
               ' with PowerSchool.'


class PSEmptyQueryException(PSException):

    def __init__(self, url):
        self.url = url

    def __str__(self):
        return 'Query to URL "{}" returned no results.'.format(self.url)


class PSNoConnectionError(PSException):

    def __str__(self):
        return 'Could not establish connection with PowerSchool server.'
