import { useState } from 'react';

interface FileUploadProps {
  onUpload: (file: File) => Promise<void>;
}

const FileUpload: React.FC<FileUploadProps> = ({ onUpload }) => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!file) {
      setError('Selecciona un archivo CSV para continuar.');
      return;
    }

    setError(null);
    setLoading(true);
    try {
      await onUpload(file);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="section">
      <h2>Subir archivo CSV de Binance</h2>
      <p>Importa tus operaciones para generar el dashboard.</p>
      <div className="input-group">
        <input
          type="file"
          accept=".csv"
          onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Subiendo...' : 'Subir archivo'}
        </button>
      </div>
      {error && <div className="alert">{error}</div>}
    </form>
  );
};

export default FileUpload;
