# plivoapi-rate-limiter

This is a Python library intented to be used with PlivoAPI to rate limit APIs using various rate-limiting mechanisms via decorators.

pip install git+https://github.com/deepakplv/plivoapi-rate-limiter

And then use decorators over the API(s) which need to be rate limited:
```python
from rate_limiter.rate_limiter import FixedWindowRateLimiter
redis_connection = redis.Redis(connection_pool=redis.ConnectionPool(host='127.0.0.1', port=6379, db=2))
@FixedWindowRateLimiter(window_size=60, max_request=100, redis_connection=redis_connection, use_IP=False)
def some_plivo_api_view():
    pass
```
