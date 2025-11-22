import { SummaryResponse } from '../api/client';

interface SummaryCardsProps {
  summary: SummaryResponse;
}

const formatter = new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' });
const icons = ['💳', '🏦', '🚪', '💸', '📈', '🌙'];

const SummaryCards: React.FC<SummaryCardsProps> = ({ summary }) => {
  const items = [
    { label: 'Capital invertido', value: summary.totalInvested, description: 'Entradas netas en el exchange', accent: 'accent-1' },
    { label: 'Saldo actual', value: summary.currentBalance, description: 'Valor en tiempo real de la cartera', accent: 'accent-2' },
    { label: 'Retiros totales', value: summary.totalWithdrawn, description: 'Fondos que han salido del exchange', accent: 'accent-3' },
    { label: 'Comisiones pagadas', value: summary.totalFees, description: 'Fees acumuladas en todas las operaciones', accent: 'accent-4' },
    { label: 'Ganancias realizadas', value: summary.realizedGains, description: 'Beneficio ya consolidado', accent: 'accent-3' },
    { label: 'Ganancias no realizadas', value: summary.unrealizedGains, description: 'Potencial pendiente', accent: 'accent-4' }
  ];

  return (
    <div className="stat-grid">
      {items.map((item, index) => (
        <article key={item.label} className={`stat-card ${item.accent}`}>
          <div className="stat-card__icon" aria-hidden="true">
            {icons[index]}
          </div>
          <p className="stat-card__label">{item.label}</p>
          <p className="stat-card__value">{formatter.format(item.value)}</p>
          <p className="stat-card__description">{item.description}</p>
        </article>
      ))}
    </div>
  );
};

export default SummaryCards;
