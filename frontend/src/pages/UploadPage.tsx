import { useId, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import { useSession } from '../context/SessionContext';

const chainOptions = [
  { id: 'ethereum', label: 'Ethereum Mainnet' },
  { id: 'arbitrum', label: 'Arbitrum One' },
  { id: 'base', label: 'Base' },
  { id: 'polygon', label: 'Polygon' },
  { id: 'optimism', label: 'Optimism' },
  { id: 'bsc', label: 'BNB Chain' },
  { id: 'avalanche', label: 'Avalanche C-Chain' }
];

const UploadPage = () => {
  const navigate = useNavigate();
  const { setSessionId } = useSession();
  const [file, setFile] = useState<File | null>(null);
  const [btcAddresses, setBtcAddresses] = useState('');
  const [evmAddresses, setEvmAddresses] = useState('');
  const [selectedChains, setSelectedChains] = useState<string[]>(['ethereum']);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputId = useId();

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const response = await apiClient.uploadUnified({
        binanceCsvFile: file || undefined,
        btcAddresses: btcAddresses.split(/\n|,/).map((addr) => addr.trim()).filter(Boolean),
        evmAddresses: evmAddresses.split(/\n|,/).map((addr) => addr.trim()).filter(Boolean),
        chains: selectedChains
      });
      setSessionId(response.session_id ?? null);
      navigate('/dashboard');
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const toggleChain = (chainId: string) => {
    setSelectedChains((prev) =>
      prev.includes(chainId) ? prev.filter((item) => item !== chainId) : [...prev, chainId]
    );
  };

  return (
    <div className="upload-stack">
      <form onSubmit={handleSubmit} className="panel upload-card">
        <div className="upload-card__header">
          <h2>Sube tu CSV o añade wallets</h2>
          <p>
            Integra Binance y tus wallets BTC/EVM en un solo análisis para visualizar todo en el dashboard.
          </p>
        </div>

        <label htmlFor={inputId} className="upload-dropzone">
          <input
            id={inputId}
            type="file"
            accept=".csv"
            onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
            disabled={loading}
            className="visually-hidden"
          />
          <div>
            <div className="upload-dropzone__badge">CSV</div>
            <p className="upload-dropzone__title">Suelta el archivo o haz clic para seleccionarlo</p>
            <p className="upload-dropzone__subtitle">{file ? `${file.name}` : 'Binance Trade History (opcional)'}</p>
          </div>
        </label>

        <div className="form-grid">
          <label className="form-field">
            <span>Direcciones BTC (una por línea)</span>
            <textarea value={btcAddresses} onChange={(e) => setBtcAddresses(e.target.value)} rows={4} />
          </label>
          <label className="form-field">
            <span>Direcciones EVM</span>
            <textarea value={evmAddresses} onChange={(e) => setEvmAddresses(e.target.value)} rows={4} />
          </label>
        </div>

        <div className="form-field">
          <span>Chains a analizar</span>
          <div className="chip-group">
            {chainOptions.map((chain) => (
              <button
                key={chain.id}
                type="button"
                className={`chip ${selectedChains.includes(chain.id) ? 'chip--active' : ''}`}
                onClick={() => toggleChain(chain.id)}
              >
                {chain.label}
              </button>
            ))}
          </div>
        </div>

        <div className="upload-actions">
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Procesando...' : 'Lanzar análisis'}
          </button>
          <span className="muted">Si no subes CSV, se analizarán solo las wallets.</span>
        </div>

        {error && (
          <div className="alert" role="alert" aria-live="assertive">
            {error}
          </div>
        )}
      </form>

      <div className="panel panel-info">
        <h3>Consejos rápidos</h3>
        <p>Combina tu export de Binance con direcciones BTC/EVM en una sola sesión.</p>
        <ul className="tips-list">
          <li>Los datos se mezclan y se muestran en el dashboard habitual.</li>
          <li>Puedes reiniciar subiendo un nuevo CSV o agregando otras wallets.</li>
        </ul>
      </div>
    </div>
  );
};

export default UploadPage;
