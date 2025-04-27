import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.js'
import { ThemeProvider } from './components/theme-provider.js'
import { BrowserRouter } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from '@/store/index';

createRoot(document.getElementById('root')!).render(
  <Provider store={store}>
    <BrowserRouter>
      <ThemeProvider defaultTheme="system" storageKey="ui-theme">
        <App />
      </ThemeProvider>
    </BrowserRouter>
  </Provider>,
)
