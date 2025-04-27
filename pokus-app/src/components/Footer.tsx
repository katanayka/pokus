const Footer = () => {
  return (
    <footer className="max-w-7xl mx-auto mt-8 py-6 border-t border-gray-200 flex justify-between items-center text-gray-600">
      <div>
        <p className="text-sm font-medium">© {new Date().getFullYear()} Pokus</p>
        <p className="mt-1 text-xs">Built with ❤️ by karmotrine</p>
      </div>
      <div className="flex space-x-6">
        <a href="#" className="text-sm hover:text-blue-500 transition-colors">
          Privacy
        </a>
        <a href="#" className="text-sm hover:text-blue-500 transition-colors">
          Terms
        </a>
        <a href="#" className="text-sm hover:text-blue-500 transition-colors">
          Contact
        </a>
      </div>
    </footer>
  );
};

export default Footer;