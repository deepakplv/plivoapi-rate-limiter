"""
Implementation of various decorators fot rate-limiting
"""
from abc import ABCMeta, abstractmethod
import redis
from hashlib import sha1


class RESTResponse(object):
    """PlivoAPI expects response in this format"""
    def __init__(self, code, content, method):
        self.code = code
        self.content = content or {}
        self.method = method

    def __str__(self):
        return '<RESTResponse %s %s>' % (str(self.method), str(self.code))


class RateLimiter(object):
    """
    Base class for rate-limit decorators.
    window_size: In seconds
    max_request: Count of allowed requests in the window
    """
    __metaclass__ = ABCMeta

    def __init__(self, window_size, max_request, redis_pool=None):
        self.window_size = window_size
        self.max_request = max_request
        self.redis_pool = redis_pool
        super(RateLimiter, self).__init__()

    def __call__(self, func):
        def wrapper(rest_handler, auth_session, *args, **kwargs):
            # api_name contains the relative URL of the API(without queryparams) which also contains the AUTHID
            key = str(auth_session.api_name)
            try:
                apply_rate_limit = self.has_limit_exceeded(key, self.redis_pool)
            except:
                apply_rate_limit = False
            if apply_rate_limit:
                return RESTResponse(
                    code=429,
                    content={'error': "too many requests"},
                    method="GET"
                )
            return func(rest_handler, auth_session, *args, **kwargs)
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    @abstractmethod
    def has_limit_exceeded(self, key, redis_pool):
        pass


class FixedWindowRateLimiter(RateLimiter):
    """
    This rate limiter blocks request if number of requests exceed allowed requests in the defined
    time-window till the window resets.
    To avoid race condition, using a lua script to increment key and set ttl(only first time).This is
    documented here: https://redis.io/commands/incr#pattern-rate-limiter-2
    """
    INCREMENT_SCRIPT = b"""
        local current
        current = redis.call("incr",KEYS[1])
        if tonumber(current) == 1 then
            redis.call("expire",KEYS[1],ARGV[1])
        end
        return current
    """
    INCREMENT_SCRIPT_HASH = sha1(INCREMENT_SCRIPT).hexdigest()

    def has_limit_exceeded(self, key, redis_pool):
        redis_conn = redis.Redis(connection_pool=redis_pool)
        try:
            count = redis_conn.evalsha(
                self.INCREMENT_SCRIPT_HASH, 1, key, self.window_size)
        except redis.exceptions.NoScriptError:
            count = redis_conn.eval(
                self.INCREMENT_SCRIPT, 1, key, self.window_size)
        if count > self.max_request:
            return True

