import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_login import (
    LoginManager, UserMixin, current_user,
    login_required, login_user, logout_user
)
from werkzeug.security import check_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("SECRET_KEY environment variable is missing. Check your .env file.")

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://project_user:choose_a_password@localhost:5432/steam_db")

CORS(app, supports_credentials=True, origins=["http://127.0.0.1:5000", "http://localhost:3000"])

login_manager = LoginManager()
login_manager.init_app(app)


def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


class User(UserMixin):
    def __init__(self, user_id, username, role):
        self.id = user_id
        self.username = username
        self.role = role


@login_manager.user_loader
def load_user(user_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, username, role FROM app_user WHERE user_id = %s;",
                (int(user_id),)
            )
            row = cur.fetchone()
        conn.close()
        if row:
            return User(row["user_id"], row["username"], row["role"])
    except Exception:
        pass
    return None


@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({"error": "Unauthorized. You must log in first."}), 401


# =============================================================================
# AUTHENTICATION ENDPOINTS
# =============================================================================

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "Missing username or password."}), 400

    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT user_id, username, role, password_hash FROM app_user WHERE username = %s;",
            (data["username"],)
        )
        row = cur.fetchone()
    conn.close()

    if row is None or not check_password_hash(row["password_hash"], data["password"]):
        return jsonify({"error": "Invalid username or password."}), 401

    user_obj = User(row["user_id"], row["username"], row["role"])
    login_user(user_obj)
    
    return jsonify({
        "message": f"Successfully logged in as {row['username']}",
        "user": {
            "id": row["user_id"],
            "username": row["username"],
            "role": row["role"]
        }
    }), 200


@app.route("/api/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Successfully logged out."}), 200


@app.route("/api/me", methods=["GET"])
@login_required
def get_current_user_profile():
    return jsonify({
        "user_id": current_user.id,
        "username": current_user.username,
        "role": current_user.role
    }), 200


# =============================================================================
# PUBLIC ANALYTICS ENDPOINTS (OPEN ACCESS)
# =============================================================================

@app.route("/api/games", methods=["GET"])
def search_games():
    query = request.args.get("q", "").strip()
    genre = request.args.get("genre", "").strip()
    min_rating = request.args.get("min_rating", type=float)
    max_price = request.args.get("max_price", type=float)
    limit = min(request.args.get("limit", default=20, type=int), 100)

    sql = """
        SELECT game_id, game_name, genre, rating_score, total_reviews, player_count, price, year
        FROM game_log
        WHERE 1=1
    """
    params = []

    if query:
        sql += " AND game_name ILIKE %s"
        params.append(f"%{query}%")
    if genre:
        sql += " AND genre ILIKE %s"
        params.append(f"%{genre}%")
    if min_rating is not None:
        sql += " AND rating_score >= %s"
        params.append(min_rating)
    if max_price is not None:
        sql += " AND price <= %s"
        params.append(max_price)

    sql += " ORDER BY rating_score DESC NULLS LAST, total_reviews DESC LIMIT %s;"
    params.append(limit)

    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    conn.close()

    return jsonify({"count": len(rows), "games": rows}), 200


@app.route("/api/games/top-rated", methods=["GET"])
def get_top_rated_games():
    min_reviews = request.args.get("min_reviews", default=1000, type=int)
    limit = min(request.args.get("limit", default=10, type=int), 100)

    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT game_id, game_name, rating_score, total_reviews, player_count, price, genre, publisher, year
            FROM game_log
            WHERE total_reviews >= %s AND rating_score IS NOT NULL
            ORDER BY rating_score DESC, total_reviews DESC
            LIMIT %s;
            """,
            (min_reviews, limit)
        )
        rows = cur.fetchall()
    conn.close()

    return jsonify({"count": len(rows), "games": rows}), 200


@app.route("/api/games/most-played", methods=["GET"])
def get_most_played_games():
    limit = min(request.args.get("limit", default=10, type=int), 100)

    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT game_id, game_name, player_count, rating_score, total_reviews, price, genre
            FROM game_log
            ORDER BY player_count DESC
            LIMIT %s;
            """,
            (limit,)
        )
        rows = cur.fetchall()
    conn.close()

    return jsonify({"count": len(rows), "games": rows}), 200


