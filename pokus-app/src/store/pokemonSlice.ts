import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';
import { Pokemon } from '@/types/pokemon';

// Async thunk to fetch Pokémon data with pagination
export const fetchPokemons = createAsyncThunk('pokemon/fetchPokemons', async (page: number) => {
  const response = await axios.get<Pokemon[]>(`http://localhost:9090/v1/pokemons/${page}`);
  return response.data;
});

// Define state shape
interface PokemonState {
  pokemons: Pokemon[];
  loading: boolean;
  error: string | null;
  currentPage: number;
}

const initialState: PokemonState = {
  pokemons: [],
  loading: false,
  error: null,
  currentPage: 1,
};

const pokemonSlice = createSlice({
  name: 'pokemon',
  initialState,
  reducers: {
    setPage: (state, action) => {
      state.currentPage = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchPokemons.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchPokemons.fulfilled, (state, action) => {
        state.loading = false;
        state.pokemons = action.payload;
      })
      .addCase(fetchPokemons.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch Pokémon';
      });
  },
});

export const { setPage } = pokemonSlice.actions;
export default pokemonSlice.reducer;