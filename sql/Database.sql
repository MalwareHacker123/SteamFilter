DROP TABLE IF EXISTS rating, search, star, game_log, user_log CASCADE;

CREATE TABLE user_log (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL UNIQUE,
    hash_password VARCHAR(255) NOT NULL
);

CREATE TABLE game_log (
    game_id INT PRIMARY KEY,
    player_count INT DEFAULT 0 CHECK (player_count >= 0),
    genre VARCHAR(50) NOT NULL,
    rating DECIMAL(4, 2) CHECK (rating BETWEEN 0.00 AND 10.00),
    total_plays INT DEFAULT 0 CHECK (total_plays >= 0),
    publisher VARCHAR(100),
    price DECIMAL(10, 2) CHECK (price >= 0.00),
    year INT CHECK (year >= 1970)
;

CREATE TABLE star (
    game_id INT NOT NULL,
    user_id INT NOT NULL,
    starred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (game_id, user_id),
    CONSTRAINT fk_star_game FOREIGN KEY (game_id) REFERENCES game_log(game_id) ON DELETE CASCADE,
    CONSTRAINT fk_star_user FOREIGN KEY (user_id) REFERENCES user_log(user_id) ON DELETE CASCADE
);

CREATE TABLE search (
    search_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INT NOT NULL,
    keyword VARCHAR(255),
    day DATE DEFAULT CURRENT_DATE,
    genre VARCHAR(50),
    CONSTRAINT fk_search_user FOREIGN KEY (user_id) REFERENCES user_log(user_id) ON DELETE CASCADE
);

CREATE TABLE rating (
    rating_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sent_user INT NOT NULL,
    rec_user INT NOT NULL,
    date DATE DATE DEFAULT CURRENT_DATE,
    response TEXT,
    CONSTRAINT chk_different_users CHECK (sent_user <> rec_user),
    CONSTRAINT fk_rating_sent FOREIGN KEY (sent_user) REFERENCES user_log(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_rating_rec FOREIGN KEY (rec_user) REFERENCES user_log(user_id) ON DELETE CASCADE
);
