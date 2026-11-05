import requests

BASE_URL = "http://127.0.0.1:5000/api"

def print_result(test_name, status_code, expected_status, response_json=None):
    passed = status_code == expected_status
    flag = "PASSED" if passed else "FAILED"
    print(f"[{flag}] {test_name}")
    print(f"   Status Code: {status_code} (Expected: {expected_status})")
    if response_json:
        print(f"   Response Payload: {response_json}")
    print("-" * 60)

def run_tests():
    print("============================================================")
    print("STARTING STEAM 2.0 API AUTOMATED TEST SUITE")
    print("============================================================\n")

    # 1. PUBLIC ROUTE TESTS (UNAUTHENTICATED)
    r = requests.get(f"{BASE_URL}/games/top-rated?limit=2")
    print_result("Public Top Rated Games", r.status_code, 200, r.json() if r.status_code == 200 else None)

    r = requests.get(f"{BASE_URL}/games?q=Terraria")
    print_result("Public Game Search (Terraria)", r.status_code, 200, r.json() if r.status_code == 200 else None)

    # 2. UNAUTHENTICATED ACCESS TO PROTECTED ROUTES (EXPECT 401)
    r = requests.get(f"{BASE_URL}/me")
    print_result("Unauthenticated /api/me Access", r.status_code, 401, r.json() if r.status_code == 401 else None)

    r = requests.post(f"{BASE_URL}/reviews", json={"game_id": 105600, "rating": 9.5})
    print_result("Unauthenticated Review Submission", r.status_code, 401, r.json() if r.status_code == 401 else None)

    # 3. VIEWER SESSION TESTS (ROLE = 'viewer')
    viewer_session = requests.Session()
    
    r = viewer_session.post(f"{BASE_URL}/login", json={"username": "sam", "password": "sams_password"})
    print_result("Viewer Login", r.status_code, 200, r.json() if r.status_code == 200 else None)

    r = viewer_session.get(f"{BASE_URL}/me")
    print_result("Viewer Profile Check (/api/me)", r.status_code, 200, r.json() if r.status_code == 200 else None)

    r = viewer_session.post(f"{BASE_URL}/reviews", json={
        "game_id": 105600,
        "rating": 9.8,
        "review_text": "Terraria is an absolute masterpiece!"
    })
    print_result("Viewer Post Review", r.status_code, 201, r.json() if r.status_code == 201 else None)
    created_review_id = r.json().get("review", {}).get("review_id") if r.status_code == 201 else None

    r = viewer_session.get(f"{BASE_URL}/my-reviews")
    print_result("Viewer Get My Reviews", r.status_code, 200, r.json() if r.status_code == 200 else None)

    r = viewer_session.post(f"{BASE_URL}/admin/games", json={"game_id": 999999, "game_name": "Unauthorized Game"})
    print_result("Viewer Attempt Admin Action", r.status_code, 403, r.json() if r.status_code == 403 else None)

    # 4. ADMIN SESSION TESTS (ROLE = 'admin')
    admin_session = requests.Session()

    r = admin_session.post(f"{BASE_URL}/login", json={"username": "ms_g", "password": "admin_password"})
    print_result("Admin Login", r.status_code, 200, r.json() if r.status_code == 200 else None)

    r = admin_session.post(f"{BASE_URL}/admin/games", json={
        "game_id": 730,
        "game_name": "Counter-Strike 2",
        "price": 0.00,
        "genre": "Action, Free To Play",
        "publisher": "Valve",
        "rating_score": 84.95,
        "total_reviews": 1526937,
        "player_count": 850000
    })
    print_result("Admin Upsert Game Record", r.status_code, 200, r.json() if r.status_code == 200 else None)

    if created_review_id:
        r = admin_session.delete(f"{BASE_URL}/admin/reviews/{created_review_id}")
        print_result(f"Admin Delete Review {created_review_id}", r.status_code, 200, r.json() if r.status_code == 200 else None)

    # 5. LOGOUT VERIFICATION
    r = viewer_session.post(f"{BASE_URL}/logout")
    print_result("Viewer Logout", r.status_code, 200, r.json() if r.status_code == 200 else None)

    r = viewer_session.get(f"{BASE_URL}/me")
    print_result("Viewer Access After Logout", r.status_code, 401, r.json() if r.status_code == 401 else None)

if __name__ == "__main__":
    run_tests()
