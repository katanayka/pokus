import { Link } from "react-router-dom";

export default function Header() {
    return (
        <header className="max-w-7xl mx-auto mb-8 flex justify-between items-center border-b border-dotted">
            <div>
                <h1 className="text-3xl font-bold">Pokus</h1>
                <p className="mt-1">hueta ebanaya</p>
            </div>
            <nav>
          <Link to="/">Главная</Link> |{' '}
          <Link to="/pokemon">Покемоны</Link>
        </nav>
        </header>
    );
}