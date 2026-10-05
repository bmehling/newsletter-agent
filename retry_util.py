import time


def with_retry(fn, attempts=4, base_delay=2, label="call"):
    """
    Calls fn() and retries on any exception with exponential backoff.
    Re-raises the last exception if all attempts fail.
    """
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as e:
            if attempt == attempts:
                raise
            delay = base_delay * (2 ** (attempt - 1))
            print(f"  ! {label} failed (attempt {attempt}/{attempts}): {e}. Retrying in {delay}s...")
            time.sleep(delay)
