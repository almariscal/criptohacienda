import { useEffect, useId, useRef, useState } from 'react';
import ProcessingStatusModal, { ProcessingStep, StepStatus } from './ProcessingStatusModal';
import { apiClient } from '../api/client';

interface FileUploadProps {
  onUploadStart: (file: File) => Promise<string>;
  onUploadComplete: (sessionId: string) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onUploadStart, onUploadComplete }) => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [showProcessing, setShowProcessing] = useState(false);
  const [processingSteps, setProcessingSteps] = useState<ProcessingStep[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [messages, setMessages] = useState<string[]>([]);
  const pollIntervalRef = useRef<number | null>(null);
  const inputId = useId();

  const selectFile = (nextFile: File | null) => {
    setFile(nextFile);
    if (nextFile) {
      setError(null);
    }
  };

  const clearPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  };

  const finishProcessing = () => {
    clearPolling();
    window.setTimeout(() => setShowProcessing(false), 400);
    setLoading(false);
    setJobId(null);
  };

  const mapStatus = (status: 'pending' | 'running' | 'completed' | 'error'): StepStatus => {
    if (status === 'running') return 'active';
    if (status === 'completed') return 'done';
    if (status === 'error') return 'error';
    return 'pending';
  };

  const pollJobStatus = async (id: string) => {
    try {
      const status = await apiClient.fetchUploadJob(id);
      setMessages(status.messages || []);
      setProcessingSteps(
        status.steps.map((step) => ({
          id: step.id,
          label: step.label,
          status: mapStatus(step.status)
        }))
      );
      if (status.status === 'completed' && status.session_id) {
        finishProcessing();
        onUploadComplete(status.session_id);
      } else if (status.status === 'error') {
        finishProcessing();
        setError(status.error || 'Se produjo un error al procesar el archivo.');
      }
    } catch (err) {
      finishProcessing();
      setError((err as Error).message);
    }
  };

  const startProcessing = (id: string) => {
    setShowProcessing(true);
    setProcessingSteps([]);
    setMessages([]);
    setJobId(id);
    pollJobStatus(id);
    pollIntervalRef.current = window.setInterval(() => pollJobStatus(id), 3000);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!file) {
      setError('Selecciona un archivo CSV para continuar.');
      return;
    }

    setError(null);
    setLoading(true);
    try {
      const job = await onUploadStart(file);
      startProcessing(job);
    } catch (err) {
      setLoading(false);
      setError((err as Error).message);
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    if (event.dataTransfer.items && event.dataTransfer.items.length > 0) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (event: React.DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    if (event.relatedTarget && event.currentTarget.contains(event.relatedTarget as Node)) {
      return;
    }
    setIsDragging(false);
  };

  const handleDrop = (event: React.DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    setIsDragging(false);
    const droppedFile = event.dataTransfer.files?.[0];
    if (!droppedFile) {
      return;
    }

    if (!droppedFile.name.toLowerCase().endsWith('.csv')) {
      setError('El archivo debe ser un CSV.');
      return;
    }

    selectFile(droppedFile);
    event.dataTransfer.clearData();
  };

  useEffect(() => {
    return () => {
      clearPolling();
    };
  }, []);

  return (
    <form onSubmit={handleSubmit} className="panel upload-card">
      <div className="upload-card__header">
        <h2>Sube tu historial</h2>
        <p>
          Arrastra el CSV exportado desde Binance y déjanos calcular tus plusvalías con un estilo tan pulido como tu
          cartera.
        </p>
      </div>

      <label
        htmlFor={inputId}
        className={`upload-dropzone ${isDragging ? 'upload-dropzone--dragging' : ''}`}
        onDragOver={handleDragOver}
        onDragEnter={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          id={inputId}
          type="file"
          accept=".csv"
          onChange={(e) => selectFile(e.target.files ? e.target.files[0] : null)}
          disabled={loading}
          className="visually-hidden"
        />
        <div>
          <div className="upload-dropzone__badge">CSV</div>
          <p className="upload-dropzone__title">Suelta el archivo aquí o haz clic para seleccionarlo</p>
          <p className="upload-dropzone__subtitle">{file ? `${file.name}` : 'Peso máximo 5MB'}</p>
        </div>
      </label>

      <div className="upload-actions">
        <button type="submit" className="btn btn-primary" disabled={loading || showProcessing}>
          {loading ? 'Procesando...' : 'Procesar archivo'}
        </button>
        <span className="muted">Solo datos locales; nada se guarda sin tu permiso.</span>
      </div>

      {error && (
        <div className="alert" role="alert" aria-live="assertive">
          {error}
        </div>
      )}
      <ProcessingStatusModal visible={showProcessing} steps={processingSteps} messages={messages} />
    </form>
  );
};

export default FileUpload;
