import { useMemo } from 'react';
import { createPortal } from 'react-dom';

type StepStatus = 'pending' | 'active' | 'done';

type ProcessingStep = {
  id: string;
  label: string;
  status: StepStatus;
};

type DashboardDetails = {
  steps: string[];
  activeIndex: number;
};

type ProcessingStatusModalProps = {
  visible: boolean;
  steps: ProcessingStep[];
  dashboardDetails?: DashboardDetails;
};

const statusIcon: Record<StepStatus, string> = {
  pending: '⏳',
  active: '⚡',
  done: '✅'
};

const ProcessingStatusModal: React.FC<ProcessingStatusModalProps> = ({ visible, steps, dashboardDetails }) => {
  const activeSteps = useMemo(() => steps.filter((step) => step.status !== 'pending').length, [steps]);

  if (!visible || typeof document === 'undefined') {
    return null;
  }

  const modal = (
    <div className="processing-modal">
      <div className="processing-card">
        <p className="panel-label">Procesando</p>
        <h2>Estamos preparando tu sesión</h2>
        <p className="processing-description">
          Analizando movimientos, armando posiciones y solicitando cotizaciones históricas ({activeSteps}/{steps.length})
        </p>
        <ol className="processing-steps">
          {steps.map((step) => {
            const showDashboardDetails = step.id === 'dashboard' && dashboardDetails && dashboardDetails.steps.length > 0;
            return (
              <li key={step.id} className={`processing-step processing-step--${step.status}`}>
                <span className="processing-step__icon" aria-hidden="true">
                  {statusIcon[step.status]}
                </span>
                <span>{step.label}</span>
                {showDashboardDetails && dashboardDetails && (
                  <ul className="processing-substeps">
                    {dashboardDetails.steps.map((substep, index) => {
                      const subStatus = (() => {
                        if (step.status === 'pending') return 'pending';
                        if (step.status === 'done') return 'done';
                        if (dashboardDetails.activeIndex > index) return 'done';
                        if (dashboardDetails.activeIndex === index) return 'active';
                        return 'pending';
                      })() as StepStatus;
                      return (
                        <li key={substep} className={`processing-substep processing-substep--${subStatus}`}>
                          <span aria-hidden="true">{statusIcon[subStatus]}</span>
                          {substep}
                        </li>
                      );
                    })}
                  </ul>
                )}
              </li>
            );
          })}
        </ol>
      </div>
    </div>
  );

  return createPortal(modal, document.body);
};

export type { ProcessingStep, StepStatus, DashboardDetails };
export default ProcessingStatusModal;
