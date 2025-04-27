import { Pokemon } from '@/types/pokemon';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../ui/card';

interface PokemonCardProps {
  pokemon: Pokemon;
}

const PokemonCard = ({ pokemon }: PokemonCardProps) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{pokemon.Name}</CardTitle>
        <CardDescription>
          <div className="flex gap-2 mt-2">
            {pokemon.Types.map((type, index) => (
              <Badge key={index} variant="outline">{type}</Badge>
            ))}
          </div>
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="border rounded-lg p-4">
            <div className="flex justify-center mt-4">
              <img
                src={pokemon.Sprite}
                alt={pokemon.Name}
                className="w-48 h-48 object-contain"
                style={{ imageRendering: "pixelated" }}
              />
            </div>
          </div>
        </div>
      </CardContent>
      <CardFooter>
        <Button variant="outline" size="sm" className="w-full">Фуфел</Button>
      </CardFooter>
    </Card>
    // <div className="w-64 p-4 bg-white rounded-lg shadow-md border flex flex-col">
    //   <div className="text-center">
    //     <h2 className="text-xl font-bold capitalize"></h2>
    //     
    //   </div>
    //   <div className="mt-4">
    //     <h3 className="text-sm font-semibold">Stats</h3>
    //     <div className="grid grid-cols-2 gap-2 mt-2 text-sm">
    //       <p>HP: {pokemon.Stats.hp}</p>
    //       <p>Attack: {pokemon.Stats.attack}</p>
    //       <p>Defense: {pokemon.Stats.defense}</p>
    //       <p>Sp. Atk: {pokemon.Stats['special-attack']}</p>
    //       <p>Sp. Def: {pokemon.Stats['special-defense']}</p>
    //       <p>Speed: {pokemon.Stats.speed}</p>
    //     </div>
    //   </div>
    // </div>
  );
};

export default PokemonCard;