"""
Cross-cutting timing utilities.
"""
import functools
import time


def timer(func):
    """Decorator to measure function runtime and print duration."""
    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        start_time = time.perf_counter()
        value = func(*args, **kwargs)
        end_time = time.perf_counter()
        run_time = end_time - start_time
        print(f" ====> Duration {run_time:.2f} secs: {func.__doc__}")
        return value

    return wrapper_timer
