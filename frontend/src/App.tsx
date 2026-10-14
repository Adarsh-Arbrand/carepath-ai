import { useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { Disclaimer } from './components/Disclaimer';
import { Questionnaire } from './components/Questionnaire';
import { Results } from './components/Results';
import type { SymptomRequest, AssessmentResponse } from './types';
import { assessSymptoms, getConfig } from './api';

type ViewState = 'landing' | 'questionnaire' | 'results' | 'about' | 'privacy';

const NAV_ITEMS: { view: ViewState; label: string }[] = [
  { view: 'landing', label: 'Home' },
  { view: 'about', label: 'About' },
  { view: 'privacy', label: 'Privacy' },
];

function friendlyError(err: unknown): string {
  if (err instanceof TypeError || (err instanceof Error && /failed to fetch|network/i.test(err.message))) {
    return "We couldn't reach the assessment service. Please check your connection and try again.";
  }
  return err instanceof Error ? err.message : 'An unexpected error occurred';
}

function LogoMark() {
  return (
    <span
      aria-hidden="true"
      className="flex h-9 w-9 items-center justify-center rounded-xl bg-teal-800 sm:h-10 sm:w-10 text-teal-300 shadow-md shadow-teal-900/20"
    >
      <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 12h4l2-5 4 10 2-5h6" />
      </svg>
    </span>
  );
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="mx-auto max-w-3xl animate-fade-up rounded-3xl border border-navy-100 bg-white p-6 shadow-card sm:p-10">
      <h2 className="mb-8 font-display text-3xl font-bold tracking-tight text-navy-900 sm:text-4xl">{title}</h2>
      <div className="space-y-8 leading-relaxed text-navy-700">{children}</div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section>
      <h3 className="mb-3 font-display text-xl font-bold text-navy-900">{title}</h3>
      {children}
    </section>
  );
}

