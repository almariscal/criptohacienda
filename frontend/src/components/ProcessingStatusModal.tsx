import { useMemo } from 'react';
import { createPortal } from 'react-dom';

type StepStatus = 'pending' | 'active' | 'done' | 'error';

type ProcessingStep = {
  id: string;
  label: string;
  status: StepStatus;
};

type ProcessingStatusModalProps = {
  visible: boolean;
  steps: ProcessingStep[];
  messages?: string[];
};

const statusIcon: Record<StepStatus, string> = {
  pending: '⏳',
  active: '⚡',
  done: '✅',
  error: '⚠️'
};

const ProcessingStatusModal: React.FC<ProcessingStatusModalProps> = ({ visible, steps, messages = [] }) => {
  const activeSteps = useMemo(() => steps.filter((step) => step.status !== 'pending').length, [steps]);
  const totalSteps = steps.length || 1;

  if (!visible || typeof document === 'undefined') {
    return null;
  }

  const modal = (
    <div className="processing-modal">
      <div className="processing-card">
        <p className="panel-label">Procesando</p>
        <h2>Estamos preparando tu sesión</h2>
        <p className="processing-description">
          Analizando movimientos, armando posiciones y solicitando cotizaciones históricas ({activeSteps}/{totalSteps})
        </p>
        <ol className="processing-steps">
          {steps.map((step) => (
            <li key={step.id} className={`processing-step processing-step--${step.status}`}>
              <span className="processing-step__icon" aria-hidden="true">
                {statusIcon[step.status]}
              </span>
              <span>{step.label}</span>
            </li>
          ))}
        </ol>
        {messages.length > 0 && (
          <div className="processing-log">
            <p className="processing-log__title">Actividad reciente</p>
            <ul>
              {messages.slice(-6).map((message, index) => (
                <li key={`${message}-${index}`}>{message}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );

  return createPortal(modal, document.body);
};

export type { ProcessingStep, StepStatus };
export default ProcessingStatusModal;
