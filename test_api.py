import requests

BASE = "http://127.0.0.1:5000/api"

print("--- 1. Testing Unauthenticated Access ---")
# Anyone can view public catalog (returns 200)
r = requests.get(f"{BASE}/games/top-rated")
print("Public route /games/top-rated status:", r.status_code)

# Unauthenticated request to protected route (returns 401)
r = requests.get(f"{BASE}/me")
print("Protected route /me (unauthenticated) status:", r.status_code, r.json())

print("\n--- 2. Testing Viewer Session (sam) ---")
# requests.Session() stores the session cookie sent back by /api/login
viewer = requests.Session()

# Log in as viewer
r = viewer.post(f"{BASE}/login", json={"username": "sam", "password": "sams_password"})
print("Login status:", r.status_code, r.json())

# Viewer access to user profile (returns 200 because cookie is automatically sent)
r = viewer.get(f"{BASE}/me")
print("GET /me status:", r.status_code, r.json())

# Viewer posts a game review (returns 201)
r = viewer.post(f"{BASE}/reviews", json={"game_id": 105600, "rating": 9.0, "review_text": "Great game!"})
print("POST /reviews status:", r.status_code, r.json())

# Viewer attempts admin-only action (returns 403 Forbidden)
r = viewer.post(f"{BASE}/admin/games", json={"game_id": 888, "game_name": "Test Game", "genre": "RPG", "price": 19.99})
print("POST /admin/games as viewer status:", r.status_code, r.json())

print("\n--- 3. Testing Admin Session (ms_g) ---")
admin = requests.Session()

# Log in as admin
r = admin.post(f"{BASE}/login", json={"username": "ms_g", "password": "admin_password"})
print("Admin Login status:", r.status_code, r.json())

# Admin creates a game entry (returns 201)
r = admin.post(f"{BASE}/admin/games", json={"game_id": 888, "game_name": "Test Game", "genre": "RPG", "price": 19.99})
print("POST /admin/games as admin status:", r.status_code, r.json())

print("\n--- 4. Testing Logout & Cleanup ---")
# Log viewer out
r = viewer.post(f"{BASE}/logout")
print("Logout status:", r.status_code, r.json())

# Trying /me after logout (returns 401 again because session cookie was cleared)
r = viewer.get(f"{BASE}/me")
print("GET /me after logout status:", r.status_code, r.json())