function Bullets({ items, tone = 'default' }: { items: string[]; tone?: 'default' | 'negative' }) {
  return (
    <ul className="mt-2 space-y-2">
      {items.map((item) => (
        <li key={item} className="flex items-start gap-3">
          <span
            aria-hidden="true"
            className={`mt-2 h-1.5 w-1.5 flex-shrink-0 rounded-full ${tone === 'negative' ? 'bg-red-400' : 'bg-teal-500'}`}
          />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

const FEATURES = [
  {
    title: 'Guided Assessment',
    text: 'Answer simple questions about your symptoms in a step-by-step format.',
    path: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2',
  },
  {
    title: 'Safety First',
    text: 'Built-in safety checks identify warning signs based on reputable medical guidance.',
    path: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
  },
  {
    title: 'Clear Guidance',
    text: 'Get actionable next steps with explanations of the reasoning behind recommendations.',
    path: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  },
];

const HOW_IT_WORKS = [
  { title: 'Tell us what\u2019s happening', text: 'Six quick steps: age group, main symptom, timing, severity and any warning signs.' },
  { title: 'Safety rules run first', text: 'A deterministic engine checks for red-flag symptoms before any AI is involved.' },
  { title: 'Get a clear next step', text: 'See whether to seek emergency, urgent or routine care, and why.' },
];

const LEVELS = [
  {
    label: 'Emergency',
    text: 'Call 112 right away',
    chip: 'bg-red-100 text-red-700',
    icon: 'M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z',
  },
  {
    label: 'Urgent',
    text: 'Seek care soon',
    chip: 'bg-orange-100 text-orange-800',
    icon: 'M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.5 2.5a1 1 0 001.414-1.414L11 9.586V6z',
  },
  {
    label: 'Routine',
    text: 'Book a regular visit',
    chip: 'bg-green-100 text-green-800',
    icon: 'M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z',
  },
];

function App() {
  const [view, setView] = useState<ViewState>('landing');
  const [assessment, setAssessment] = useState<AssessmentResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSlow, setIsSlow] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mainRef = useRef<HTMLElement>(null);
  const isFirstRender = useRef(true);

  // Warm up the backend (free-tier hosts sleep when idle) so the first assessment is faster.
  useEffect(() => {
    getConfig().catch(() => {});
  }, []);

  // On every view change: scroll to top and move focus to the main region for assistive tech.
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    window.scrollTo({ top: 0 });
    mainRef.current?.focus({ preventScroll: true });
  }, [view]);

  // If a request takes a while, explain why instead of leaving the user guessing.
  useEffect(() => {
    if (!isLoading) {
      setIsSlow(false);
      return;
    }
    const timer = window.setTimeout(() => setIsSlow(true), 4000);
    return () => window.clearTimeout(timer);
  }, [isLoading]);

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
      setError(friendlyError(err));
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
    <div className="app-bg flex min-h-screen flex-col">
      <a href="#main" className="skip-link">
        Skip to main content
      </a>

      {/* Header */}
      <header className="sticky top-0 z-30 border-b border-navy-200/70 bg-paper/85 backdrop-blur-md print:hidden">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3">
          <button
            type="button"
            onClick={() => setView('landing')}
            className="flex items-center gap-2.5 rounded-lg text-left sm:gap-3"
            aria-label="CarePath AI home"
          >
            <LogoMark />
            <h1 className="whitespace-nowrap font-display text-lg font-bold tracking-tight text-navy-900 sm:text-2xl">CarePath AI</h1>
          </button>
          <nav aria-label="Primary" className="flex gap-1">
            {NAV_ITEMS.map((item) => {
              const active = view === item.view;
              return (
                <button
                  key={item.view}
                  onClick={() => setView(item.view)}
                  aria-current={active ? 'page' : undefined}
                  className={`rounded-lg px-2.5 py-2 text-sm font-medium transition-colors sm:px-4 ${
                    active ? 'bg-teal-100 text-teal-800' : 'text-navy-600 hover:bg-navy-100 hover:text-teal-700'
                  }`}
                >
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main id="main" ref={mainRef} tabIndex={-1} className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:py-10">
        {view !== 'results' && <Disclaimer />}

        {error && (
          <div
            className="mb-6 animate-fade-in rounded-xl border border-red-200 border-l-4 border-l-red-500 bg-red-50 p-4"
            role="alert"
          >
            <p className="text-red-800">{error}</p>
            <button
              onClick={() => setError(null)}
              className="mt-2 rounded text-sm font-medium text-red-600 underline hover:text-red-700"
            >
              Dismiss
            </button>
          </div>
        )}

        {view === 'landing' && (
          <div>
            <section className="grid items-center gap-10 py-4 sm:py-10 lg:grid-cols-[1.1fr_1fr] lg:gap-16">
              <div>
                <p
                  className="animate-fade-up mb-4 text-sm font-semibold tracking-wide text-teal-700"
                  style={{ animationDelay: '0ms' }}
                >
                  Intelligent Healthcare Navigation
                </p>
                <h2
                  className="hero-title animate-fade-up font-display text-[2.6rem] font-bold leading-[1.04] tracking-tight text-navy-900 sm:text-6xl"
                  style={{ animationDelay: '60ms' }}
                >
                  Understand your health. Take the right next step.
                </h2>
                <p
                  className="animate-fade-up mt-5 max-w-xl text-lg leading-relaxed text-navy-600"
                  style={{ animationDelay: '120ms' }}
                >
                  Answer a few questions about your symptoms. Safety rules run first, then you see whether to seek
                  emergency, urgent or routine care, and why.
                </p>
                <div
                  className="animate-fade-up mt-8 flex flex-wrap items-center gap-x-6 gap-y-3"
                  style={{ animationDelay: '180ms' }}
                >
                  <button
                    onClick={handleStartAssessment}
                    className="group inline-flex items-center gap-2 rounded-xl bg-teal-600 px-8 py-4 text-lg font-semibold text-white shadow-lg shadow-teal-900/20 transition duration-200 hover:bg-teal-700 active:scale-[0.97]"
                  >
                    Start Assessment
                    <svg className="h-5 w-5 transition-transform duration-200 group-hover:translate-x-1" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                      <path fillRule="evenodd" d="M10.3 3.3a1 1 0 011.4 0l6 6a1 1 0 010 1.4l-6 6a1 1 0 01-1.4-1.4L14.6 11H3a1 1 0 110-2h11.6l-4.3-4.3a1 1 0 010-1.4z" clipRule="evenodd" />
                    </svg>
                  </button>
                  <button
                    type="button"
                    onClick={() => document.getElementById('how-it-works')?.scrollIntoView?.({ block: 'start' })}
                    className="rounded-md py-2 text-base font-medium text-navy-700 underline decoration-navy-300 underline-offset-4 transition-colors hover:text-teal-700 hover:decoration-teal-500"
                  >
                    How it works
                  </button>
                </div>
                <p className="animate-fade-up mt-4 text-sm text-navy-500" style={{ animationDelay: '220ms' }}>
                  Takes about two minutes. No sign-up. Nothing is stored.
                </p>
              </div>

              {/* Hero visual: the three possible outcomes as a stepped path, with one ECG line drawn once. */}
              <div className="animate-fade-up relative mx-auto w-full max-w-md" style={{ animationDelay: '140ms' }}>
                <div
                  aria-hidden="true"
                  className="absolute -inset-6 -z-10 rounded-[2rem] bg-[radial-gradient(closest-side,rgb(138_219_203/0.35),transparent)]"
                />
                <svg viewBox="0 0 400 56" className="mb-4 h-12 w-full text-teal-600" fill="none" aria-hidden="true">
                  <path
                    d="M0 30h118l16-22 24 44 20-34 14 12h208"
                    pathLength={1}
                    stroke="currentColor"
                    strokeWidth={2.5}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeDasharray={1}
                    className="animate-draw"
                  />
                </svg>
                <ul
                  className="relative space-y-3"
                  aria-label="Urgency levels"
                >
                  {LEVELS.map((level, i) => (
                    <li
                      key={level.label}
                      className="animate-fade-up relative flex items-center gap-4 rounded-2xl border border-navy-100 bg-white px-4 py-3.5 shadow-card"
                      style={{ animationDelay: `${260 + i * 90}ms`, marginLeft: `${i * 1.25}rem` }}
                    >
                      <span
                        aria-hidden="true"
                        className={`flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full ${level.chip}`}
                      >
                        <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d={level.icon} clipRule="evenodd" /></svg>
                      </span>
                      <span>
                        <span className="block font-semibold text-navy-900">{level.label}</span>
                        <span className="block text-sm text-navy-600">{level.text}</span>
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </section>

            <section className="mx-auto mt-14 grid max-w-5xl grid-cols-1 gap-x-10 gap-y-8 sm:mt-20 md:grid-cols-3">
              {FEATURES.map((feature, i) => (
                <div
                  key={feature.title}
                  className="animate-fade-up border-t-2 border-navy-900 pt-5"
                  style={{ animationDelay: `${i * 90}ms` }}
                >
                  <svg className="mb-4 h-7 w-7 text-teal-700" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d={feature.path} />
                  </svg>
                  <h3 className="mb-2 font-display text-xl font-bold text-navy-900">{feature.title}</h3>
                  <p className="leading-relaxed text-navy-600">{feature.text}</p>
                </div>
              ))}
            </section>

            <section
              className="mx-auto mt-16 max-w-5xl scroll-mt-24 rounded-3xl border border-navy-100 bg-white p-6 shadow-card sm:mt-20 sm:p-10"
              aria-labelledby="how-it-works"
            >
              <h2 id="how-it-works" className="mb-8 font-display text-2xl font-bold tracking-tight text-navy-900 sm:text-3xl">
                How it works
              </h2>
              <ol className="grid grid-cols-1 gap-8 md:grid-cols-3 md:gap-10">
                {HOW_IT_WORKS.map((item, i) => (
                  <li
                    key={item.title}
                    className={`relative ${
                      i < HOW_IT_WORKS.length - 1
                        ? 'md:after:absolute md:after:left-12 md:after:right-[-1.5rem] md:after:top-[1.1rem] md:after:h-px md:after:bg-navy-300 md:after:content-[\'\']'
                        : ''
                    }`}
                  >
                    <span
                      aria-hidden="true"
                      className="relative z-10 mb-4 flex h-9 w-9 items-center justify-center rounded-full bg-teal-700 text-sm font-bold text-white"
                    >
                      {i + 1}
                    </span>
                    <h3 className="mb-2 text-lg font-semibold text-navy-900">{item.title}</h3>
                    <p className="text-sm leading-relaxed text-navy-600">{item.text}</p>
                  </li>
                ))}
              </ol>
            </section>
          </div>
        )}

        {view === 'questionnaire' && (
          <>
            <Questionnaire onSubmit={handleAssessmentSubmit} isLoading={isLoading} />
            {isLoading && (
              <div
                role="status"
                aria-live="polite"
                className="mx-auto mt-6 flex max-w-2xl animate-fade-in items-start gap-3 rounded-xl border border-teal-200 bg-teal-50 p-4 text-teal-900"
              >
                <svg className="mt-0.5 h-5 w-5 flex-shrink-0 animate-spin text-teal-600" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                </svg>
                <p className="text-sm">
                  Reviewing your answers against safety guidance&hellip;
                  {isSlow && (
                    <span className="mt-1 block text-teal-800">
                      The service may be waking up after being idle. The first request can take up to a minute.
                    </span>
                  )}
                </p>
              </div>
            )}
          </>
        )}

        {view === 'results' && assessment && (
          <>
            <Results response={assessment} onReset={handleReset} />
            <div className="mx-auto mt-8 max-w-3xl">
              <Disclaimer />
            </div>
          </>
        )}

        {view === 'about' && (
          <Panel title="About CarePath AI">
            <Section title="Purpose">
              <p>
                CarePath AI is an intelligent healthcare navigation assistant designed to help people
                understand appropriate next steps when experiencing health concerns. It provides
                informational guidance on when to seek emergency care, urgent medical attention,
                or routine evaluation.
              </p>
            </Section>

            <Section title="What It Does">
              <Bullets
                items={[
                  'Gathers symptom-related context through a guided questionnaire',
                  'Asks relevant follow-up questions when information is unclear',
                  'Identifies potential warning signs based on reputable medical guidance',
                  'Provides safe, explainable guidance on appropriate next steps',
                  'Uses AI to provide explanatory context when available',
                ]}
              />
            </Section>

            <Section title="What It Does NOT Do">
              <Bullets
                tone="negative"
                items={[
                  'It does NOT diagnose medical conditions',
                  'It does NOT rule out diseases or conditions',
                  'It does NOT provide medical treatment recommendations',
                  'It is NOT a substitute for professional medical evaluation',
                  'It has NOT been clinically validated',
                ]}
              />
            </Section>

            <Section title="Safety Design">
              <p>
                CarePath AI uses a deterministic safety engine that runs independently of any AI system.
                This engine is based on conservative rules derived from reputable public health sources
                including the NHS (UK), Mayo Clinic, American Heart Association, CDC, and WHO.
                The system is designed to err on the side of caution - when in doubt, it recommends
                seeking professional medical evaluation.
              </p>
            </Section>

            <Section title="Privacy">
              <p>
                This tool does not store assessment histories or symptoms in a database by default.
                No names, addresses, government IDs, or unnecessary identifying information is collected.
                Information provided during an assessment is used only for that specific assessment
                and is not retained or used for any other purpose.
              </p>
            </Section>

            <Section title="Emergency Guidance">
              <p>
                If you are experiencing a medical emergency, call your local emergency services
                immediately. In India, the emergency number is 112. In the United States, it is 911.
                Do not rely on this tool for emergency situations.
              </p>
            </Section>
          </Panel>
        )}

        {view === 'privacy' && (
          <Panel title="Privacy Information">
            <Section title="Data Collection">
              <p>CarePath AI collects only the information necessary to provide an assessment:</p>
              <Bullets
                items={[
                  'Age group (not specific date of birth)',
                  'Symptom descriptions',
                  'Duration and onset information',
                  'Severity level',
                  'Associated symptoms and warning signs (optional)',
                  'Additional context (optional)',
                ]}
              />
              <p className="mt-4">We do NOT collect:</p>
              <Bullets
                tone="negative"
                items={['Names', 'Precise addresses', 'Government IDs', 'Contact information (phone, email)', 'Medical history records']}
              />
            </Section>

            <Section title="Data Storage">
              <p>
                By default, this tool does NOT store assessment histories or symptoms in a database.
                Information provided during an assessment is processed to generate guidance and then
                discarded. No localStorage or analytics are used to retain sensitive symptom details.
              </p>
            </Section>

            <Section title="Data Usage">
              <p>
                The information you provide is used solely for the purpose of generating an assessment
                and appropriate guidance. It is not:
              </p>
              <Bullets
                tone="negative"
                items={[
                  'Sold to third parties',
                  'Used for advertising',
                  'Shared with other users',
                  'Used for research without explicit consent',
                ]}
              />
            </Section>

            <Section title="Security">
              <p>
                All data transmission is encrypted using HTTPS. API keys for AI services are stored
                server-side and never exposed to the frontend. Request bodies containing health
                information are not logged.
              </p>
            </Section>

            <Section title="Your Rights">
              <p>
                Since we do not store your data, there is no personal data to delete, export, or modify.
                If you have concerns about privacy, you can simply close the browser window - no
                information will be retained.
              </p>
            </Section>

            <Section title="Children's Privacy">
              <p>
                This tool may be used to assess symptoms for children, but we do not collect
                personally identifiable information about children. Parents and guardians should
                supervise children's use of this tool.
              </p>
            </Section>

            <Section title="Changes to Privacy Policy">
              <p>
                Any changes to this privacy policy will be posted here with an updated revision date.
                We encourage you to review this policy periodically.
              </p>
            </Section>
          </Panel>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-12 bg-teal-950 py-10 text-white print:hidden">
        <div className="mx-auto max-w-6xl px-4 text-center">
          <p className="mb-2 text-navy-300">
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
