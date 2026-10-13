import { AssessmentResponse } from '../types';

interface ResultsProps {
  response: AssessmentResponse;
  onReset: () => void;
}

export function Results({ response, onReset }: ResultsProps) {
  const handlePrint = () => {
    window.print();
  };

  const getUrgencyColor = () => {
    switch (response.urgency) {
      case 'emergency':
        return 'bg-red-600';
      case 'urgent':
        return 'bg-orange-500';
      case 'routine':
        return 'bg-green-600';
      case 'unknown':
        return 'bg-navy-600';
      default:
        return 'bg-navy-600';
    }
  };

  const getUrgencyLabel = () => {
    switch (response.urgency) {
      case 'emergency':
        return 'EMERGENCY';
      case 'urgent':
        return 'URGENT';
      case 'routine':
        return 'ROUTINE';
      case 'unknown':
        return 'INSUFFICIENT INFORMATION';
      default:
        return 'UNKNOWN';
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Urgency Banner */}
      <div
        className={`${getUrgencyColor()} text-white p-6 rounded-xl shadow-lg`}
        role="alert"
        aria-live="assertive"
        data-testid="urgency-banner"
      >
        <div className="flex items-center gap-4">
          <div className="flex-shrink-0">
            {response.urgency === 'emergency' && (
              <svg className="h-12 w-12" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            )}
            {response.urgency === 'urgent' && (
              <svg className="h-12 w-12" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            )}
            {response.urgency === 'routine' && (
              <svg className="h-12 w-12" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            )}
            {response.urgency === 'unknown' && (
              <svg className="h-12 w-12" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            )}
          </div>
          <div>
            <h2 className="text-3xl font-bold">{getUrgencyLabel()}</h2>
            {response.urgency === 'emergency' && (
              <p className="text-lg mt-1">Call emergency services immediately (112 in India)</p>
            )}
          </div>
        </div>
      </div>

      {/* Warning Signs */}
      {response.warning_signs_detected.length > 0 && (
        <div className="bg-red-50 border-l-4 border-red-500 p-6 rounded-r-xl">
          <h3 className="text-lg font-semibold text-red-900 mb-3">Warning Signs Detected</h3>
          <ul className="space-y-2">
            {response.warning_signs_detected.map((sign, index) => (
              <li key={index} className="text-red-800">
                <strong>{sign.sign}</strong>: {sign.description}
                <span className="block text-sm text-red-600 mt-1">Source: {sign.source}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Reasoning */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-xl font-semibold text-navy-900 mb-3">Assessment Reasoning</h3>
        <p className="text-navy-700 whitespace-pre-line">{response.reasoning}</p>
      </div>

      {/* Recommended Next Steps */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-xl font-semibold text-navy-900 mb-3">Recommended Next Steps</h3>
        <ul className="space-y-2">
          {response.recommended_next_steps.map((step, index) => (
            <li key={index} className="flex items-start gap-3 text-navy-700">
              <span className="flex-shrink-0 w-6 h-6 bg-teal-100 text-teal-800 rounded-full flex items-center justify-center text-sm font-semibold">
                {index + 1}
              </span>
              <span>{step}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Limitations */}
      <div className="bg-navy-50 rounded-xl p-6">
        <h3 className="text-xl font-semibold text-navy-900 mb-3">Important Limitations</h3>
        <ul className="space-y-2">
          {response.limitations.map((limitation, index) => (
            <li key={index} className="flex items-start gap-3 text-navy-700">
              <span className="text-teal-600">•</span>
              <span>{limitation}</span>
            </li>
          ))}
        </ul>
        {response.is_demo_mode && (
          <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
            <p className="text-sm text-amber-800">
              <strong>Demo Mode:</strong> AI explanations are generalized. For personalized explanations, configure an AI provider.
            </p>
          </div>
        )}
      </div>

      {/* Follow-up Question */}
      {response.needs_follow_up && response.follow_up_question && (
        <div className="bg-teal-50 border-l-4 border-teal-500 p-6 rounded-r-xl">
          <h3 className="text-lg font-semibold text-teal-900 mb-2">Additional Information Needed</h3>
          <p className="text-teal-800">{response.follow_up_question}</p>
        </div>
      )}

      {/* Actions */}
      <div className="flex flex-wrap gap-4 justify-center">
        <button
          onClick={handlePrint}
          className="px-6 py-3 bg-navy-600 text-white rounded-lg hover:bg-navy-700 transition-colors flex items-center gap-2"
        >
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
          </svg>
          Print Summary
        </button>
        <button
          onClick={onReset}
          className="px-6 py-3 border-2 border-navy-300 text-navy-700 rounded-lg hover:bg-navy-50 transition-colors"
        >
          Start New Assessment
        </button>
      </div>
    </div>
  );
}
