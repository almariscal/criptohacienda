import { useEffect, useId, useRef, useState } from 'react';
import ProcessingStatusModal, { ProcessingStep, StepStatus } from './ProcessingStatusModal';

interface FileUploadProps {
  onUpload: (file: File) => Promise<void>;
}

const PROCESSING_SEQUENCE: Omit<ProcessingStep, 'status'>[] = [
  { id: 'upload', label: 'Subiendo archivo' },
  { id: 'validate', label: 'Validando formato y agrupando movimientos' },
  { id: 'calc', label: 'Calculando operaciones, lotes y ganancias' },
  { id: 'pricing', label: 'Obteniendo cotizaciones históricas' },
  { id: 'dashboard', label: 'Generando dashboard e informes' }
];

const DASHBOARD_SUB_STEPS = [
  'Construyendo snapshots de cartera',
  'Calculando métricas agregadas',
  'Preparando tablas y gráficos'
];

const FileUpload: React.FC<FileUploadProps> = ({ onUpload }) => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [showProcessing, setShowProcessing] = useState(false);
  const createInitialSteps = (): ProcessingStep[] =>
    PROCESSING_SEQUENCE.map((step, index) => ({
      ...step,
      status: (index === 0 ? 'active' : 'pending') as StepStatus
    }));

  const [processingSteps, setProcessingSteps] = useState<ProcessingStep[]>(createInitialSteps);
  const [dashboardSubStepIndex, setDashboardSubStepIndex] = useState(0);
  const processingIntervalRef = useRef<number | null>(null);
  const timersRef = useRef<number[]>([]);
  const inputId = useId();

  const selectFile = (nextFile: File | null) => {
    setFile(nextFile);
    if (nextFile) {
      setError(null);
    }
  };

  const resetProcessingSteps = (): ProcessingStep[] => createInitialSteps();

  const advanceStep = (targetIndex: number) => {
    setProcessingSteps((prev) =>
      prev.map((step, index) => {
        if (index < targetIndex) return { ...step, status: 'done' as StepStatus };
        if (index === targetIndex) return { ...step, status: 'active' as StepStatus };
        return { ...step, status: 'pending' as StepStatus };
      })
    );
  };

  const startProcessing = () => {
    timersRef.current.forEach((timer) => clearTimeout(timer));
    timersRef.current = [];
    if (processingIntervalRef.current) {
      clearInterval(processingIntervalRef.current);
      processingIntervalRef.current = null;
    }

    setProcessingSteps(resetProcessingSteps());
    setShowProcessing(true);
    setDashboardSubStepIndex(0);

    let currentIndex = 0;
    processingIntervalRef.current = window.setInterval(() => {
      setProcessingSteps((prev) => {
        const next = prev.map((step, index) => {
          if (index < currentIndex) return { ...step, status: 'done' as StepStatus };
          if (index === currentIndex) return { ...step, status: 'active' as StepStatus };
          return { ...step, status: 'pending' as StepStatus };
        });
        return next;
      });

      if (PROCESSING_SEQUENCE[currentIndex].id === 'dashboard') {
        const subIndex = (dashboardSubStepIndex + 1) % DASHBOARD_SUB_STEPS.length;
        setDashboardSubStepIndex(subIndex);
      }

      currentIndex += 1;
      if (currentIndex >= PROCESSING_SEQUENCE.length) {
        currentIndex = PROCESSING_SEQUENCE.length - 1;
      }
    }, 4000);
  };

  const finishProcessing = () => {
    timersRef.current.forEach((timer) => clearTimeout(timer));
    timersRef.current = [];
    if (processingIntervalRef.current) {
      clearInterval(processingIntervalRef.current);
      processingIntervalRef.current = null;
    }
    setProcessingSteps((prev) => prev.map((step) => ({ ...step, status: 'done' as StepStatus })));
    setDashboardSubStepIndex(DASHBOARD_SUB_STEPS.length - 1);
    window.setTimeout(() => setShowProcessing(false), 400);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!file) {
      setError('Selecciona un archivo CSV para continuar.');
      return;
    }

    setError(null);
    setLoading(true);
    startProcessing();
    try {
      await onUpload(file);
      finishProcessing();
    } catch (err) {
      finishProcessing();
      setError((err as Error).message);
    } finally {
      setLoading(false);
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
      timersRef.current.forEach((timer) => clearTimeout(timer));
      if (processingIntervalRef.current) {
        clearInterval(processingIntervalRef.current);
      }
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
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Subiendo...' : 'Procesar archivo'}
        </button>
        <span className="muted">Solo datos locales; nada se guarda sin tu permiso.</span>
      </div>

      {error && (
        <div className="alert" role="alert" aria-live="assertive">
          {error}
        </div>
      )}
      <ProcessingStatusModal
        visible={showProcessing}
        steps={processingSteps}
        dashboardDetails={{ steps: DASHBOARD_SUB_STEPS, activeIndex: dashboardSubStepIndex }}
      />
    </form>
  );
};

export default FileUpload;
