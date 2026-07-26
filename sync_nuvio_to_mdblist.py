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
MDBLIST_API_URL = f"https://api.mdblist.com/lists/{MDBLIST_LIST_ID}/items/add"

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


def main():
    try:
        print("1. Authenticating with Nuvio...")
        token = get_nuvio_token()

        print("2. Fetching library...")
        raw_items = fetch_all_nuvio_items(token)

        print("3. Formatting items for MDBList...")
        payload = process_items_for_mdblist(raw_items)
        print(f"Prepared {len(payload['movies'])} movies and {len(payload['shows'])} shows.")

        if payload["movies"] or payload["shows"]:
            print("4. Syncing to MDBList...")
            result = push_to_mdblist(payload)
            print("Result:", result)
        else:
            print("No items found to sync.")

    except Exception as e:
        print(f"Error occurred: {e}")


if __name__ == "__main__":
    main()