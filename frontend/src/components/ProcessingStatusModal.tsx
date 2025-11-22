import { useEffect, useMemo } from 'react';

type StepStatus = 'pending' | 'active' | 'done';

type ProcessingStep = {
  id: string;
  label: string;
  status: StepStatus;
};

type ProcessingStatusModalProps = {
  visible: boolean;
  steps: ProcessingStep[];
};

const statusIcon: Record<StepStatus, string> = {
  pending: '⏳',
  active: '⚡',
  done: '✅'
};

const ProcessingStatusModal: React.FC<ProcessingStatusModalProps> = ({ visible, steps }) => {
  const activeSteps = useMemo(() => steps.filter((step) => step.status !== 'pending').length, [steps]);

  if (!visible) {
    return null;
  }

  return (
    <div className="processing-modal">
      <div className="processing-card">
        <p className="panel-label">Procesando</p>
        <h2>Estamos preparando tu sesión</h2>
        <p className="processing-description">
          Analizando movimientos, armando posiciones y solicitando cotizaciones históricas ({activeSteps}/{steps.length})
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
      </div>
    </div>
  );
};

export type { ProcessingStep, StepStatus };
export default ProcessingStatusModal;
