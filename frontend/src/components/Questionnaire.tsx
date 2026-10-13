import { useState } from 'react';
import { AgeGroup, SymptomRequest } from '../types';

interface QuestionnaireProps {
  onSubmit: (data: SymptomRequest) => void;
  isLoading: boolean;
}

export function Questionnaire({ onSubmit, isLoading }: QuestionnaireProps) {
  const [step, setStep] = useState(1);
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
      setStep(step + 1);
    } else {
      onSubmit(formData as SymptomRequest);
    }
  };

  const handleBack = () => {
    if (step > 1) {
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
          <div className="space-y-4">
            <h2 className="text-2xl font-semibold text-navy-900">Age Group</h2>
            <p className="text-navy-600">Please select the age group of the person experiencing symptoms.</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { value: '0-2', label: 'Infant (0-2 years)' },
                { value: '3-12', label: 'Child (3-12 years)' },
                { value: '13-17', label: 'Teen (13-17 years)' },
                { value: '18-64', label: 'Adult (18-64 years)' },
                { value: '65+', label: 'Senior (65+ years)' },
              ].map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => updateField('age_group', option.value as AgeGroup)}
                  className={`p-4 rounded-lg border-2 text-left transition-all ${
                    formData.age_group === option.value
                      ? 'border-teal-600 bg-teal-50 text-teal-900'
                      : 'border-navy-200 hover:border-teal-400 text-navy-700'
                  }`}
                  aria-pressed={formData.age_group === option.value}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-4">
            <h2 className="text-2xl font-semibold text-navy-900">Main Symptom</h2>
            <p className="text-navy-600">What is the primary symptom or concern?</p>
            <input
              type="text"
              value={formData.main_symptom}
              onChange={(e) => updateField('main_symptom', e.target.value)}
              placeholder="e.g., headache, stomach pain, fever"
              className="w-full p-4 border-2 border-navy-200 rounded-lg focus:border-teal-600 focus:outline-none"
              maxLength={500}
              aria-label="Main symptom"
            />
            <p className="text-sm text-navy-500">{formData.main_symptom!.length}/500 characters</p>
          </div>
        );

      case 3:
        return (
          <div className="space-y-4">
            <h2 className="text-2xl font-semibold text-navy-900">Duration & Onset</h2>
            <p className="text-navy-600">How long have you had this symptom, and when did it start?</p>
            <div>
              <label htmlFor="duration" className="block text-sm font-medium text-navy-700 mb-2">
                Duration
              </label>
              <input
                id="duration"
                type="text"
                value={formData.duration}
                onChange={(e) => updateField('duration', e.target.value)}
                placeholder="e.g., 2 hours, 3 days, 1 week"
                className="w-full p-4 border-2 border-navy-200 rounded-lg focus:border-teal-600 focus:outline-none"
                maxLength={200}
                aria-label="Duration of symptoms"
              />
            </div>
            <div>
              <label htmlFor="onset" className="block text-sm font-medium text-navy-700 mb-2">
                Onset
              </label>
              <input
                id="onset"
                type="text"
                value={formData.onset}
                onChange={(e) => updateField('onset', e.target.value)}
                placeholder="e.g., sudden, gradual, after eating"
                className="w-full p-4 border-2 border-navy-200 rounded-lg focus:border-teal-600 focus:outline-none"
                maxLength={200}
                aria-label="How symptoms started"
              />
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-4">
            <h2 className="text-2xl font-semibold text-navy-900">Severity</h2>
            <p className="text-navy-600">How would you describe the severity?</p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[
                { value: 'mild', label: 'Mild' },
                { value: 'moderate', label: 'Moderate' },
                { value: 'severe', label: 'Severe' },
              ].map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => updateField('severity', option.value)}
                  className={`p-4 rounded-lg border-2 text-left transition-all ${
                    formData.severity === option.value
                      ? 'border-teal-600 bg-teal-50 text-teal-900'
                      : 'border-navy-200 hover:border-teal-400 text-navy-700'
                  }`}
                  aria-pressed={formData.severity === option.value}
                >
                  {option.label}
                </button>
              ))}
            </div>
            <input
              type="text"
              value={formData.severity}
              onChange={(e) => updateField('severity', e.target.value)}
              placeholder="Or describe severity in your own words"
              className="w-full p-4 border-2 border-navy-200 rounded-lg focus:border-teal-600 focus:outline-none"
              maxLength={200}
              aria-label="Severity description"
            />
          </div>
        );

      case 5:
        return (
          <div className="space-y-4">
            <h2 className="text-2xl font-semibold text-navy-900">Additional Symptoms</h2>
            <p className="text-navy-600">Are you experiencing any other symptoms? (Optional)</p>
            <div className="flex gap-2">
              <input
                type="text"
                value={associatedSymptomInput}
                onChange={(e) => setAssociatedSymptomInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && addAssociatedSymptom()}
                placeholder="Add associated symptom"
                className="flex-1 p-4 border-2 border-navy-200 rounded-lg focus:border-teal-600 focus:outline-none"
                maxLength={500}
                aria-label="Associated symptom"
              />
              <button
                type="button"
                onClick={addAssociatedSymptom}
                disabled={!associatedSymptomInput.trim() || formData.associated_symptoms!.length >= 20}
                className="px-6 py-4 bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:bg-navy-300 disabled:cursor-not-allowed transition-colors"
              >
                Add
              </button>
            </div>
            {formData.associated_symptoms!.length > 0 && (
              <div className="space-y-2">
                {formData.associated_symptoms!.map((symptom, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-navy-50 rounded-lg">
                    <span className="text-navy-700">{symptom}</span>
                    <button
                      type="button"
                      onClick={() => removeAssociatedSymptom(index)}
                      className="text-red-600 hover:text-red-700 px-3 py-1"
                      aria-label={`Remove ${symptom}`}
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            )}
            <p className="text-sm text-navy-500">{formData.associated_symptoms!.length}/20 symptoms</p>
          </div>
        );

      case 6:
        return (
          <div className="space-y-4">
            <h2 className="text-2xl font-semibold text-navy-900">Warning Signs & Context</h2>
            <p className="text-navy-600">Are you experiencing any warning signs? (Optional)</p>
            <div className="flex gap-2">
              <input
                type="text"
                value={warningSignInput}
                onChange={(e) => setWarningSignInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && addWarningSign()}
                placeholder="Add warning sign"
                className="flex-1 p-4 border-2 border-navy-200 rounded-lg focus:border-teal-600 focus:outline-none"
                maxLength={500}
                aria-label="Warning sign"
              />
              <button
                type="button"
                onClick={addWarningSign}
                disabled={!warningSignInput.trim() || formData.warning_signs!.length >= 20}
                className="px-6 py-4 bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:bg-navy-300 disabled:cursor-not-allowed transition-colors"
              >
                Add
              </button>
            </div>
            {formData.warning_signs!.length > 0 && (
              <div className="space-y-2">
                {formData.warning_signs!.map((sign, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-red-50 rounded-lg border border-red-200">
                    <span className="text-red-700">{sign}</span>
                    <button
                      type="button"
                      onClick={() => removeWarningSign(index)}
                      className="text-red-600 hover:text-red-700 px-3 py-1"
                      aria-label={`Remove ${sign}`}
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            )}
            <div className="mt-6">
              <label htmlFor="context" className="block text-sm font-medium text-navy-700 mb-2">
                Additional Context (Optional)
              </label>
              <textarea
                id="context"
                value={formData.additional_context}
                onChange={(e) => updateField('additional_context', e.target.value)}
                placeholder="Any other relevant information..."
                className="w-full p-4 border-2 border-navy-200 rounded-lg focus:border-teal-600 focus:outline-none h-32"
                maxLength={1000}
                aria-label="Additional context"
              />
              <p className="text-sm text-navy-500 mt-1">{formData.additional_context!.length}/1000 characters</p>
              <p className="text-xs text-navy-400 mt-2">
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
    <div className="max-w-2xl mx-auto">
      {/* Progress bar */}
      <div className="mb-8">
        <div className="flex justify-between text-sm text-navy-600 mb-2">
          <span>Step {step} of {totalSteps}</span>
          <span>{Math.round((step / totalSteps) * 100)}%</span>
        </div>
        <div className="w-full bg-navy-200 rounded-full h-2">
          <div
            className="bg-teal-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${(step / totalSteps) * 100}%` }}
            role="progressbar"
            aria-valuenow={step}
            aria-valuemin={1}
            aria-valuemax={totalSteps}
          />
        </div>
      </div>

      {/* Form content */}
      <div className="bg-white rounded-xl shadow-lg p-8">
        {renderStep()}
      </div>

      {/* Navigation */}
      <div className="flex justify-between mt-6">
        <button
          type="button"
          onClick={handleBack}
          disabled={step === 1}
          className="px-6 py-3 border-2 border-navy-300 text-navy-700 rounded-lg hover:bg-navy-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Back
        </button>
        <button
          type="button"
          onClick={handleNext}
          disabled={!isStepValid() || isLoading}
          className="px-6 py-3 bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:bg-navy-300 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? 'Processing...' : step === totalSteps ? 'Get Assessment' : 'Continue'}
        </button>
      </div>
    </div>
  );
}
