import os
import requests

# ==========================================
# CONFIGURATION FROM ENVIRONMENT
# ==========================================
NUVIO_PUBLISHABLE_KEY = os.getenv("NUVIO_PUBLISHABLE_KEY")
NUVIO_EMAIL = os.getenv("NUVIO_EMAIL")
NUVIO_PASSWORD = os.getenv("NUVIO_PASSWORD")
NUVIO_PROFILE_ID = int(os.getenv("NUVIO_PROFILE_ID", "1"))

MDBLIST_API_KEY = os.getenv("MDBLIST_API_KEY")
MDBLIST_LIST_ID = os.getenv("MDBLIST_LIST_ID")

# API URLs
NUVIO_AUTH_URL = "https://api.nuvio.tv/auth/v1/token?grant_type=password"
NUVIO_RPC_URL = "https://api.nuvio.tv/rest/v1/rpc/sync_pull_library"
NUVIO_WATCHED_URL = "https://api.nuvio.tv/rest/v1/rpc/sync_pull_watched_items"
MDBLIST_API_URL = f"https://api.mdblist.com/lists/{MDBLIST_LIST_ID}/items/add"
MDBLIST_REMOVE_URL = f"https://api.mdblist.com/lists/{MDBLIST_LIST_ID}/items/remove"
MDBLIST_ITEMS_URL = f"https://api.mdblist.com/lists/{MDBLIST_LIST_ID}/items?apikey={MDBLIST_API_KEY}"

def get_nuvio_token():
    """Authenticates with Nuvio and retrieves an access token."""
    headers = {
        "Content-Type": "application/json",
        "apikey": NUVIO_PUBLISHABLE_KEY
    }
    payload = {
        "email": NUVIO_EMAIL,
        "password": NUVIO_PASSWORD
    }
    response = requests.post(NUVIO_AUTH_URL, json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    return data["access_token"]


def fetch_all_nuvio_items(access_token):
    """Paginates through Nuvio library and returns all items."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "apikey": NUVIO_PUBLISHABLE_KEY
    }

    all_items = []
    limit = 500
    offset = 0

    while True:
        payload = {
            "p_profile_id": NUVIO_PROFILE_ID,
            "p_limit": limit,
            "p_offset": offset
        }
        
        print(f"Fetching Nuvio items (offset {offset})...")
        response = requests.post(NUVIO_RPC_URL, json=payload, headers=headers)
        response.raise_for_status()
        items = response.json()

        if not items:
            break

        all_items.extend(items)
        
        if len(items) < limit:
            break  # Reached the last page
            
        offset += limit

    print(f"Total items fetched from Nuvio: {len(all_items)}")
    return all_items


def fetch_watched_items(access_token):
    """Fetches all watched items from Nuvio using pagination."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "apikey": NUVIO_PUBLISHABLE_KEY
    }

    all_watched = []
    page = 1
    page_size = 500

    while True:
        payload = {
            "p_profile_id": NUVIO_PROFILE_ID,
            "p_page": page,
            "p_page_size": page_size
        }
        
        print(f"Fetching watched items (page {page})...")
        response = requests.post(NUVIO_WATCHED_URL, json=payload, headers=headers)
        response.raise_for_status()
        items = response.json()

        if not items:
            break

        all_watched.extend(items)
        
        if len(items) < page_size:
            break
            
        page += 1

    print(f"Total watched items fetched from Nuvio: {len(all_watched)}")
    return all_watched


def get_content_ids(items):
    """Extracts content_ids from a list of items for comparison."""
    return set(item.get("content_id", "") for item in items if item.get("content_id"))


def filter_watched_items(library_items, watched_content_ids):
    """Filters out items that are already watched."""
    filtered = [item for item in library_items if item.get("content_id") not in watched_content_ids]
    watched_count = len(library_items) - len(filtered)
    if watched_count > 0:
        print(f"Filtered out {watched_count} watched items from library.")
    return filtered


def process_items_for_mdblist(items):
    """Parses Nuvio items into MDBList payload format."""
    movies = []
    shows = []

    for item in items:
        content_id = item.get("content_id", "")
        content_type = item.get("content_type", "").lower()

        # Check if item uses TMDB ID format (e.g. "tmdb:550")
        if content_id.startswith("tmdb:"):
            try:
                tmdb_id = int(content_id.split(":")[1])
                
                if content_type in ["movie"]:
                    movies.append({"tmdb": tmdb_id})
                elif content_type in ["series", "show", "tv"]:
                    shows.append({"tmdb": tmdb_id})
            except (ValueError, IndexError):
                continue
        # If content_id is an IMDb ID (e.g. "tt0032138")
        elif content_id.startswith("tt"):
            if content_type in ["movie"]:
                movies.append({"imdb": content_id})
            elif content_type in ["series", "show", "tv"]:
                shows.append({"imdb": content_id})

    return {"movies": movies, "shows": shows}


