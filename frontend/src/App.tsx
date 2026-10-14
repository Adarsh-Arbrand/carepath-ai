import { useState } from 'react';
import { Disclaimer } from './components/Disclaimer';
import { Questionnaire } from './components/Questionnaire';
import { Results } from './components/Results';
import type { SymptomRequest, AssessmentResponse } from './types';
import { assessSymptoms } from './api';

type ViewState = 'landing' | 'questionnaire' | 'results' | 'about' | 'privacy';

function App() {
  const [view, setView] = useState<ViewState>('landing');
  const [assessment, setAssessment] = useState<AssessmentResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleStartAssessment = () => {
    setView('questionnaire');
    setError(null);
  };

  const handleAssessmentSubmit = async (data: SymptomRequest) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await assessSymptoms(data);
      setAssessment(response);
      setView('results');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setAssessment(null);
    setView('landing');
    setError(null);
  };

  return (
    <div className="min-h-screen bg-[#fafaf9]">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-navy-200">
        <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-navy-900">CarePath AI</h1>
          <nav className="flex gap-4">
            <button
              onClick={() => setView('landing')}
              className="text-navy-600 hover:text-teal-600 transition-colors"
            >
              Home
            </button>
            <button
              onClick={() => setView('about')}
              className="text-navy-600 hover:text-teal-600 transition-colors"
            >
              About
            </button>
            <button
              onClick={() => setView('privacy')}
              className="text-navy-600 hover:text-teal-600 transition-colors"
            >
              Privacy
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        <Disclaimer />

        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6 rounded-r-xl" role="alert">
            <p className="text-red-800">{error}</p>
            <button
              onClick={() => setError(null)}
              className="mt-2 text-red-600 hover:text-red-700 underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {view === 'landing' && (
          <div className="text-center py-12">
            <h2 className="text-4xl font-bold text-navy-900 mb-4">
              Intelligent Healthcare Navigation
            </h2>
            <p className="text-xl text-navy-600 mb-8 max-w-2xl mx-auto">
              Get personalized guidance on appropriate next steps for your health concerns.
              This informational tool helps you understand when to seek emergency care,
              urgent attention, or routine medical evaluation.
            </p>
            <div className="flex flex-wrap gap-4 justify-center mb-12">
              <button
                onClick={handleStartAssessment}
                className="px-8 py-4 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition-colors text-lg font-semibold"
              >
                Start Assessment
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
              <div className="bg-white p-6 rounded-xl shadow-md">
                <div className="w-12 h-12 bg-teal-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="h-6 w-6 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-navy-900 mb-2">Guided Assessment</h3>
                <p className="text-navy-600">
                  Answer simple questions about your symptoms in a step-by-step format.
                </p>
              </div>

              <div className="bg-white p-6 rounded-xl shadow-md">
                <div className="w-12 h-12 bg-teal-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="h-6 w-6 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-navy-900 mb-2">Safety First</h3>
                <p className="text-navy-600">
                  Built-in safety checks identify warning signs based on reputable medical guidance.
                </p>
              </div>

              <div className="bg-white p-6 rounded-xl shadow-md">
                <div className="w-12 h-12 bg-teal-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="h-6 w-6 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-navy-900 mb-2">Clear Guidance</h3>
                <p className="text-navy-600">
                  Get actionable next steps with explanations of the reasoning behind recommendations.
                </p>
              </div>
            </div>
          </div>
        )}

        {view === 'questionnaire' && (
          <Questionnaire onSubmit={handleAssessmentSubmit} isLoading={isLoading} />
        )}

        {view === 'results' && assessment && (
          <Results response={assessment} onReset={handleReset} />
        )}

        {view === 'about' && (
          <div className="max-w-3xl mx-auto bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-3xl font-bold text-navy-900 mb-6">About CarePath AI</h2>
            <div className="space-y-6 text-navy-700">
              <section>
                <h3 className="text-xl font-semibold text-navy-900 mb-3">Purpose</h3>
                <p>
                  CarePath AI is an intelligent healthcare navigation assistant designed to help people
                  understand appropriate next steps when experiencing health concerns. It provides
                  informational guidance on when to seek emergency care, urgent medical attention,
                  or routine evaluation.
                </p>
              </section>

              <section>
                <h3 className="text-xl font-semibold text-navy-900 mb-3">What It Does</h3>
                <ul className="list-disc list-inside space-y-2">
                  <li>Gathers symptom-related context through a guided questionnaire</li>
                  <li>Asks relevant follow-up questions when information is unclear</li>
                  <li>Identifies potential warning signs based on reputable medical guidance</li>
                  <li>Provides safe, explainable guidance on appropriate next steps</li>
                  <li>Uses AI to provide explanatory context when available</li>
                </ul>
              </section>

              <section>
                <h3 className="text-xl font-semibold text-navy-900 mb-3">What It Does NOT Do</h3>
                <ul className="list-disc list-inside space-y-2">
                  <li>It does NOT diagnose medical conditions</li>
                  <li>It does NOT rule out diseases or conditions</li>
                  <li>It does NOT provide medical treatment recommendations</li>
                  <li>It is NOT a substitute for professional medical evaluation</li>
                  <li>It has NOT been clinically validated</li>
                </ul>
              </section>

              <section>
                <h3 className="text-xl font-semibold text-navy-900 mb-3">Safety Design</h3>
                <p>
                  CarePath AI uses a deterministic safety engine that runs independently of any AI system.
                  This engine is based on conservative rules derived from reputable public health sources
                  including the NHS (UK), Mayo Clinic, American Heart Association, CDC, and WHO.
                  The system is designed to err on the side of caution - when in doubt, it recommends
                  seeking professional medical evaluation.
                </p>
              </section>

              <section>
                <h3 className="text-xl font-semibold text-navy-900 mb-3">Privacy</h3>
                <p>
                  This tool does not store assessment histories or symptoms in a database by default.
                  No names, addresses, government IDs, or unnecessary identifying information is collected.
                  Information provided during an assessment is used only for that specific assessment
                  and is not retained or used for any other purpose.
                </p>
              </section>

              <section>
                <h3 className="text-xl font-semibold text-navy-900 mb-3">Emergency Guidance</h3>
                <p>
                  If you are experiencing a medical emergency, call your local emergency services
                  immediately. In India, the emergency number is 112. In the United States, it is 911.
                  Do not rely on this tool for emergency situations.
                </p>
              </section>
            </div>
          </div>
        )}

        {view === 'privacy' && (
          <div className="max-w-3xl mx-auto bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-3xl font-bold text-navy-900 mb-6">Privacy Information</h2>
            <div className="space-y-6 text-navy-700">
              <section>
                <h3 className="text-xl font-semibold text-navy-900 mb-3">Data Collection</h3>
                <p>
                  CarePath AI collects only the information necessary to provide an assessment:
                </p>
                <ul className="list-disc list-inside space-y-2 mt-2">
                  <li>Age group (not specific date of birth)</li>
                  <li>Symptom descriptions</li>
                  <li>Duration and onset information</li>
                  <li>Severity level</li>
                  <li>Associated symptoms and warning signs (optional)</li>
                  <li>Additional context (optional)</li>
                </ul>
                <p className="mt-3">
                  We do NOT collect:
                </p>
                <ul className="list-disc list-inside space-y-2">
                  <li>Names</li>
                  <li>Precise addresses</li>
                  <li>Government IDs</li>
                  <li>Contact information (phone, email)</li>
                  <li>Medical history records</li>
                </ul>
              </section>

              <section>
                <h3 className="text-xl font-semibold text-navy-900 mb-3">Data Storage</h3>
                <p>
                  By default, this tool does NOT store assessment histories or symptoms in a database.
                  Information provided during an assessment is processed to generate guidance and then
                  discarded. No localStorage or analytics are used to retain sensitive symptom details.
                </p>
              </section>

              <section>
                <h3 className="text-xl font-semibold text-navy-900 mb-3">Data Usage</h3>
                <p>
                  The information you provide is used solely for the purpose of generating an assessment
                  and appropriate guidance. It is not:
                </p>
                <ul className="list-disc list-inside space-y-2 mt-2">
                  <li>Sold to third parties</li>
                  <li>Used for advertising</li>
                  <li>Shared with other users</li>
                  <li>Used for research without explicit consent</li>
                </ul>
              </section>

              <section>
                <h3 className="text-xl font-semibold text-navy-900 mb-3">Security</h3>
                <p>
                  All data transmission is encrypted using HTTPS. API keys for AI services are stored
                  server-side and never exposed to the frontend. Request bodies containing health
                  information are not logged.
                </p>
              </section>

              <section>
                <h3 className="text-xl font-semibold text-navy-900 mb-3">Your Rights</h3>
                <p>
                  Since we do not store your data, there is no personal data to delete, export, or modify.
                  If you have concerns about privacy, you can simply close the browser window - no
                  information will be retained.
                </p>
              </section>

              <section>
                <h3 className="text-xl font-semibold text-navy-900 mb-3">Children's Privacy</h3>
                <p>
                  This tool may be used to assess symptoms for children, but we do not collect
                  personally identifiable information about children. Parents and guardians should
                  supervise children's use of this tool.
                </p>
              </section>

              <section>
                <h3 className="text-xl font-semibold text-navy-900 mb-3">Changes to Privacy Policy</h3>
                <p>
                  Any changes to this privacy policy will be posted here with an updated revision date.
                  We encourage you to review this policy periodically.
                </p>
              </section>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-navy-900 text-white py-8 mt-12">
        <div className="max-w-6xl mx-auto px-4 text-center">
          <p className="text-navy-300 mb-2">
            CarePath AI - Hack2Skill PromptWars × HackWkie AI Code Submission
          </p>
          <p className="text-sm text-navy-400">
            This is a demonstration prototype. Not a certified medical device. Not clinically validated.
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