@app.route("/api/games/free", methods=["GET"])
def get_free_games():
    min_reviews = request.args.get("min_reviews", default=100, type=int)
    limit = min(request.args.get("limit", default=10, type=int), 100)

    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT game_id, game_name, rating_score, total_reviews, player_count, genre, publisher, year
            FROM game_log
            WHERE price = 0.00 AND total_reviews >= %s
            ORDER BY rating_score DESC
            LIMIT %s;
            """,
            (min_reviews, limit)
        )
        rows = cur.fetchall()
    conn.close()

    return jsonify({"count": len(rows), "games": rows}), 200


@app.route("/api/games/<int:game_id>", methods=["GET"])
def get_game_detail(game_id):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM game_log WHERE game_id = %s;", (game_id,))
        game = cur.fetchone()
        
        if not game:
            conn.close()
            return jsonify({"error": f"Game with ID {game_id} not found."}), 404

        cur.execute(
            """
            SELECT r.review_id, r.user_id, u.username, r.rating, r.review_text, r.created_at
            FROM user_reviews r
            JOIN app_user u ON r.user_id = u.user_id
            WHERE r.game_id = %s
            ORDER BY r.created_at DESC;
            """,
            (game_id,)
        )
        app_reviews = cur.fetchall()
    conn.close()

    for rev in app_reviews:
        if rev.get("created_at"):
            rev["created_at"] = str(rev["created_at"])

    game["app_user_reviews"] = app_reviews
    return jsonify(game), 200


# =============================================================================
# AUTHENTICATED USER ENDPOINTS (VIEWER + ADMIN)
# =============================================================================

@app.route("/api/reviews", methods=["POST"])
@login_required
def create_review():
    data = request.get_json()
    if not data or "game_id" not in data or "rating" not in data:
        return jsonify({"error": "Fields 'game_id' and 'rating' are required."}), 400

    try:
        rating_val = float(data["rating"])
        if not (0.0 <= rating_val <= 10.0):
            return jsonify({"error": "Rating must be between 0.0 and 10.0."}), 400
    except ValueError:
        return jsonify({"error": "Rating must be a valid decimal number."}), 400

    game_id = int(data["game_id"])
    review_text = data.get("review_text", "").strip()

    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT game_id FROM game_log WHERE game_id = %s;", (game_id,))
        if cur.fetchone() is None:
            conn.close()
            return jsonify({"error": f"Game ID {game_id} does not exist."}), 404

        cur.execute(
            """
            INSERT INTO user_reviews (user_id, game_id, rating, review_text)
            VALUES (%s, %s, %s, %s)
            RETURNING review_id, created_at;
            """,
            (current_user.id, game_id, rating_val, review_text)
        )
        new_rev = cur.fetchone()
    conn.commit()
    conn.close()

    return jsonify({
        "message": "Review created successfully.",
        "review": {
            "review_id": new_rev["review_id"],
            "user_id": current_user.id,
            "game_id": game_id,
            "rating": rating_val,
            "review_text": review_text,
            "created_at": str(new_rev["created_at"])
        }
    }), 201


@app.route("/api/my-reviews", methods=["GET"])
@login_required
def get_my_reviews():
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT r.review_id, r.game_id, g.game_name, r.rating, r.review_text, r.created_at
            FROM user_reviews r
            JOIN game_log g ON r.game_id = g.game_id
            WHERE r.user_id = %s
            ORDER BY r.created_at DESC;
            """,
            (current_user.id,)
        )
        reviews = cur.fetchall()
    conn.close()

    for rev in reviews:
        if rev.get("created_at"):
            rev["created_at"] = str(rev["created_at"])

    return jsonify({"count": len(reviews), "reviews": reviews}), 200


# =============================================================================
# ADMIN-ONLY ENDPOINTS (ROLE = 'admin')
# =============================================================================

@app.route("/api/admin/games", methods=["POST"])
@login_required
def admin_upsert_game():
    if current_user.role != "admin":
        return jsonify({"error": "Forbidden. Admin privileges required."}), 403

    data = request.get_json()
    required_fields = ["game_id", "game_name"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Field '{field}' is required."}), 400

    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO game_log (
                game_id, game_name, price, genre, publisher, rating_score, total_reviews, player_count
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (game_id) DO UPDATE SET
                game_name = EXCLUDED.game_name,
                price = EXCLUDED.price,
                genre = EXCLUDED.genre,
                publisher = EXCLUDED.publisher,
                rating_score = EXCLUDED.rating_score,
                total_reviews = EXCLUDED.total_reviews,
                player_count = EXCLUDED.player_count;
            """,
            (
                data["game_id"],
                data["game_name"],
                data.get("price", 0.00),
                data.get("genre", ""),
                data.get("publisher", ""),
                data.get("rating_score"),
                data.get("total_reviews", 0),
                data.get("player_count", 0)
            )
        )
    conn.commit()
    conn.close()

    return jsonify({"message": f"Game '{data['game_name']}' (ID: {data['game_id']}) catalog record updated."}), 200


@app.route("/api/admin/reviews/<int:review_id>", methods=["DELETE"])
@login_required
def admin_delete_review(review_id):
    if current_user.role != "admin":
        return jsonify({"error": "Forbidden. Admin privileges required."}), 403

    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM user_reviews WHERE review_id = %s RETURNING review_id;", (review_id,))
        deleted = cur.fetchone()
    conn.commit()
    conn.close()

    if not deleted:
        return jsonify({"error": f"Review ID {review_id} not found."}), 404

    return jsonify({"message": f"Review {review_id} successfully deleted by admin."}), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
