import requests
from urllib import parse
import re

class Facebook():

    def __init__(self, config):
        """
            Config is a dict containing: app_id; app_secret
        """
        self.app_id = config['app_id']
        self.app_secret = config['app_secret']
        self.base_url = 'https://graph.facebook.com/v2.5/'
        self.access_token = self._get_access_token()

    def _get_access_token(self):
        url = 'https://graph.facebook.com/v2.5/oauth/access_token?client_id={}&' \
              'client_secret={}&grant_type=client_credentials'.format(self.app_id, self.app_secret)
        access_token = requests.get(url).json()['access_token']
        return access_token

    def _request(self, url, params = {}, method='GET'):
        params['access_token'] = self.access_token
        if method == 'GET':
            r = requests.get(url=url, params=params)
        elif method == 'POST':
            r = requests.post(url=url, params=params)
        else:
            raise TypeError("'Method' should be either POST or GET.")
        return r

    def _get_id_from_username(self, username):
        html = requests.get('https://facebook.com/' + username).text
        id = re.findall(r'fbpage_id=(\d+)', html)[0]
        return id

    def get_object_comments(self, object_id):
        url = self.base_url + object_id + '/comments'
        r = self._request(url).json()
        if 'data' in r:
            comments = r['data']
        else:
            comments = []
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