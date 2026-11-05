import time
import requests
import psycopg2

DB_HOST = "localhost"
DB_NAME = "steam_db"
DB_USER = "project_user"
DB_PASS = "choose_a_password"
STEAM_API_KEY = "5EDDA0679628F05C8C40C847C843D204"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
}

session = requests.Session()
session.headers.update(HEADERS)

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

def fetch_master_app_list(api_key):
    apps = []
    last_appid = 0
    have_more = True
    print("Fetching active games catalog...")
    while have_more:
        url = "https://api.steampowered.com/IStoreService/GetAppList/v1/"
        params = {
            "key": api_key,
            "include_games": True,
            "max_results": 50000,
            "last_appid": last_appid
        }
        try:
            resp = session.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json().get("response", {})
                batch = data.get("apps", [])
                if not batch:
                    break
                apps.extend(batch)
                last_appid = data.get("last_appid", batch[-1].get("appid"))
                have_more = data.get("have_more_results", False)
                print(f"Loaded {len(apps)} store games...")
            else:
                break
        except Exception:
            break
    print(f"Total games loaded: {len(apps)}")
    return apps

def fetch_live_player_count(game_id):
    url = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={game_id}"
    try:
        resp = session.get(url, timeout=5)
        if resp.status_code == 200:
            return resp.json().get("response", {}).get("player_count", 0)
    except Exception:
        pass
    return 0

def fetch_review_stats(game_id):
    url = "https://api.steampowered.com/IUserReviewsService/GetAppReviews/v1/"
    params = {
        "key": STEAM_API_KEY,
        "appid": game_id,
        "review_type": "all",
        "purchase_type": "all",
        "num_per_page": 0
    }
    try:
        resp = session.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            summary = resp.json().get("response", {}).get("query_summary", {})
            total_reviews = summary.get("total_reviews", 0)
            total_positive = summary.get("total_positive", 0)
            
            rating_score = round((total_positive / total_reviews) * 100, 2) if total_reviews > 0 else None
            total_plays_est = total_reviews * 35
            return rating_score, total_reviews, total_plays_est
    except Exception:
        pass
    return None, 0, 0

def fetch_store_details(game_id):
    url = f"https://store.steampowered.com/api/appdetails?appids={game_id}&cc=us&l=english"
    try:
        resp = session.get(url, timeout=10)
        ctype = resp.headers.get("content-type", "")
        if resp.status_code == 200 and "application/json" in ctype:
            data = resp.json().get(str(game_id), {})
            if data.get("success") and "data" in data:
                app = data["data"]
                if app.get("type") != "game":
                    return None
                name = app.get("name")
                is_free = app.get("is_free", False)
                price = 0.0
                if not is_free and "price_overview" in app:
                    price = app["price_overview"].get("final", 0) / 100.0
                meta = app.get("metacritic", {}).get("score")
                genres = ", ".join([g.get("description", "") for g in app.get("genres", [])])
                devs = ", ".join(app.get("developers", []))
                pubs = ", ".join(app.get("publishers", []))
                rdate = app.get("release_date", {}).get("date", "")
                year = None
                if rdate:
                    for token in rdate.replace(",", "").split():
                        if token.isdigit() and len(token) == 4:
                            year = int(token)
                            break
                desc = app.get("short_description") or app.get("detailed_description", "")
                return {
                    "name": name,
                    "is_free": is_free,
                    "price": price,
                    "metacritic": meta,
                    "genre": genres,
                    "developers": devs,
                    "publisher": pubs,
                    "year": year,
                    "description": desc
                }
    except Exception:
        pass
    return None

def upsert_game(conn, game_id, d, players, rating, reviews, plays_est):
    sql = """
    INSERT INTO game_log (
        game_id, game_name, player_count, genre, rating_score, 
        total_reviews, total_plays_est, publisher, price, year, 
        developers, metacritic_score, is_free, detailed_description
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (game_id) DO UPDATE SET
        game_name = EXCLUDED.game_name,
        player_count = EXCLUDED.player_count,
        genre = EXCLUDED.genre,
        rating_score = EXCLUDED.rating_score,
        total_reviews = EXCLUDED.total_reviews,
        total_plays_est = EXCLUDED.total_plays_est,
        publisher = EXCLUDED.publisher,
        price = EXCLUDED.price,
        year = EXCLUDED.year,
        developers = EXCLUDED.developers,
        metacritic_score = EXCLUDED.metacritic_score,
        is_free = EXCLUDED.is_free,
        detailed_description = EXCLUDED.detailed_description;
    """
    with conn.cursor() as cur:
        cur.execute(sql, (
            game_id, d["name"], players, d["genre"], rating,
            reviews, plays_est, d["publisher"], d["price"], d["year"],
            d["developers"], d["metacritic"], d["is_free"], d["description"]
        ))
    conn.commit()

def main():
    apps = fetch_master_app_list(STEAM_API_KEY)
    if not apps:
        return
    conn = get_db_connection()
    print("Starting sync loop...")
    for idx, app in enumerate(apps):
        gid = app.get("appid")
        if not gid:
            continue
        d = fetch_store_details(gid)
        if d:
            players = fetch_live_player_count(gid)
            rating, reviews, plays_est = fetch_review_stats(gid)
            try:
                upsert_game(conn, gid, d, players, rating, reviews, plays_est)
                print(f"[{idx+1}/{len(apps)}] Saved: {gid} - {d['name']} | Rating: {rating}% | Reviews: {reviews}")
            except Exception as err:
                conn.rollback()
                print(f"DB Error on {gid}: {err}")
        time.sleep(1.5)
    conn.close()

if __name__ == "__main__":
    main()
