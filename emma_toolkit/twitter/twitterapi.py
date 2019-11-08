import requests
from requests_oauthlib import OAuth1
import math
import time
import re
import datetime

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
        self.rate_limits = {}

    def set_auth(self, consumer_key, consumer_secret, access_token, acces_secret):
        self.oauth = OAuth1(consumer_key, consumer_secret, access_token, acces_secret)

    def show_friendship(self, source, target):
        url = self.base_url + '/friendships/show.json'
        params = {'source_screen_name': source,
                  'target_screen_name': target}
        # TODO rate limits inbouwen
        r = self._request(url, params)
        friendship = r.json()
        return {'following': friendship['relationship']['source']['following'],
                'followed': friendship['relationship']['source']['followed_by']}

    def get_followers(self, user, include_user_ids = None, cursor = -1, count = 5000, iterate = True, verbose = False):
        if '/followers/ids' not in self.rate_limits:
            self.rate_limits['/followers/ids'] = self.get_rate_limit('followers')['followers']['/followers/ids']
        if self.rate_limits['/followers/ids']['remaining'] == 0:
            self._wait('/followers/ids', verbose)
        follower_ids = []
        url = self.base_url + '/followers/ids.json'
        params = {'cursor': cursor,
                  'count': count}
        if type(user) == str:
            params['screen_name'] = user
        elif type(user) == int:
            params['user_id'] = user
        else:
            raise TypeError("'user' must be str or int, not {}".format(type(user)))
        r = self._request(url, params)
        self.rate_limits['/followers/ids']['remaining'] -= 1
        user_ids = r.json()
        if include_user_ids:
            followers_to_include = [id for id in user_ids['ids'] if id in include_user_ids]
        else:
            followers_to_include = user_ids['ids']
        follower_ids += followers_to_include
        while 'next_cursor' in user_ids and user_ids['next_cursor'] != 0 and iterate:
            if self.rate_limits['/followers/ids']['remaining'] == 0:
                self._wait('/followers/ids', verbose)
            params['cursor'] = user_ids['next_cursor']
            r = self._request(url, params)
            self.rate_limits['/followers/ids']['remaining'] -= 1
            user_ids = r.json()
            if include_user_ids:
                followers_to_include = [id for id in user_ids['ids'] if id in include_user_ids]
            else:
                followers_to_include = user_ids['ids']
            follower_ids += followers_to_include
        return follower_ids

    def get_friends(self, user, cursor = -1, count = 5000, iterate = True, verbose = False):
        if '/friends/ids' not in self.rate_limits:
            self.rate_limits['/friends/ids'] = self.get_rate_limit('friends')['friends']['/friends/ids']
        if self.rate_limits['/friends/ids']['remaining'] == 0:
            self._wait('/friends/ids', verbose)
        friend_ids = []
        url = self.base_url + '/friends/ids.json'
        params = {'cursor': cursor,
                  'screen_name': user,
                  'count': count}
        r = self._request(url, params)
        self.rate_limits['/friends/ids']['remaining'] -= 1
        user_ids = r.json()
        friend_ids += user_ids['ids']
        while 'next_cursor' in user_ids and user_ids['next_cursor'] != 0 and iterate:
            if self.rate_limits['/friends/ids']['remaining'] == 0:
                self._wait('/friends/ids', verbose)
            params['cursor'] = user_ids['next_cursor']
            r = self._request(url, params)
            self.rate_limits['/friends/ids']['remaining'] -= 1
            user_ids = r.json()
            friend_ids += user_ids['ids']
        return friend_ids

    def get_user_info(self, users, verbose = False):
        if '/users/lookup' not in self.rate_limits:
            self.rate_limits['/users/lookup'] = self.get_rate_limit('users')['users']['/users/lookup']
        if self.rate_limits['/users/lookup']['remaining'] == 0:
            self._wait('/users/lookup', verbose)
        url = self.base_url + '/users/lookup.json'
        user_info = []
        if isinstance(users, list):
            method = 'POST'
            if len(users) > 100:
                chunks = self._create_chunks(users, 100)
            else:
                chunks = [users]
            for chunk in chunks:
                if self.rate_limits['/users/lookup']['remaining'] == 0:
                    self._wait('/users/lookup', verbose)
                if isinstance(users[0], int):
                    params = {'user_id': ','.join([str(user) for user in chunk])}
                else:
                    params = {'screen_name': ','.join(chunk)}
                r = self._request(url, params, method).json()
                self.rate_limits['/users/lookup']['remaining'] -= 1
                user_info += r
        elif isinstance(users, str):
            method = 'GET'
            params = {'screen_name': users}
            r = self._request(url, params, method).json()
            self.rate_limits['/users/lookup']['remaining'] -= 1
            user_info += r
        elif isinstance(users, int):
            method = 'GET'
            params = {'user_id': users}
            r = self._request(url, params, method).json()
            self.rate_limits['/users/lookup']['remaining'] -= 1
            user_info += r
        else:
            raise TypeError("Users should be list, string or int, not {}.".format(str(type(users))))
        return user_info

    def get_recent_tweets(self, user, count = 3200, start_date = None, include_rts = True, verbose=False):
        if '/statuses/user_timeline' not in self.rate_limits:
            self.rate_limits['/statuses/user_timeline'] = self.get_rate_limit('statuses')['statuses']['/statuses/user_timeline']
        if self.rate_limits['/statuses/user_timeline']['remaining'] == 0:
            self._wait('/statuses/user_timeline', verbose)
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
        params['count'] = 200 if count >= 200 else count
        iterations = int(math.ceil(count / 200))
        if start_date:
            start_timestamp = datetime.datetime.timestamp(start_date)
        else:
            start_timestamp = 0
        all_tweets = []
        date_format = '%a %b %d %H:%M:%S %z %Y'
        for i in range(iterations):
            if self.rate_limits['/statuses/user_timeline']['remaining'] == 0:
                self._wait('/statuses/user_timeline', verbose)
            r = self._request(url, params).json()
            self.rate_limits['/statuses/user_timeline']['remaining'] -= 1
            if 'error' in r:
                error = r['error']
            elif 'errors' in r:
                error = r['errors'][0]['message']
            else:
                error = None
            if error:
                if verbose:
                    print("Error for user {}: '{}'. Returning nothing.".format(user, error))
                return []
            if len(r) == 0:
                if verbose:
                    print("No tweets for user {}. Returning nothing.".format(user))
                return []
            all_tweets += r
            params['max_id'] = r[-1]['id'] - 1
            last_date = r[-1]['created_at']
            last_timestamp = datetime.datetime.timestamp(datetime.datetime.strptime(last_date, date_format))
            if last_timestamp < start_timestamp or len(r) < params['count']:
                break
        tweets = []
        for tweet in all_tweets:
            timestamp = datetime.datetime.timestamp(datetime.datetime.strptime(tweet['created_at'], date_format))
            if timestamp > start_timestamp:
                tweets.append(tweet)
        return tweets

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

    def search_users(self, query, users_to_return=20, verbose=False):
        if '/users/search' not in self.rate_limits:
            self.rate_limits['/users/search'] = self.get_rate_limit('users')['users']['/users/search']
        if self.rate_limits['/users/search']['remaining'] == 0:
            self._wait('/users/search', verbose)
        url = self.base_url + '/users/search.json'
        count = 20
        user_info = []
        params = {'q': query,
                  'count': count,
                  'page': 1}
        iterations = int(math.ceil(users_to_return / 20))
        for i in range(iterations):
            if self.rate_limits['/users/search']['remaining'] == 0:
                self._wait('/users/search', verbose)
            params['page'] += 1
            r = self._request(url, params, method="GET").json()
            user_info += r
            self.rate_limits['/users/search']['remaining'] -= 1
            if len(r) < count:
                break
        return user_info

    def get_follow_network(self, user_screen_names, verbose = False, get_time_estimate = False):
        users_info = self.get_user_info(user_screen_names, verbose=verbose)
        if get_time_estimate:
            amount_of_followers = [user['followers_count'] for user in users_info]
            amount_of_iterations = int(sum([math.ceil(x / 5000) for x in amount_of_followers]))
            time_to_collect_network = str(datetime.timedelta(minutes=amount_of_iterations))[:-3]
            eta = datetime.datetime.now() + datetime.timedelta(minutes=amount_of_iterations)
            print('Dit netwerk duurt ongeveer {} uur om binnen te halen ({})'.format(time_to_collect_network, eta))
        user_ids = [user['id'] for user in users_info]
        edges = []
        for user_id in user_ids:
            follower_ids = self.get_followers(user_id, include_user_ids=user_ids, verbose=verbose)
            for follower_id in follower_ids:
                edges.append((follower_id, user_id))
        return({'nodes': users_info, 'edges': edges})

    def get_mentions_network(self, tweets, author_col, tweet_col, method = 'mentions', verbose = False):
        """
        :param tweets: Pandas Dataframe
        :param author_col: String
        :param tweet_col: String
        :param method: String: ['mentions', 'retweets', 'mentions_and_retweets']
        :return: Dict: {nodes, edges}
        """
        tweets['is_retweet'] = tweets[tweet_col].str.startswith('RT @')
        if method == 'mentions':
            tweets = tweets[~tweets['is_retweet']]
            exp = re.compile(r'@(\w+)')
        elif method == 'retweets':
            tweets = tweets[tweets['is_retweet']]
            exp = re.compile(r'^RT @(\w+)')
        elif method == 'mentions_and_retweets':
            exp = re.compile(r'@(\w+)')
        else:
            raise ValueError('Parameter "method" should be one of [mentions, retweets, mentions_and_retweets]')
        tweets['mentions'] = tweets[tweet_col].apply(lambda x: re.findall(exp, x))
        mentions_per_auteur = tweets.groupby(author_col)['mentions'].sum()
        edges = []
        alle_tweeps = []
        for index, mentions in mentions_per_auteur.iteritems():
            source = index
            targets = mentions
            for target in targets:
                edges.append((source.lower(), target.lower()))
                alle_tweeps.append(source.lower())
                alle_tweeps.append(target.lower())

        alle_tweeps = list(set(alle_tweeps))
        nodes = self.get_user_info(alle_tweeps, verbose=verbose)
        return({'nodes': nodes, 'edges': edges})

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

    def _create_chunks(self, l, n):
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

    def _wait(self, resource, verbose = False):
        # Rate limit opnieuw checken voor de zekerheid
        main_resource = re.findall(r'/(\w+)/', resource)[0]
        new_rate_limit = self.get_rate_limit(main_resource)[main_resource][resource]
        self.rate_limits[resource] = new_rate_limit
        rate_limit_reset = self.rate_limits[resource]['reset']
        now = time.time()
        time_to_sleep = rate_limit_reset - now + 5
        resume = datetime.datetime.now() + datetime.timedelta(seconds=time_to_sleep)
        if verbose:
            print('{}: Rate limit voor {}. Wachten tot {}.'.format(
                time.strftime('%H:%M:%S'), resource, resume.strftime('%H:%M:%S')))
        if time_to_sleep < 0:
            time_to_sleep = 900
        time.sleep(time_to_sleep)
        new_rate_limit = self.get_rate_limit(main_resource)[main_resource][resource]
        self.rate_limits[resource] = new_rate_limit
        if verbose:
            print('{}: We gaan verder met data binnenhalen via {}.'.format(
                time.strftime('%H:%M:%S'), resource))