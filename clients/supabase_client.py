import os

_client = None


def get_supabase_client():
    """Lazily initialize and return a singleton Supabase client, or None if env vars are missing."""
    global _client
    if _client is not None:
        return _client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return None

    from supabase import create_client
    _client = create_client(url, key)
    return _client
