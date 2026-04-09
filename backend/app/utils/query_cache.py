query_cache = {}

def get_cached(query: str):
    return query_cache.get(query)

def set_cached(query: str, rewritten: str):
    query_cache[query] = rewritten

def clear_cache():
    query_cache.clear()
