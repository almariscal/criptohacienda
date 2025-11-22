import { NavLink, Route, Routes, useLocation } from 'react-router-dom';
import UploadPage from './pages/UploadPage';
import DashboardPage from './pages/DashboardPage';

const Layout = ({ children }: { children: React.ReactNode }) => {
  const location = useLocation();
  return (
    <div className="container">
      <header className="layout-header">
        <div>
          <h1>Cripto Hacienda</h1>
          <p>Visualiza y analiza tus operaciones</p>
        </div>
        <nav className="nav-links">
          <NavLink to="/" className={({ isActive }) => (isActive && location.pathname === '/' ? 'active' : '')}>
            Subir CSV
          </NavLink>
          <NavLink to="/dashboard" className={({ isActive }) => (isActive ? 'active' : '')}>
            Dashboard
          </NavLink>
        </nav>
      </header>
      {children}
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
    </Routes>
  );
}

export default App;
