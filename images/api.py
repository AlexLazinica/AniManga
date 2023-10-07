import requests

def fetch_anime_data(query):
    # anime API
    base_url = "https://api.jikan.moe/v3/"

    # Endpoint anime searcha
    endpoint = f"search/anime?q={query}&page=1"

    # GET response za API
    response = requests.get(base_url + endpoint)

    if response.status_code == 200:
        # Json response za anime-datu
        anime_data = response.json()
        return anime_data
    else:
        # Ovo je za errors
        return None

def fetch_manga_data(query):
    #manga API
    base_url = "https://api.mangadex.org/v2/"

    # Konstruisan endpint
    endpoint = f"manga?title={query}"

    # GET response za API
    response = requests.get(base_url + endpoint)

    if response.status_code == 200:
        # Json response za manga-data
        manga_data = response.json()
        return manga_data
    else:
        # Ovo je za errors
        return None
