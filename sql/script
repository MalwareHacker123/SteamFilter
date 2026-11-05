import time
import requests
import psycopg2

DB_HOST = "localhost"
DB_NAME = "steam_db"
DB_USER = "project_user"
DB_PASS = "choose_a_password"

def update_player_counts():
    conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cursor = conn.cursor()

    # Fetch all game_ids currently in your database
    cursor.execute("SELECT game_id FROM game_log WHERE game_name IS NOT NULL;")
    games = cursor.fetchall()

    print(f"Updating player counts for {len(games)} games...")

    for (game_id,) in games:
        url = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={game_id}"
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                count = resp.json().get("response", {}).get("player_count", 0)
                cursor.execute("UPDATE game_log SET player_count = %s WHERE game_id = %s;", (count, game_id))
                conn.commit()
        except Exception:
            conn.rollback()

        # 0.2s delay allows fast updates without store page rate-limiting
        time.sleep(0.2)

    cursor.close()
    conn.close()

if __name__ == "__main__":
    while True:
        update_player_counts()
        print("Player counts updated. Waiting 15 minutes for next cycle...")
        time.sleep(900)  # Refresh every 15 minutes
