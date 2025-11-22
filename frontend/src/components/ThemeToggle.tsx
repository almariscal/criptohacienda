import { useTheme } from '../context/ThemeContext';

const ThemeToggle = () => {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <button type="button" className="theme-toggle" onClick={toggleTheme} aria-label="Cambiar modo de color">
      <span className="theme-toggle__icon" role="img" aria-hidden="true">
        {isDark ? '🌙' : '☀️'}
      </span>
      <span className="theme-toggle__label">{isDark ? 'Modo noche' : 'Modo día'}</span>
      <span className="theme-toggle__switch" data-active={isDark}></span>
    </button>
  );
};

export default ThemeToggle;
