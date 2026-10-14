import type { AssessmentResponse, UrgencyLevel } from '../types';

interface ResultsProps {
  response: AssessmentResponse;
  onReset: () => void;
}

const URGENCY_STYLE: Record<
  UrgencyLevel,
  { banner: string; label: string; subtitle: string | null }
> = {
  emergency: {
    banner: 'from-red-700 to-red-800',
    label: 'EMERGENCY',
    subtitle: null,
  },
  urgent: {
    banner: 'from-orange-700 to-orange-800',
    label: 'URGENT',
    subtitle: 'Please seek medical attention soon, ideally today.',
  },
  routine: {
    banner: 'from-green-700 to-emerald-800',
    label: 'ROUTINE',
    subtitle: 'Book a visit with a healthcare provider when convenient.',
  },
  unknown: {
    banner: 'from-navy-700 to-navy-900',
    label: 'INSUFFICIENT INFORMATION',
    subtitle: 'A little more detail would help us guide you safely.',
  },
};

function UrgencyIcon({ urgency }: { urgency: UrgencyLevel }) {
  const common = { className: 'h-9 w-9 sm:h-11 sm:w-11', fill: 'currentColor', viewBox: '0 0 20 20', 'aria-hidden': true } as const;
  switch (urgency) {
    case 'emergency':
      return (
        <svg {...common}>
          <path
            fillRule="evenodd"
            d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
            clipRule="evenodd"
          />
        </svg>
      );
    case 'urgent':
      return (
        <svg {...common}>
          <path
            fillRule="evenodd"
            d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
            clipRule="evenodd"
          />
        </svg>
      );
    case 'routine':
      return (
        <svg {...common}>
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
            clipRule="evenodd"
          />
        </svg>
      );
    default:
      return (
        <svg {...common}>
          <path
            fillRule="evenodd"
            d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
            clipRule="evenodd"
          />
        </svg>
      );
  }
}

const SCALE: { level: UrgencyLevel; label: string }[] = [
  { level: 'routine', label: 'Routine' },
  { level: 'urgent', label: 'Urgent' },
  { level: 'emergency', label: 'Emergency' },
];

const card = 'rounded-3xl border border-navy-100 bg-white p-6 shadow-card sm:p-7';
const heading = 'mb-4 font-display text-xl font-bold text-navy-900';

