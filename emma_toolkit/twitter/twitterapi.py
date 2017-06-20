import requests
from requests_oauthlib import OAuth1

class Twitter():

    def __init__(self, config):
        """
        Config is a dict containing: consumer_key; consumer_secret;
                                     access_token; access_secret
        """
        self.oauth = OAuth1(config['consumer_key'],
                       config['consumer_secret'],
                       config['access_token'],
                       config['access_secret']
                       )
        self.base_url = 'https://api.twitter.com/1.1'

    def set_auth(self, consumer_key, consumer_secret, access_token, acces_secret):
        self.oauth = OAuth1(consumer_key, consumer_secret, access_token, acces_secret)

    def show_friendship(self, source, target):
        url = self.base_url + '/friendships/show.json'
        params = {'source_screen_name': source,
                  'target_screen_name': target}
        r = self._request(url, params)
        friendship = r.json()
        return {'following': friendship['relationship']['source']['following'],
                'followed': friendship['relationship']['source']['followed_by']}

    def get_followers(self, user, cursor = -1, count = 5000):
        url = self.base_url + '/followers/ids.json'
        params = {'cursor': cursor,
                  'screen_name': user,
                  'count': count}
        r = self._request(url, params)
        user_ids = r.json()
        return user_ids

    def get_friends(self, user, cursor = -1, count = 5000):
        url = self.base_url + '/friends/ids.json'
        params = {'cursor': cursor,
                  'screen_name': user,
                  'count': count}
        r = self._request(url, params)
        user_ids = r.json()
        return user_ids

    def get_friends(self, user, cursor = -1, count = 5000):
        url = self.base_url + '/friends/ids.json'
        params = {'cursor': cursor,
                  'screen_name': user,
                  'count': count}
        r = self._request(url, params)
        user_ids = r.json()
        return user_ids

    def get_user_info(self, users):
        url = self.base_url + '/users/lookup.json'
        if isinstance(users, list):
            method = 'POST'
            if isinstance(users[0], int):
                params = {'user_id': ','.join([str(user) for user in users])}
            else:
                params = {'screen_name': ','.join(users)}
        elif isinstance(users, str):
            method = 'GET'
            params = {'screen_name': users}
        elif isinstance(users, int):
            method = 'GET'
            params = {'user_id': users}
        else:
            raise TypeError("Users should be list, string or int, not {}.".format(str(type(users))))

        r = self._request(url, params, method).json()
        return r

    def get_recent_tweets(self, user, count = 200, include_rts = True):
        url = self.base_url + '/statuses/user_timeline.json'
        if isinstance(user, str):
            params = {'screen_name': user}
        elif isinstance(user, int):
            params = {'user_id': user}
        else:
            raise TypeError("User should be string or int, not {}.".format(str(type(user))))
        if include_rts:
            params['include_rts'] = 1
        else:
            params['include_rts'] = 0
        params['count'] = count
        r = self._request(url, params).json()
        return r

    def follow_user(self, user):
        url = self.base_url + '/friendships/create.json'
        if isinstance(user, str):
            params = {'screen_name': user}
        elif isinstance(user, int):
            params = {'user_id': user}
        else:
            raise TypeError("User should be list or string, not {}.".format(str(type(user))))

        r = self._request(url, params, method="POST").json()
        return r

    def get_rate_limit(self, resources):
        url = self.base_url + '/application/rate_limit_status.json'
        if isinstance(resources, list):
            params = {'resources': ','.join(resources)}
        elif isinstance(resources, str):
            params = {'resources': resources}
        else:
            raise TypeError("Resources should be list or string, not {}.".format(str(type(resources))))

        r = self._request(url, params).json()
        return r['resources']

    def create_chunks(self, l, n):
        """
        :param l: array
        :param n: size of every chunk
        :return: chunks of l of size n
        """
        for i in range(0, len(l), n):
            yield l[i:i+n]

    def _request(self, url, params, method='GET'):
        if method == 'GET':
            r = requests.get(url=url, params=params, auth=self.oauth)
        elif method == 'POST':
            r = requests.post(url=url, params=params, auth=self.oauth)
        else:
            raise TypeError("'Method' should be either POST or GET.")
        return r
