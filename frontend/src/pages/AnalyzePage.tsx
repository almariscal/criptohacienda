import { useState } from 'react';
import { AnalyzeResponse, apiClient } from '../api/client';

const chainOptions = [
  { id: 'ethereum', label: 'Ethereum Mainnet' },
  { id: 'arbitrum', label: 'Arbitrum One' },
  { id: 'base', label: 'Base' },
  { id: 'polygon', label: 'Polygon' },
  { id: 'optimism', label: 'Optimism' },
  { id: 'bsc', label: 'BNB Chain' },
  { id: 'avalanche', label: 'Avalanche C-Chain' }
];

const AnalyzePage = () => {
  const [btcAddresses, setBtcAddresses] = useState('');
  const [evmAddresses, setEvmAddresses] = useState('');
  const [selectedChains, setSelectedChains] = useState<string[]>(['ethereum']);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.analyze({
        binanceCsvFile: file || undefined,
        btcAddresses: btcAddresses.split(/\n|,/).map((addr) => addr.trim()).filter(Boolean),
        evmAddresses: evmAddresses.split(/\n|,/).map((addr) => addr.trim()).filter(Boolean),
        chains: selectedChains
      });
      setResult(response);
    } catch (err) {
      setError((err as Error).message);
      setResult(null);
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
    <div className="dashboard-stack">
      <form className="panel" onSubmit={handleSubmit}>
        <div className="panel-header panel-header--stacked">
          <div>
            <p className="panel-label">Análisis combinado</p>
            <h2>Binance + Wallets on-chain</h2>
          </div>
        </div>
        <label className="upload-dropzone">
          <input
            type="file"
            accept=".csv"
            className="visually-hidden"
            onChange={(event) => setFile(event.target.files ? event.target.files[0] : null)}
          />
          <div>
            <div className="upload-dropzone__badge">CSV</div>
            <p className="upload-dropzone__title">Selecciona tu export de Binance</p>
            <p className="upload-dropzone__subtitle">{file ? file.name : 'Histórico de operaciones'}</p>
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
        <button className="btn btn-primary" type="submit" disabled={loading}>
          {loading ? 'Analizando...' : 'Lanzar análisis'}
        </button>
        {error && <div className="alert" role="alert">{error}</div>}
      </form>

      {result && (
        <div className="panel">
          <div className="panel-header panel-header--stacked">
            <div>
              <p className="panel-label">Resultados</p>
              <h2>Resumen de PnL</h2>
            </div>
          </div>
          <div className="stat-grid">
            {Object.entries(result.pnlSummary).map(([asset, value]) => (
              <article key={asset} className="stat-card">
                <p className="stat-card__label">{asset}</p>
                <p className="stat-card__value">{value.toFixed(6)}</p>
                <p className="stat-card__description">PnL estimado</p>
              </article>
            ))}
          </div>
        </div>
      )}

      {result && (
        <div className="panel">
          <div className="panel-header panel-header--stacked">
            <div>
              <p className="panel-label">Detalles de movimientos</p>
              <h2>Todo el histórico normalizado</h2>
            </div>
          </div>
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Fecha</th>
                  <th>Activo</th>
                  <th>Chain/Ubicación</th>
                  <th>Tipo</th>
                  <th>Cantidad</th>
                  <th>Fee</th>
                  <th>Raw</th>
                </tr>
              </thead>
              <tbody>
                {result.normalizedTxs.map((tx) => (
                  <tr key={tx.id}>
                    <td>{tx.id}</td>
                    <td>{new Date(tx.timestamp).toLocaleString()}</td>
                    <td>{tx.asset}</td>
                    <td>
                      {tx.chain || 'Binance'} / {tx.location}
                    </td>
                    <td>{tx.type}</td>
                    <td>{tx.amount.toFixed(8)}</td>
                    <td>
                      {tx.fee > 0 ? `${tx.fee.toFixed(8)} ${tx.fee_asset}` : '-'}
                    </td>
                    <td>
                      <details>
                        <summary>Ver</summary>
                        <pre>{JSON.stringify(tx.raw, null, 2)}</pre>
                      </details>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {result && (
        <div className="panel">
          <div className="panel-header panel-header--stacked">
            <div>
              <p className="panel-label">Balances</p>
              <h2>Por ubicación</h2>
            </div>
          </div>
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Ubicación</th>
                  <th>Activo</th>
                  <th>Cantidad</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(result.balancesByLocation).map(([location, assets]) =>
                  Object.entries(assets).map(([asset, amount]) => (
                    <tr key={`${location}-${asset}`}>
                      <td>{location}</td>
                      <td>{asset}</td>
                      <td>{amount.toFixed(8)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {result && (
        <div className="panel">
          <div className="panel-header panel-header--stacked">
            <div>
              <p className="panel-label">Desglose por activo</p>
              <h2>Entradas, salidas y fees</h2>
            </div>
          </div>
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Activo</th>
                  <th>Entrado</th>
                  <th>Salido</th>
                  <th>Net</th>
                  <th>Fees</th>
                </tr>
              </thead>
              <tbody>
                {result.assetBreakdown.map((asset) => (
                  <tr key={asset.asset}>
                    <td>{asset.asset}</td>
                    <td>{asset.total_in.toFixed(8)}</td>
                    <td>{asset.total_out.toFixed(8)}</td>
                    <td>{asset.net_amount.toFixed(8)}</td>
                    <td>{asset.fees_paid.toFixed(8)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {result.assetBreakdown.map((asset) => (
            <details key={`${asset.asset}-entries`} className="ledger-details">
              <summary>Operaciones de {asset.asset}</summary>
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Fecha</th>
                      <th>Ubicación</th>
                      <th>Tipo</th>
                      <th>Cantidad</th>
                      <th>Fee</th>
                    </tr>
                  </thead>
                  <tbody>
                    {asset.entries.map((entry) => (
                      <tr key={entry.id}>
                        <td>{new Date(entry.timestamp).toLocaleString()}</td>
                        <td>{entry.location}</td>
                        <td>{entry.type}</td>
                        <td>{entry.amount.toFixed(8)}</td>
                        <td>
                          {entry.fee ? `${entry.fee.toFixed(8)} ${entry.fee_asset}` : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
          ))}
        </div>
      )}

      {result && (
        <div className="panel">
          <div className="panel-header panel-header--stacked">
            <div>
              <p className="panel-label">Evolución de saldos</p>
              <h2>Histórico por token</h2>
            </div>
          </div>
          {Object.entries(result.assetHistory).map(([asset, history]) => (
            <details key={`${asset}-history`} className="ledger-details">
              <summary>{asset}</summary>
              <ul className="history-list">
                {history.map((point) => (
                  <li key={`${asset}-${point.timestamp}`}>
                    {new Date(point.timestamp).toLocaleString()} &mdash; {point.balance.toFixed(8)}
                  </li>
                ))}
              </ul>
            </details>
          ))}
        </div>
      )}
    </div>
  );
};

export default AnalyzePage;
