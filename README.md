# Steam Game Filter (Better)
# Purpose
### The purpose of this project is to help steam users find games that might not pop up on their regular steam homepage. It helps filter, find, and secure great games with a user ran and reviewed rating system. Its simple, easy, and fun to use! Its a great software for new gamers and verterans alike.
#
# Use Cases
### My system uses well thought out filter and recommendations through remerebing users and keeping track of their searches, favorite games, rated games, cost, player count, and steam reviews. Users have drop boxes and boxes to type and check off what they want to see or not.
#
# Business Rules
### 1. Every account (User_id) only have one username and one Hash password.
### 2. Every Game must be made after 1970, ratings is only from 0.00 to 10.00, player count cannot be negative, every game gets one id, price cannot go below 0.00.
### 3. Every star needs a user_id, game_id and timestamp of when it was stared. 
### 4. Every table needs a search_id, user_id, date it was searched, can have multiple geners and keywords.
### 5. Every review needs review_id, user_id, game_id, rating score (1.00 to 10.00), optional review text, and timestamp when created.
#
# data dictionary with entity relationship diagram
# Steam 2.0 REST API

A Flask REST API integrated with PostgreSQL (`steam_db`) and `Flask-Login` for session authentication.

## Setup & Execution

1. **Activate Virtual Environment:**
   ```bash
   source .venv/bin/activate







## Entity Relationship Diagram

```mermaid
erDiagram
    user_log {
        INT user_id PK
        VARCHAR username UK
        VARCHAR hash_password
    }

    game_log {
        INT game_id PK
        INT player_count
        VARCHAR genre
        DECIMAL rating
        INT total_plays
        VARCHAR publisher
        DECIMAL price
        INT year
    }

    star {
        INT game_id PK, FK
        INT user_id PK, FK
        TIMESTAMP starred_at
    }

    search {
        INT search_id PK
        INT user_id FK
        VARCHAR keyword
        DATE day
        VARCHAR genre
    }

    user_reviews {
        INT review_id PK
        INT user_id FK
        INT game_id FK
        DECIMAL rating
        TEXT review_text
        TIMESTAMP created_at
    }

    user_log ||--o{ star : "has"
    game_log ||--o{ star : "has"
    user_log ||--o{ search : "performs"
    user_log ||--o{ user_reviews : "writes"
    game_log ||--o{ user_reviews : "receives"
