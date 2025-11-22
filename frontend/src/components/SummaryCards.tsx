import { SummaryResponse } from '../api/client';

interface SummaryCardsProps {
  summary: SummaryResponse;
}

const formatter = new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' });

const SummaryCards: React.FC<SummaryCardsProps> = ({ summary }) => {
  const items = [
    { label: 'Invertido', value: summary.totalInvested },
    { label: 'Comisiones', value: summary.totalFees },
    { label: 'Ganancias realizadas', value: summary.realizedGains },
    { label: 'Ganancias no realizadas', value: summary.unrealizedGains }
  ];

  return (
    <div className="card-grid">
      {items.map((item) => (
        <div key={item.label} className="section">
          <h3>{item.label}</h3>
          <p style={{ fontSize: '24px', fontWeight: 700 }}>{formatter.format(item.value)}</p>
        </div>
      ))}
    </div>
  );
};

export default SummaryCards;
