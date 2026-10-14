export function Disclaimer() {
  return (
    <div
      className="mb-6 flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 sm:mb-8"
      role="alert"
    >
      <svg
        className="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-500"
        viewBox="0 0 20 20"
        fill="currentColor"
        aria-hidden="true"
      >
        <path
          fillRule="evenodd"
          d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
          clipRule="evenodd"
        />
      </svg>
      <p className="text-sm leading-relaxed text-amber-900">
        <strong>Medical Disclaimer:</strong> This tool provides general information only and is not a
        substitute for professional medical advice, diagnosis, or treatment. If you have a medical
        emergency, call your local emergency number immediately (112 in India).
      </p>
    </div>
  );
}