export function Results({ response, onReset }: ResultsProps) {
  const handlePrint = () => {
    window.print();
  };

  const style = URGENCY_STYLE[response.urgency] ?? URGENCY_STYLE.unknown;
  const isEmergency = response.urgency === 'emergency';
  // Emergency guidance is never animated or delayed: it is in place on the first paint.
  const reveal = (delay: number) => (isEmergency ? undefined : { animationDelay: `${delay}ms` });
  const revealClass = isEmergency ? '' : 'animate-fade-up';

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      {/* Urgency classification (first thing on the page, never animated for emergencies) */}
      <div
        className={`${isEmergency ? '' : 'animate-fade-up'} rounded-3xl bg-gradient-to-br ${style.banner} p-6 text-white shadow-lift sm:p-8`}
        role="alert"
        aria-live="assertive"
        data-testid="urgency-banner"
      >
        <div className="flex items-center gap-4 sm:gap-5">
          <div className="flex h-16 w-16 flex-shrink-0 items-center justify-center rounded-full bg-white/15 sm:h-20 sm:w-20">
            <UrgencyIcon urgency={response.urgency} />
          </div>
          <div className="min-w-0">
            <h2 className="text-2xl font-extrabold tracking-wide sm:text-3xl">{style.label}</h2>
            {isEmergency && (
              <p className="mt-1 text-base sm:text-lg">Call emergency services immediately (112 in India)</p>
            )}
            {style.subtitle && <p className="mt-1 text-base text-white/90 sm:text-lg">{style.subtitle}</p>}
          </div>
        </div>
        {isEmergency && (
          <a
            href="tel:112"
            className="mt-5 inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3 text-lg font-bold text-red-700 shadow-md transition-transform active:scale-95 print:hidden"
          >
            <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path d="M2 3a1 1 0 011-1h2.15a1 1 0 01.98.8l.7 3.5a1 1 0 01-.28.9L5.2 8.4a11 11 0 006.4 6.4l1.2-1.35a1 1 0 01.9-.28l3.5.7a1 1 0 01.8.98V17a1 1 0 01-1 1h-1C8.7 18 2 11.3 2 3z" />
            </svg>
            Call 112 now
          </a>
        )}
        {/* Where this result sits on the scale: labelled and outlined, so it never relies on colour alone */}
        <div className="mt-6 grid grid-cols-3 gap-1.5 text-center text-xs font-semibold sm:text-sm" aria-hidden="true">
          {SCALE.map(({ level, label }) => {
            const current = level === response.urgency;
            return (
              <span
                key={level}
                className={`flex items-center justify-center rounded-lg px-2 py-1.5 ${
                  current ? 'bg-white text-navy-900' : 'border border-white/40 text-white/90'
                }`}
              >
                {current ? `${label} (your result)` : label}
              </span>
            );
          })}
        </div>
      </div>

      {/* Warning Signs */}
      {response.warning_signs_detected.length > 0 && (
        <div
          className={`${revealClass} rounded-3xl border border-red-200 border-l-4 border-l-red-600 bg-red-50 p-6`}
          style={reveal(80)}
        >
          <h3 className="mb-3 flex items-center gap-2 font-display text-xl font-bold text-red-900">
            <svg className="h-5 w-5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            Warning Signs Detected
          </h3>
          <ul className="space-y-3">
            {response.warning_signs_detected.map((sign, index) => (
              <li key={index} className="text-red-900">
                <strong>{sign.sign}</strong>: {sign.description}
                <span className="mt-1 block text-sm text-red-700">Source: {sign.source}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommended Next Steps: the primary action card */}
      <div className={`${revealClass} ${card} border-t-4 border-t-teal-600`} style={reveal(140)}>
        <h3 className={heading}>Recommended Next Steps</h3>
        <ol className="space-y-4">
          {response.recommended_next_steps.map((step, index) => (
            <li key={index} className="flex items-start gap-3.5 text-navy-800">
              <span className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-teal-700 text-sm font-semibold text-white">
                {index + 1}
              </span>
              <span className="pt-0.5 text-[1.02rem] leading-relaxed">{step}</span>
            </li>
          ))}
        </ol>
      </div>

      {/* Reasoning */}
      <div className={`${revealClass} ${card}`} style={reveal(200)}>
        <h3 className={`${heading} mb-3`}>Assessment Reasoning</h3>
        <p className="whitespace-pre-line leading-relaxed text-navy-700">{response.reasoning}</p>
      </div>

      {/* Follow-up Question */}
      {response.needs_follow_up && response.follow_up_question && (
        <div className={`${revealClass} rounded-3xl border border-teal-200 border-l-4 border-l-teal-600 bg-teal-50 p-6`} style={reveal(230)}>
          <h3 className="mb-2 font-display text-lg font-bold text-teal-900">Additional Information Needed</h3>
          <p className="text-teal-900">{response.follow_up_question}</p>
        </div>
      )}

      {/* Limitations */}
      <div className={`${revealClass} rounded-3xl border border-navy-200 bg-navy-50 p-6 sm:p-7`} style={reveal(260)}>
        <h3 className="mb-3 flex items-center gap-2 font-display text-xl font-bold text-navy-900">
          <svg className="h-5 w-5 flex-shrink-0 text-navy-600" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path fillRule="evenodd" d="M10 1.944A11.954 11.954 0 012.166 5C2.056 5.649 2 6.319 2 7c0 5.225 3.34 9.67 8 11.317C14.66 16.67 18 12.225 18 7c0-.682-.057-1.35-.166-2.001A11.954 11.954 0 0110 1.944zM11 14a1 1 0 11-2 0 1 1 0 012 0zm0-7a1 1 0 10-2 0v3a1 1 0 102 0V7z" clipRule="evenodd" />
          </svg>
          Important Limitations
        </h3>
        <ul className="space-y-2">
          {response.limitations.map((limitation, index) => (
            <li key={index} className="flex items-start gap-3 text-navy-700">
              <span className="text-teal-700" aria-hidden="true">•</span>
              <span>{limitation}</span>
            </li>
          ))}
        </ul>
        {response.is_demo_mode && (
          <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-3">
            <p className="text-sm text-amber-900">
              <strong>Demo Mode:</strong> AI explanations are generalized. For personalized explanations, configure an AI provider.
            </p>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex flex-wrap justify-center gap-3 pt-2 print:hidden">
        <button
          onClick={handlePrint}
          className="flex items-center gap-2 rounded-xl bg-navy-800 px-6 py-3 font-medium text-white shadow-sm transition duration-150 hover:bg-navy-900 active:scale-[0.97]"
        >
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
          </svg>
          Print Summary
        </button>
        <button
          onClick={onReset}
          className="rounded-xl border border-navy-300 bg-white px-6 py-3 font-medium text-navy-700 transition duration-150 hover:bg-navy-50 active:scale-[0.97]"
        >
          Start New Assessment
        </button>
      </div>
    </div>
  );
}
