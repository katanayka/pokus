CREATE TABLE IF NOT EXISTS users (
  id serial PRIMARY KEY,
  email text UNIQUE NOT NULL,
  password_hash text NOT NULL,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_pokemons (
  id serial PRIMARY KEY,
  user_id int REFERENCES users(id),
  pokemon_id int NOT NULL,
  name text NOT NULL,
  stats jsonb NOT NULL,
  types jsonb NOT NULL,
  UNIQUE(user_id, pokemon_id)
);

CREATE TABLE IF NOT EXISTS active_pokemon (
  user_id int PRIMARY KEY REFERENCES users(id),
  pokemon_id int NOT NULL REFERENCES user_pokemons(pokemon_id),
  selected_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS lobby (
  id serial PRIMARY KEY,
  user_id int REFERENCES users(id),
  pokemon_id int NOT NULL,
  enqueued_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS battles (
  id serial PRIMARY KEY,
  p1_id int REFERENCES users(id),
  p2_id int REFERENCES users(id),
  p1_pokemon_id int,
  p2_pokemon_id int,
  seed bigint NOT NULL,
  status text,
  result jsonb,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS battle_events (
  id serial PRIMARY KEY,
  battle_id int REFERENCES battles(id),
  turn int,
  payload jsonb,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS statistics (
  user_id int PRIMARY KEY REFERENCES users(id),
  wins int DEFAULT 0,
  losses int DEFAULT 0,
  damage int DEFAULT 0,
  crits int DEFAULT 0,
  win_rate numeric(5,2) DEFAULT 0
);
