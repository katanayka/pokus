import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchPokemons } from '@/store/pokemonSlice';
import { RootState } from '@/store/index';
import PokemonCard from '@/components/pokemon/pokemonCard';
import { Link, useParams } from 'react-router-dom';

const PokemonPage = () => {
  const page = parseInt(useParams().page || '1', 10);
  const dispatch = useDispatch<any>();
  const { pokemons, loading, error } = useSelector((state: RootState) => state.pokemon);
  useEffect(() => {
    dispatch(fetchPokemons(page));
  }, [dispatch, page]);

  if (loading) return <p className="text-center">Loading Pokémon...</p>;
  if (error) return <p className="text-center text-red-500">{error}</p>;

  const totalPages = Math.ceil(1118 / 12);
  
  return (
    <div className="max-w-7xl mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6 text-center">Pokémon Cards</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {pokemons.map((pokemon) => (
          <PokemonCard key={pokemon.ID} pokemon={pokemon} />
        ))}
      </div>
      <div className="mt-6 flex justify-center space-x-4">
        {page > 1 && (
          <Link to={`/pokemon/${page - 1}`} className="px-4 py-2 text-white rounded">
            Previous
          </Link>
        )}
        {page < totalPages && (
          <Link to={`/pokemon/${page + 1}`} className="px-4 py-2 text-white rounded">
            Next
          </Link>
        )}
      </div>
    </div>
  );
};

export default PokemonPage;