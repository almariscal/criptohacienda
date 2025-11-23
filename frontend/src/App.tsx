import { NavLink, Route, Routes, useLocation } from 'react-router-dom';
import UploadPage from './pages/UploadPage';
import DashboardPage from './pages/DashboardPage';
import AnalyzePage from './pages/AnalyzePage';
import ThemeToggle from './components/ThemeToggle';

const Layout = ({ children }: { children: React.ReactNode }) => {
  const location = useLocation();
  const isHome = location.pathname === '/';

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <p className="hero__eyebrow">Cripto Hacienda</p>
          <h1>Controla tus operaciones como lo haría Revolut</h1>
          <p className="hero__subtitle">
            Subir, analizar y visualizar tus operaciones nunca fue tan elegante. Alterna entre modo luz y noche sin perder
            detalle.
          </p>
        </div>
        <ThemeToggle />
      </header>
      <nav className="nav-pills" aria-label="Navegación principal">
        <NavLink to="/" className={({ isActive }) => `nav-pill ${isActive && isHome ? 'nav-pill--active' : ''}`}>
          Subir CSV
        </NavLink>
        <NavLink to="/dashboard" className={({ isActive }) => `nav-pill ${isActive ? 'nav-pill--active' : ''}`}>
          Dashboard
        </NavLink>
        <NavLink to="/analyze" className={({ isActive }) => `nav-pill ${isActive ? 'nav-pill--active' : ''}`}>
          Análisis multichain
        </NavLink>
      </nav>
      <main className="page-content">{children}</main>
    </div>
  );
};

function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <Layout>
            <UploadPage />
          </Layout>
        }
      />
      <Route
        path="/dashboard"
        element={
          <Layout>
            <DashboardPage />
          </Layout>
        }
      />
      <Route
        path="/analyze"
        element={
          <Layout>
            <AnalyzePage />
          </Layout>
        }
      />
    </Routes>
  );
}

export default App;
