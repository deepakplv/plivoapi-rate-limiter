class RESTResponse(object):
    def __init__(self, code, content, method):
        self.code = code
        self.content = content or {}
        self.method = method

    def __str__(self):
        return '<RESTResponse %s %s>' % (str(self.method), str(self.code))

class RateLimiter(object):
    def __init__(self, window_size, max_request):
        self.window_size = window_size
        self.max_request = max_request

    def __call__(self, func):
        def wrapper(rest_handler, auth_session, *args, **kwargs):
            if self.max_request > 2:
                return RESTResponse(429,
                                    {'error': "too many requests", "max_request":self.max_request, "window_size":self.window_size},
                                    "GET")
            return func(rest_handler, auth_session, *args, **kwargs)
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
