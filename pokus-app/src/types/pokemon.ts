export interface PokemonStats {
    attack: number;
    defense: number;
    hp: number;
    'special-attack': number;
    'special-defense': number;
    speed: number;
}

export interface Pokemon {
    ID: number;
    Name: string;
    Sprite: string;
    Types: string[];
    Stats: PokemonStats;
}