import { Routes, Route } from 'react-router-dom';
import Main from '@/pages/Main';
import Layout from '@/layouts/Layout';
import Pokemons from '@/pages/Pokemons';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Main />} />
        <Route path="pokemon" element={<Pokemons />} />
        <Route path="pokemon/:page" element={<Pokemons />} />
      </Route>
    </Routes>
  );
}

export default App;