def push_to_mdblist(payload):
    """Posts items payload to MDBList static list."""
    # DO NOT pass 'Authorization: Bearer' header when using an MDBList API key
    headers = {
        "Content-Type": "application/json"
    }
    
    url = f"https://api.mdblist.com/lists/{MDBLIST_LIST_ID}/items/add?apikey={MDBLIST_API_KEY}"

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    print("Successfully added items to MDBList!")
    return response.json()


def remove_from_mdblist(payload):
    """Removes items from MDBList static list."""
    headers = {
        "Content-Type": "application/json"
    }
    
    url = f"https://api.mdblist.com/lists/{MDBLIST_LIST_ID}/items/remove?apikey={MDBLIST_API_KEY}"

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    print("Successfully removed items from MDBList!")
    return response.json()


def fetch_mdblist_items():
    """Fetches all items currently on the MDBList."""
    headers = {"Content-Type": "application/json"}
    url = f"https://api.mdblist.com/lists/{MDBLIST_LIST_ID}/items?apikey={MDBLIST_API_KEY}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    
    items = []
    if isinstance(data, dict):
        for key in ["items", "results", "data"]:
            if key in data and isinstance(data[key], list):
                items = data[key]
                break
        else:
            for value in data.values():
                if isinstance(value, list):
                    items = value
                    break
    elif isinstance(data, list):
        items = data
    
    print(f"Total items fetched from MDBList: {len(items)}")
    return items


def get_mdblist_ids(items):
    """Extracts TMDB/IMDb IDs from MDBList items for comparison."""
    ids = set()
    for item in items:
        if isinstance(item, dict):
            if item.get("tmdb"):
                ids.add(f"tmdb:{item['tmdb']}")
            if item.get("imdb"):
                ids.add(item["imdb"])
        elif isinstance(item, str):
            if item.startswith("tmdb:"):
                ids.add(item)
            elif item.startswith("tt"):
                ids.add(item)
    return ids


def main():
    try:
        print("1. Authenticating with Nuvio...")
        token = get_nuvio_token()

        print("2. Fetching library...")
        raw_items = fetch_all_nuvio_items(token)

        print("3. Fetching watched items...")
        watched_items = fetch_watched_items(token)
        watched_content_ids = get_content_ids(watched_items)

        print("4. Filtering out watched items from library...")
        filtered_items = filter_watched_items(raw_items, watched_content_ids)

        print("5. Fetching current MDBList items...")
        mdblist_items = fetch_mdblist_items()
        mdblist_ids = get_mdblist_ids(mdblist_items)

        print("6. Formatting items for MDBList...")
        payload = process_items_for_mdblist(filtered_items)
        print(f"Prepared {len(payload['movies'])} movies and {len(payload['shows'])} shows for addition.")

        # Remove watched items from MDBList ONLY if they are actually on the list
        watched_payload = process_items_for_mdblist(watched_items)
        
        # Filter watched payload to only include items that are on MDBList
        removal_movies = []
        removal_shows = []
        
        for movie in watched_payload["movies"]:
            # Check if this movie is on MDBList
            movie_id = None
            if "tmdb" in movie:
                movie_id = f"tmdb:{movie['tmdb']}"
            elif "imdb" in movie:
                movie_id = movie["imdb"]
            if movie_id and movie_id in mdblist_ids:
                removal_movies.append(movie)
        
        for show in watched_payload["shows"]:
            show_id = None
            if "tmdb" in show:
                show_id = f"tmdb:{show['tmdb']}"
            elif "imdb" in show:
                show_id = show["imdb"]
            if show_id and show_id in mdblist_ids:
                removal_shows.append(show)
        
        removal_payload = {"movies": removal_movies, "shows": removal_shows}
        
        if removal_payload["movies"] or removal_payload["shows"]:
            print(f"7. Removing {len(removal_payload['movies'])} movies and {len(removal_payload['shows'])} shows from MDBList...")
            remove_from_mdblist(removal_payload)
        else:
            print("7. No watched items to remove from MDBList.")

        if payload["movies"] or payload["shows"]:
            print("8. Syncing to MDBList...")
            result = push_to_mdblist(payload)
            print("Result:", result)
        else:
            print("8. No items found to sync.")

    except Exception as e:
        print(f"Error occurred: {e}")


if __name__ == "__main__":
    main()
