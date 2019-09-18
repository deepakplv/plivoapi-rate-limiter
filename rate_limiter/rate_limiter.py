"""
This library provides various rate-limiting mechanisms for Flask-based APIs.
RateLimiters are provided as decorators which can be applied over API views.
"""
from abc import ABCMeta, abstractmethod
from flask import request


class RateLimitResponse(object):
    """
    Response returned by the API when rate-limit exceeds.
    PlivoAPI(Python Flask) expects response in this specific format.
    """
    def __init__(self, code, content, method):
        self.code = code
        self.content = content or {}
        self.method = method


class AbstractRateLimiter(object):
    """
    All rate-limiter implementations need to derive from this base class.
    window_size: In seconds
    max_request: Count of allowed requests in the window
    redis_connection: Redis connection(clustered or non-clustered)
    use_IP: Also use IPAddress for rate-limiting
    """
    __metaclass__ = ABCMeta

    def __init__(self, window_size, max_request, redis_connection=None, use_IP=False):
        self.window_size = window_size
        self.max_request = max_request
        self.redis_connection = redis_connection
        self.use_IP = use_IP
        super(AbstractRateLimiter, self).__init__()

    def __call__(self, func):
        """
        Check if limit has exceeded or not, and return rate-limiting response accordingly.
        Specific rate-limiting implementations need to define the logic for `has_limit_exceeded()`
        """
        def wrapper(rest_handler, auth_session, *args, **kwargs):
            # api_name contains the relative URL of the API(without queryparams) which also contains the AUTHID
            key = str(auth_session.api_name)
            if self.use_IP:
                ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
                key += ":" + ip
            if self.has_limit_exceeded(key):
                return RateLimitResponse(
                    code=429,
                    content={'error': "too many requests"},
                    method=auth_session.api_method
                )
            return func(rest_handler, auth_session, *args, **kwargs)
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    @abstractmethod
    def has_limit_exceeded(self, key):
        pass


class FixedWindowRateLimiter(AbstractRateLimiter):
    """
    This rate limiter blocks request if the number of requests exceeds the allowed requests in the
    defined time-window till the window resets.
    """
    def has_limit_exceeded(self, key):
        key = "FWLimiter:" + key
        # To avoid race condition, using a lua script to increment key and set ttl(only first time).
        # This is documented here: https://redis.io/commands/incr#pattern-rate-limiter-2
        lua_script = b"""
            local current
            current = redis.call("incr",KEYS[1])
            if tonumber(current) == 1 then
                redis.call("expire",KEYS[1],ARGV[1])
            end
            return current
        """
        try:
            count = self.redis_connection.eval(
                lua_script, 1, key, self.window_size)
        except:
            return False
        if count > self.max_request:
            return True
        return False

