import { useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import type { AgeGroup, SymptomRequest } from '../types';

interface QuestionnaireProps {
  onSubmit: (data: SymptomRequest) => void;
  isLoading: boolean;
}

const inputClass =
  'w-full rounded-xl border border-navy-300 bg-white p-4 text-base text-navy-900 placeholder:text-navy-500 transition-colors hover:border-navy-400 focus:border-teal-600 focus:outline-none focus:ring-4 focus:ring-teal-100';

const choiceClass = (selected: boolean) =>
  `group relative flex w-full items-center justify-between gap-3 rounded-xl border-2 p-4 text-left transition-all duration-150 active:scale-[0.99] ${
    selected
      ? 'border-teal-600 bg-teal-50 text-teal-900 shadow-sm ring-4 ring-teal-100'
      : 'border-navy-200 bg-white text-navy-700 hover:border-teal-500 hover:bg-teal-50/60'
  }`;

function CheckBadge({ selected }: { selected: boolean }) {
  return (
    <span
      aria-hidden="true"
      className={`flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full border-2 transition-all ${
        selected ? 'border-teal-600 bg-teal-600 text-white' : 'border-navy-300 text-transparent'
      }`}
    >
      <svg className="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
        <path
          fillRule="evenodd"
          d="M16.7 5.3a1 1 0 010 1.4l-7.5 7.5a1 1 0 01-1.4 0L3.3 9.7a1 1 0 011.4-1.4l3.8 3.8 6.8-6.8a1 1 0 011.4 0z"
          clipRule="evenodd"
        />
      </svg>
    </span>
  );
}

function StepHeader({ title, subtitle }: { title: string; subtitle: ReactNode }) {
  return (
    <div className="space-y-2">
      <h2
        data-step-heading
        tabIndex={-1}
        className="font-display text-2xl font-bold tracking-tight text-navy-900 sm:text-3xl"
      >
        {title}
      </h2>
      <p className="text-navy-600">{subtitle}</p>
    </div>
  );
}

const STEP_TITLES = ['Age group', 'Main symptom', 'Duration & onset', 'Severity', 'Additional symptoms', 'Warning signs'];

const STEP_HINTS: Record<number, string> = {
  2: 'Enter your main symptom to continue.',
  3: 'Fill in both how long you have had it and how it started to continue.',
  4: 'Choose a severity, or describe it in your own words, to continue.',
};

const SEVERITY_DOT: Record<string, string> = {
  mild: 'bg-green-500',
  moderate: 'bg-amber-500',
  severe: 'bg-red-500',
};

export function Questionnaire({ onSubmit, isLoading }: QuestionnaireProps) {
  const [step, setStep] = useState(1);
  const [forward, setForward] = useState(true);
  const [formData, setFormData] = useState<Partial<SymptomRequest>>({
    age_group: '18-64',
    main_symptom: '',
    duration: '',
    onset: '',
    severity: '',
    associated_symptoms: [],
    warning_signs: [],
    additional_context: '',
  });

  const [associatedSymptomInput, setAssociatedSymptomInput] = useState('');
  const [warningSignInput, setWarningSignInput] = useState('');

  const totalSteps = 6;
  const containerRef = useRef<HTMLDivElement>(null);
  const isFirstRender = useRef(true);

  // Move focus to the new step's heading so keyboard and screen-reader users land in context.
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    const heading = containerRef.current?.querySelector<HTMLElement>('[data-step-heading]');
    heading?.focus({ preventScroll: true });
    heading?.scrollIntoView?.({ block: 'center', behavior: 'smooth' });
  }, [step]);

  const updateField = (field: keyof SymptomRequest, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const addAssociatedSymptom = () => {
    if (associatedSymptomInput.trim() && formData.associated_symptoms!.length < 20) {
      updateField('associated_symptoms', [...formData.associated_symptoms!, associatedSymptomInput.trim()]);
      setAssociatedSymptomInput('');
    }
  };

  const removeAssociatedSymptom = (index: number) => {
    updateField('associated_symptoms', formData.associated_symptoms!.filter((_, i) => i !== index));
  };

  const addWarningSign = () => {
    if (warningSignInput.trim() && formData.warning_signs!.length < 20) {
      updateField('warning_signs', [...formData.warning_signs!, warningSignInput.trim()]);
      setWarningSignInput('');
    }
  };

  const removeWarningSign = (index: number) => {
    updateField('warning_signs', formData.warning_signs!.filter((_, i) => i !== index));
  };

  const handleNext = () => {
    if (step < totalSteps) {
      setForward(true);
      setStep(step + 1);
    } else {
      onSubmit(formData as SymptomRequest);
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setForward(false);
      setStep(step - 1);
    }
  };

  const isStepValid = () => {
    switch (step) {
      case 1:
        return !!formData.age_group;
      case 2:
        return formData.main_symptom!.trim().length > 0;
      case 3:
        return formData.duration!.trim().length > 0 && formData.onset!.trim().length > 0;
      case 4:
        return formData.severity!.trim().length > 0;
      case 5:
        return true; // Optional fields
      case 6:
        return true; // Optional context
      default:
        return false;
    }
  };

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <div className="space-y-6">
            <StepHeader
              title="Age Group"
              subtitle="Please select the age group of the person experiencing symptoms."
            />
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2" role="group" aria-label="Age group options">
              {[
                { value: '0-2', label: 'Infant (0-2 years)' },
                { value: '3-12', label: 'Child (3-12 years)' },
                { value: '13-17', label: 'Teen (13-17 years)' },
                { value: '18-64', label: 'Adult (18-64 years)' },
                { value: '65+', label: 'Senior (65+ years)' },
              ].map((option) => {
                const selected = formData.age_group === option.value;
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => updateField('age_group', option.value as AgeGroup)}
                    className={choiceClass(selected)}
                    aria-pressed={selected}
                  >
                    <span className="font-medium">{option.label}</span>
                    <CheckBadge selected={selected} />
                  </button>
                );
              })}
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <StepHeader title="Main Symptom" subtitle="What is the primary symptom or concern?" />
            <div>
              <label htmlFor="main-symptom" className="mb-2 block text-sm font-medium text-navy-700">
                Main symptom
              </label>
              <input
                type="text"
                value={formData.main_symptom}
                onChange={(e) => updateField('main_symptom', e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && isStepValid() && !isLoading) {
                    e.preventDefault();
                    handleNext();
                  }
                }}
                placeholder="e.g., headache, stomach pain, fever"
                className={inputClass}
                maxLength={500}
                id="main-symptom"
                aria-label="Main symptom"
                autoComplete="off"
              />
              <p className="mt-2 text-right text-sm text-navy-500">{formData.main_symptom!.length}/500 characters</p>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <StepHeader
              title="Duration & Onset"
              subtitle="How long have you had this symptom, and when did it start?"
            />
            <div>
              <label htmlFor="duration" className="mb-2 block text-sm font-medium text-navy-700">
                Duration
              </label>
              <input
                id="duration"
                type="text"
                value={formData.duration}
                onChange={(e) => updateField('duration', e.target.value)}
                placeholder="e.g., 2 hours, 3 days, 1 week"
                className={inputClass}
                maxLength={200}
                aria-label="Duration of symptoms"
                autoComplete="off"
              />
            </div>
            <div>
              <label htmlFor="onset" className="mb-2 block text-sm font-medium text-navy-700">
                Onset
              </label>
              <input
                id="onset"
                type="text"
                value={formData.onset}
                onChange={(e) => updateField('onset', e.target.value)}
                placeholder="e.g., sudden, gradual, after eating"
                className={inputClass}
                maxLength={200}
                aria-label="How symptoms started"
                autoComplete="off"
              />
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <StepHeader title="Severity" subtitle="How would you describe the severity?" />
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3" role="group" aria-label="Severity options">
              {[
                { value: 'mild', label: 'Mild' },
                { value: 'moderate', label: 'Moderate' },
                { value: 'severe', label: 'Severe' },
              ].map((option) => {
                const selected = formData.severity === option.value;
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => updateField('severity', option.value)}
                    className={choiceClass(selected)}
                    aria-pressed={selected}
                  >
                    <span className="flex items-center gap-3 font-medium">
                      <span
                        aria-hidden="true"
                        className={`h-2.5 w-2.5 rounded-full ${SEVERITY_DOT[option.value]}`}
                      />
                      {option.label}
                    </span>
                    <CheckBadge selected={selected} />
                  </button>
                );
              })}
            </div>
            <label htmlFor="severity-text" className="-mb-4 block text-sm font-medium text-navy-700">
              Or describe severity in your own words
            </label>
            <input
              type="text"
              value={formData.severity}
              onChange={(e) => updateField('severity', e.target.value)}
              placeholder="e.g., annoying but manageable"
              className={inputClass}
              maxLength={200}
              id="severity-text"
              aria-label="Severity description"
              autoComplete="off"
            />
          </div>
        );

      case 5:
        return (
          <div className="space-y-6">
            <StepHeader
              title="Additional Symptoms"
              subtitle="Are you experiencing any other symptoms? (Optional)"
            />
            <label htmlFor="associated-symptom" className="-mb-4 block text-sm font-medium text-navy-700">
              Associated symptom
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={associatedSymptomInput}
                onChange={(e) => setAssociatedSymptomInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addAssociatedSymptom();
                  }
                }}
                placeholder="Add associated symptom"
                className={`${inputClass} flex-1`}
                maxLength={500}
                id="associated-symptom"
                aria-label="Associated symptom"
                autoComplete="off"
              />
              <button
                type="button"
                onClick={addAssociatedSymptom}
                disabled={!associatedSymptomInput.trim() || formData.associated_symptoms!.length >= 20}
                className="rounded-xl bg-teal-600 px-6 py-4 font-semibold text-white transition duration-150 hover:bg-teal-700 active:scale-[0.97] disabled:cursor-not-allowed disabled:bg-navy-200 disabled:text-navy-500"
              >
                Add
              </button>
            </div>
            {formData.associated_symptoms!.length > 0 && (
              <ul className="space-y-2">
                {formData.associated_symptoms!.map((symptom, index) => (
                  <li
                    key={index}
                    className="flex animate-fade-in items-center justify-between gap-3 rounded-xl border border-navy-200 bg-navy-50 p-3"
                  >
                    <span className="break-words text-navy-700">{symptom}</span>
                    <button
                      type="button"
                      onClick={() => removeAssociatedSymptom(index)}
                      className="rounded-lg px-3 py-1 text-sm font-medium text-red-600 transition-colors hover:bg-red-50 hover:text-red-700"
                      aria-label={`Remove ${symptom}`}
                    >
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
            )}
            <p className="text-sm text-navy-500">{formData.associated_symptoms!.length}/20 symptoms</p>
          </div>
        );

      case 6:
        return (
          <div className="space-y-6">
            <StepHeader
              title="Warning Signs & Context"
              subtitle="Are you experiencing any warning signs? (Optional)"
            />
            <label htmlFor="warning-sign" className="-mb-4 block text-sm font-medium text-navy-700">
              Warning sign
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={warningSignInput}
                onChange={(e) => setWarningSignInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addWarningSign();
                  }
                }}
                placeholder="Add warning sign"
                className={`${inputClass} flex-1`}
                maxLength={500}
                id="warning-sign"
                aria-label="Warning sign"
                autoComplete="off"
              />
              <button
                type="button"
                onClick={addWarningSign}
                disabled={!warningSignInput.trim() || formData.warning_signs!.length >= 20}
                className="rounded-xl bg-teal-600 px-6 py-4 font-semibold text-white transition duration-150 hover:bg-teal-700 active:scale-[0.97] disabled:cursor-not-allowed disabled:bg-navy-200 disabled:text-navy-500"
              >
                Add
              </button>
            </div>
            {formData.warning_signs!.length > 0 && (
              <ul className="space-y-2">
                {formData.warning_signs!.map((sign, index) => (
                  <li
                    key={index}
                    className="flex animate-fade-in items-center justify-between gap-3 rounded-xl border border-red-200 bg-red-50 p-3"
                  >
                    <span className="break-words text-red-800">{sign}</span>
                    <button
                      type="button"
                      onClick={() => removeWarningSign(index)}
                      className="rounded-lg px-3 py-1 text-sm font-medium text-red-600 transition-colors hover:bg-red-100 hover:text-red-700"
                      aria-label={`Remove ${sign}`}
                    >
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
            )}
            <div>
              <label htmlFor="context" className="mb-2 block text-sm font-medium text-navy-700">
                Additional Context (Optional)
              </label>
              <textarea
                id="context"
                value={formData.additional_context}
                onChange={(e) => updateField('additional_context', e.target.value)}
                placeholder="Any other relevant information..."
                className={`${inputClass} h-32 resize-y`}
                maxLength={1000}
                aria-label="Additional context"
              />
              <p className="mt-1 text-right text-sm text-navy-500">{formData.additional_context!.length}/1000 characters</p>
              <p className="mt-2 flex items-center gap-1.5 text-xs text-navy-500">
                <svg className="h-3.5 w-3.5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path
                    fillRule="evenodd"
                    d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z"
                    clipRule="evenodd"
                  />
                </svg>
                This information is not stored and is used only for this assessment.
              </p>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="mx-auto max-w-2xl animate-fade-up" ref={containerRef}>
      {/* Progress */}
      <div className="mb-6">
        <div className="mb-3 flex items-baseline justify-between gap-3 text-sm">
          <div className="flex flex-wrap items-baseline gap-x-3">
            <span className="font-semibold text-navy-900">Step {step} of {totalSteps}</span>
            <span className="text-navy-600">{STEP_TITLES[step - 1]}</span>
          </div>
          <span className="font-medium text-navy-600">{Math.round((step / totalSteps) * 100)}%</span>
        </div>
        <div
          role="progressbar"
          aria-label="Assessment progress"
          aria-valuenow={step}
          aria-valuemin={1}
          aria-valuemax={totalSteps}
          aria-valuetext={`Step ${step} of ${totalSteps}: ${STEP_TITLES[step - 1]}`}
          className="flex gap-1.5"
        >
          {Array.from({ length: totalSteps }, (_, i) => (
            <span key={i} className="h-1.5 flex-1 overflow-hidden rounded-full bg-navy-200">
              <span
                className={`block h-full origin-left rounded-full bg-teal-600 transition-transform duration-500 ease-out ${
                  i + 1 <= step ? 'scale-x-100' : 'scale-x-0'
                }`}
              />
            </span>
          ))}
        </div>
      </div>

      {/* Form content */}
      <div
        key={step}
        className={`${forward ? 'animate-step-in' : 'animate-step-back'} rounded-3xl border border-navy-100 bg-white p-6 shadow-card sm:p-8`}
      >
        {renderStep()}
      </div>

      {/* Navigation */}
      {!isStepValid() && STEP_HINTS[step] && (
        <p className="mt-4 text-sm text-navy-600">{STEP_HINTS[step]}</p>
      )}
      <div className="mt-4 flex items-center justify-between gap-3">
        <button
          type="button"
          onClick={handleBack}
          disabled={step === 1}
          className="rounded-xl border border-navy-300 bg-white px-6 py-3 font-medium text-navy-700 transition duration-150 hover:bg-navy-50 active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-50"
        >
          Back
        </button>
        <button
          type="button"
          onClick={handleNext}
          disabled={!isStepValid() || isLoading}
          className="inline-flex items-center gap-2 rounded-xl bg-teal-600 px-8 py-3 font-semibold text-white shadow-sm transition duration-150 hover:bg-teal-700 active:scale-[0.97] disabled:cursor-not-allowed disabled:bg-navy-200 disabled:text-navy-500 disabled:shadow-none"
        >
          {isLoading && (
            <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
            </svg>
          )}
          {isLoading ? 'Processing...' : step === totalSteps ? 'Get Assessment' : 'Continue'}
        </button>
      </div>
    </div>
  );
}
