import requests
from urllib import parse
import re

class Facebook():

    def __init__(self, config):
        """
            Config is a dict containing: app_id; app_secret; page_access_token
        """
        self.app_id = config['app_id']
        self.app_secret = config['app_secret']
        self.base_url = 'https://graph.facebook.com/'
        self.access_token = self._get_access_token()
        if 'page_access_token' in config:
            self.page_access_token = config['page_access_token']
        else:
            self.page_access_token = ''

    def _get_access_token(self):
        url = 'https://graph.facebook.com/v2.5/oauth/access_token?client_id={}&' \
              'client_secret={}&grant_type=client_credentials'.format(self.app_id, self.app_secret)
        access_token = requests.get(url).json()['access_token']
        return access_token

    def _request(self, url, params = {}, method='GET', access_token='user'):
        if access_token == 'user':
            params['access_token'] = self.access_token
        elif access_token == 'page':
            if not self.page_access_token:
                print('Geen page access token!')
                raise Exception
            params['access_token'] = self.page_access_token
        if method == 'GET':
            r = requests.get(url=url, params=params)
        elif method == 'POST':
            r = requests.post(url=url, params=params)
        else:
            raise TypeError("'Method' should be either POST or GET.")
        return r

    def _get_id_from_username(self, username):
        html = requests.get('https://facebook.com/' + username).text
        result = re.findall(r'fbpage_id=(\d+)', html)
        if result:
            id = result[0]
        else:
            id = ''
        return id

    def set_page_access_token(self, page_access_token):
        self.page_access_token = page_access_token

    def get_object_comments(self, object_id, user_info = False):
        url = self.base_url + object_id + '/comments'
        r = self._request(url).json()
        if 'data' in r:
            comments = r['data']
        else:
            comments = []
        if user_info:
            for c in comments:
                user_info = self.get_user_info(c['from']['id'])
                c['from']['metadata'] = user_info['metadata']
        return comments

    def get_user_id_from_url(self, url):
        parsed_url = parse.urlparse(url)
        path = parsed_url.path
        query = parsed_url.query
        try:
            if 'post' in path:
                user_id = re.findall(r'/(.+?)/posts/\d+', path)[0]
                try:
                    int(user_id)
                except ValueError:
                    user_id = self._get_id_from_username(user_id)
            elif 'video' in path:
                user_id = re.findall(r'/(.+?)/videos/\d+', path)[0]
            elif 'photo' in path:
                result = re.findall(r'v=(\d+)|fbid=(\d+)', query)[0]
                user_id = result[0] if result[0] else result[1]
            elif 'permalink' in path:
                user_id = re.findall(r'story_fbid=(\d+)&', query)[0]
            elif 'events' in path:
                user_id = re.findall(r'events/(\d+)', path)[0]
            else:
                raise ValueError('URL nog niet in systeem: {}'.format(url))
        except IndexError:
            raise IndexError('URL nog niet in systeem: {}'.format(url))
        return user_id

    def get_post_id_from_url(self, url):
        parsed_url = parse.urlparse(url)
        path = parsed_url.path
        query = parsed_url.query
        try:
            if 'post' in path:
                post_ids = re.findall(r'/(.+?)/posts/(\d+)', path)
                try:
                    int(post_ids[0][0])
                    post_id = str(post_ids[0][0]) + '_' + str(post_ids[0][1])
                except ValueError:
                    post_id = ''
            elif 'video' in path:
                post_ids = re.findall(r'/(.+?)/videos/(\d+)', path)
                post_id = str(post_ids[0][0]) + '_' + str(post_ids[0][1])
            elif 'photo' in path:
                post_ids = re.findall(r'v=(\d+)|fbid=(\d+)', query)
                post_id = str(post_ids[0][0]) + '_' + str(post_ids[0][1])
            elif 'permalink' in path:
                post_id = re.findall(r'story_fbid=(\d+)&', query)[0]
            elif 'events' in path:
                post_id = re.findall(r'events/(\d+)', path)[0]
            else:
                raise ValueError('URL nog niet in systeem: {}'.format(url))
        except IndexError:
            raise IndexError('URL nog niet in systeem: {}'.format(url))
        return post_id

    # TODO foutmelding: 'Unsupported get request. Object with ID 317412078342460 does not exist' --> Ondervangen

    def get_page_access_token(self, page_id):
        url = "https://graph.facebook.com/" + str(page_id)
        params = {'fields': 'access_token'}
        r = self._request(url, params)
        return r

    def get_long_lived_page_access_token(self, page_access_token):
        url = 'https://graph.facebook.com/oauth/access_token?client_id={}&client_secret={}&grant_type=' \
              'fb_exchange_token&fb_exchange_token={}'.format(self.app_id, self.app_secret, page_access_token)
        r = self._request(url)
        return r

    def get_page_feed(self, page_id):
        url = self.base_url + str(page_id) + '/feed'
        r = self._request(url, access_token='page')
        return r

    def get_object_insights(self, object_id, metrics):
        url = self.base_url + str(object_id) + '/insights'
        params = {'metric': ','.join(metrics), 'period': 'days_28'}
        r = self._request(url, access_token='page', params=params)
        return r

    def get_user_info(self, user_id):
        url = self.base_url + user_id
        r = self._request(url, params = {'metadata': 1}).json()
        return r

    def search(self, query, type):
        url = self.base_url + 'search'
        params = {'q': query, 'type': type}
        r = self._request(url, params).json()
        return r