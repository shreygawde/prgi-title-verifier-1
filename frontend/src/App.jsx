import { useState } from "react";

// ---------------------------------------------------------------------------
// Static reference data
// ---------------------------------------------------------------------------

const LANGUAGES = [
  "English",
  "Hindi",
  "Marathi",
  "Gujarati",
  "Bengali",
  "Tamil",
  "Telugu",
  "Kannada",
  "Malayalam",
  "Punjabi",
  "Urdu",
];

const PERIODICITIES = ["Daily", "Weekly", "Fortnightly", "Monthly", "Quarterly"];

// PRGI institutional blue, pulled closer to the tone used on prgi.gov.in.
const PRGI_BLUE = "#0B3B70";

// Verification-status presentation. Keys are normalized (lowercase, underscored)
// so the UI tolerates several backend spellings. Kept muted/institutional
// rather than bright pill-badge colors.
const STATUS_CONFIG = {
  rejected: {
    label: "Rejected",
    text: "text-red-800",
    border: "border-red-700",
    bar: "bg-red-700",
  },
  likely_eligible: {
    label: "Likely Eligible",
    text: "text-emerald-800",
    border: "border-emerald-700",
    bar: "bg-emerald-700",
  },
  needs_review: {
    label: "Needs Review",
    text: "text-amber-800",
    border: "border-amber-600",
    bar: "bg-amber-600",
  },
};

const DEFAULT_STATUS = {
  label: "Result received",
  text: "text-slate-700",
  border: "border-slate-500",
  bar: "bg-slate-500",
};

function normalizeStatusKey(status) {
  if (!status) return null;
  return String(status).trim().toLowerCase().replace(/\s+/g, "_");
}

function formatScore(score) {
  if (score === null || score === undefined || Number.isNaN(Number(score))) {
    return null;
  }
  // The AI service returns scores on a 0-100 scale already — display as-is.
  return Math.round(Number(score));
}

function formatMatchTypes(matchTypes) {
  if (!Array.isArray(matchTypes) || matchTypes.length === 0) return "—";
  return matchTypes.join(", ");
}

function formatGeneratedTimestamp() {
  return new Date().toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ---------------------------------------------------------------------------
// Small presentational pieces
// ---------------------------------------------------------------------------

function FieldLabel({ children, htmlFor }) {
  return (
    <label
      htmlFor={htmlFor}
      className="mb-1.5 block text-[13px] font-medium tracking-wide text-slate-600"
    >
      {children}
    </label>
  );
}

function SectionHeading({ title, description }) {
  return (
    <div className="mb-5">
      <h2
        className="font-serif text-[20px] font-semibold text-slate-900"
        style={{ borderLeft: `3px solid ${PRGI_BLUE}`, paddingLeft: "12px" }}
      >
        {title}
      </h2>
      {description && (
        <p className="mt-1.5 max-w-3xl pl-[15px] text-[13.5px] leading-relaxed text-slate-500">
          {description}
        </p>
      )}
    </div>
  );
}

function ReportField({ label, value }) {
  return (
    <div className="border-b border-slate-200 py-2.5 sm:border-b-0 sm:py-0">
      <p className="text-[11px] uppercase tracking-wide text-slate-400">
        {label}
      </p>
      <p className="mt-0.5 text-[14px] font-medium text-slate-900">{value}</p>
    </div>
  );
}

function SimilarityBar({ label, value }) {
  const pct = formatScore(value);
  if (pct === null) return null;
  return (
    <div className="flex items-center gap-4 py-2.5">
      <span className="w-44 shrink-0 text-[13px] text-slate-600">{label}</span>
      <div className="h-1.5 flex-1 overflow-hidden bg-slate-100">
        <div
          className="h-full"
          style={{ width: `${pct}%`, backgroundColor: PRGI_BLUE }}
        />
      </div>
      <span className="w-10 shrink-0 text-right text-[13px] tabular-nums font-medium text-slate-700">
        {pct}%
      </span>
    </div>
  );
}

function EmptyRow({ children }) {
  return (
    <div className="border border-dashed border-slate-300 bg-slate-50/60 px-5 py-6 text-center text-[13px] text-slate-500">
      {children}
    </div>
  );
}

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------

function App() {
  const [title, setTitle] = useState("");
  const [language, setLanguage] = useState("English");
  const [periodicity, setPeriodicity] = useState("Daily");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [generatedAt, setGeneratedAt] = useState(null);

  const handleVerify = async () => {
    if (!title.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:8001/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title,
          language,
          periodicity,
        }),
      });

      if (!response.ok) {
        throw new Error("Verification request failed");
      }

      const data = await response.json();

      setResult({
        ...data,
        submitted_title: title,
      });
      setGeneratedAt(formatGeneratedTimestamp());
    } catch (err) {
      console.error(err);
      setError(
        "Unable to reach the verification service. Confirm the server is running and try again."
      );
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  // Normalize backend fields so the UI tolerates the current database-only
  // response shape as well as the richer AI-assisted response described in
  // the product spec.
  const statusKey = normalizeStatusKey(result?.status);
  const statusConfig = (statusKey && STATUS_CONFIG[statusKey]) || (result ? DEFAULT_STATUS : null);

  const allMatches = result?.matches ?? [];
  const registeredMatches = allMatches.filter(
    (match) => match.source === "REGISTERED"
  );
  const applicationMatches = allMatches.filter(
    (match) => match.source === "PENDING_APPLICATION"
  );
  const signals = result?.signals ?? {};
  const overallScore = formatScore(result?.verification_score ?? result?.score);

  const hasFuzzy = signals?.fuzzy !== undefined || signals?.spelling !== undefined;
  const hasPhonetic = signals?.phonetic !== undefined;
  const hasSemantic = signals?.semantic !== undefined;
  const hasAnySignal = hasFuzzy || hasPhonetic || hasSemantic;

  return (
    <div className="min-h-screen w-full bg-white font-sans text-slate-900">
      {/* ------------------------------------------------------------------ */}
      {/* GOVERNMENT OF INDIA TOP STRIP                                      */}
      {/* ------------------------------------------------------------------ */}
      <div className="flex h-[3px] w-full">
        <div className="flex-1 bg-[#FF9933]" />
        <div className="flex-1 bg-white" />
        <div className="flex-1 bg-[#138808]" />
      </div>
      <div className="w-full bg-[#0B1E38] text-white">
        <div className="flex flex-wrap items-center justify-between gap-1 px-[4vw] py-1.5 text-[11.5px]">
          <span>Government of India&nbsp;&nbsp;|&nbsp;&nbsp;भारत सरकार</span>
          <span className="text-slate-300">
            Ministry of Information &amp; Broadcasting
          </span>
        </div>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* HEADER                                                             */}
      {/* ------------------------------------------------------------------ */}
      <header className="w-full border-b-[3px]" style={{ borderColor: PRGI_BLUE }}>
        <div className="flex items-center gap-4 px-[4vw] py-4">
          <div
            className="flex h-12 w-12 shrink-0 items-center justify-center border-2 font-serif text-[15px] font-bold"
            style={{ borderColor: PRGI_BLUE, color: PRGI_BLUE }}
          >
            प्र
          </div>
          <div>
            <h1
              className="font-serif text-[15.5px] font-semibold leading-tight sm:text-[17px]"
              style={{ color: PRGI_BLUE }}
            >
              भारत के प्रेस महापंजीयक
            </h1>
            <h1 className="font-serif text-[15.5px] font-semibold leading-tight text-slate-900 sm:text-[17px]">
              Press Registrar General of India
            </h1>
            <p className="mt-0.5 text-[12px] text-slate-500">
              Formerly Registrar of Newspapers for India (RNI) &middot; Title
              Verification System
            </p>
          </div>
        </div>
      </header>

      <main className="w-full px-[4vw] py-10">
        {/* ------------------------------------------------------------------ */}
        {/* FORM                                                               */}
        {/* ------------------------------------------------------------------ */}
        <section aria-labelledby="verify-heading">
          <SectionHeading
            title="Title Verification"
            description="Check a proposed publication title against registered publications and application history."
          />

          <div
            className="border-t-2 border-b border-slate-200"
            style={{ borderTopColor: PRGI_BLUE }}
          >
            <div className="grid divide-y divide-slate-200 sm:grid-cols-[minmax(0,1fr)_260px_220px] sm:divide-y-0 sm:divide-x">
              <div className="px-5 py-4">
                <FieldLabel htmlFor="title">Proposed publication title</FieldLabel>
                <input
                  id="title"
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Enter proposed publication title"
                  className="w-full border-0 border-b border-slate-300 bg-transparent px-0 py-2 text-[15px] text-slate-900 outline-none transition focus:border-b-2 focus:border-[#0B3B70] placeholder:text-slate-400"
                />
              </div>

              <div className="px-5 py-4">
                <FieldLabel htmlFor="language">Language</FieldLabel>
                <select
                  id="language"
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-full border-0 border-b border-slate-300 bg-transparent px-0 py-2 text-[15px] text-slate-900 outline-none transition focus:border-b-2 focus:border-[#0B3B70]"
                >
                  {LANGUAGES.map((lang) => (
                    <option key={lang}>{lang}</option>
                  ))}
                </select>
              </div>

              <div className="px-5 py-4">
                <FieldLabel htmlFor="periodicity">Periodicity</FieldLabel>
                <select
                  id="periodicity"
                  value={periodicity}
                  onChange={(e) => setPeriodicity(e.target.value)}
                  className="w-full border-0 border-b border-slate-300 bg-transparent px-0 py-2 text-[15px] text-slate-900 outline-none transition focus:border-b-2 focus:border-[#0B3B70]"
                >
                  {PERIODICITIES.map((p) => (
                    <option key={p}>{p}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex items-center justify-between px-5 py-4">
              <p className="text-[12px] text-slate-500">
                Checked against the PRGI registered-publication database and
                application records.
              </p>
              <button
                onClick={handleVerify}
                disabled={!title.trim() || loading}
                className="px-6 py-2.5 text-[14px] font-medium text-white transition disabled:cursor-not-allowed disabled:bg-slate-300"
                style={{
                  backgroundColor: !title.trim() || loading ? undefined : PRGI_BLUE,
                }}
              >
                {loading ? "Checking…" : "Verify Title"}
              </button>
            </div>
          </div>
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* RESULT — presented as an official verification report              */}
        {/* ------------------------------------------------------------------ */}
        <section aria-labelledby="result-heading" className="mt-12">
          <SectionHeading title="Verification Result" />

          {error && (
            <div className="border border-red-300 bg-red-50 px-5 py-4 text-[14px] text-red-800">
              {error}
            </div>
          )}

          {!error && !result && !loading && (
            <div className="flex min-h-[200px] flex-col items-center justify-center border border-dashed border-slate-300 px-6 py-14 text-center">
              <p className="text-[15px] font-medium text-slate-700">
                No verification yet
              </p>
              <p className="mt-1.5 text-[13px] text-slate-500">
                Enter a proposed title and run the verification.
              </p>
            </div>
          )}

          {!error && loading && (
            <div className="flex min-h-[200px] flex-col items-center justify-center border border-slate-200 px-6 py-14 text-center">
              <div
                className="mb-3 h-5 w-5 animate-spin rounded-full border-2 border-slate-300"
                style={{ borderTopColor: PRGI_BLUE }}
              />
              <p className="text-[14px] text-slate-600">Checking submitted title…</p>
            </div>
          )}

          {!error && !loading && result && (
            <div className="border border-slate-300">
              {/* report letterhead row */}
              <div
                className="flex flex-wrap items-center justify-between gap-2 border-b-2 px-5 py-3"
                style={{ borderColor: PRGI_BLUE }}
              >
                <p
                  className="text-[12px] font-semibold uppercase tracking-[0.12em]"
                  style={{ color: PRGI_BLUE }}
                >
                  Verification Report
                </p>
                <p className="text-[11.5px] text-slate-400">
                  Generated {generatedAt}
                </p>
              </div>

              <div className="p-5 sm:p-6">
                <div className="grid gap-x-8 gap-y-4 sm:grid-cols-4">
                  <div className="sm:col-span-2">
                    <ReportField label="Submitted title" value={result.submitted_title} />
                  </div>
                  <ReportField label="Language" value={language} />
                  <ReportField label="Periodicity" value={periodicity} />
                </div>

                <div className="mt-5 grid gap-x-8 gap-y-4 border-t border-slate-200 pt-5 sm:grid-cols-4">
                  <div className="sm:col-span-2">
                    <p className="text-[11px] uppercase tracking-wide text-slate-400">
                      Status
                    </p>
                    <div
                      className={`mt-1 inline-block border px-2.5 py-1 text-[12.5px] font-semibold uppercase tracking-wide ${statusConfig.text} ${statusConfig.border}`}
                    >
                      {statusConfig.label}
                    </div>
                  </div>

                  {overallScore !== null && (
                    <ReportField
                      label="Verification / similarity score"
                      value={`${overallScore}%`}
                    />
                  )}

                  {typeof result.candidates_found === "number" && (
                    <ReportField
                      label="Registered titles checked"
                      value={result.candidates_found}
                    />
                  )}
                </div>

                {Array.isArray(result.violations) && result.violations.length > 0 && (
                  <div className="mt-5 border-t border-slate-200 pt-5">
                    <p className="text-[11px] uppercase tracking-wide text-slate-400">
                      Violations
                    </p>
                    <ul className="mt-2 space-y-2">
                      {result.violations.map((violation, i) => (
                        <li
                          key={i}
                          className="border border-red-200 bg-red-50 px-3 py-2.5"
                        >
                          <span className="text-[11px] font-semibold uppercase tracking-wide text-red-700">
                            {violation.type ?? "Violation"}
                          </span>
                          <p className="mt-0.5 text-[13.5px] leading-relaxed text-red-800">
                            {violation.message ?? "—"}
                          </p>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {result.explanation && (
                  <div className="mt-5 border-t border-slate-200 pt-5">
                    <p className="text-[11px] uppercase tracking-wide text-slate-400">
                      Explanation
                    </p>
                    <p className="mt-1.5 max-w-3xl text-[14px] leading-relaxed text-slate-700">
                      {result.explanation}
                    </p>
                  </div>
                )}

                {hasAnySignal && (
                  <div className="mt-5 border-t border-slate-200 pt-5">
                    <p className="mb-1 text-[11px] uppercase tracking-wide text-slate-400">
                      Similarity signals
                    </p>
                    <div className="grid divide-y divide-slate-100 sm:max-w-xl">
                      {hasFuzzy && (
                        <SimilarityBar
                          label="Spelling / fuzzy"
                          value={signals.fuzzy ?? signals.spelling}
                        />
                      )}
                      {hasPhonetic && (
                        <SimilarityBar label="Phonetic" value={signals.phonetic} />
                      )}
                      {hasSemantic && (
                        <SimilarityBar label="Semantic" value={signals.semantic} />
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* REGISTERED PUBLICATION MATCHES                                     */}
        {/* ------------------------------------------------------------------ */}
        {!error && result && (
          <section aria-labelledby="registered-heading" className="mt-12">
            <SectionHeading
              title="Registered Publication Matches"
              description="Similar titles found in the PRGI registered publication database. These represent the authoritative historical registry."
            />

            {registeredMatches.length === 0 ? (
              <EmptyRow>No significant registered-title matches found.</EmptyRow>
            ) : (
              <div className="overflow-x-auto border border-slate-200">
                <table className="w-full min-w-[640px] border-collapse text-left text-[13px]">
                  <thead>
                    <tr className="border-b border-slate-300 bg-slate-50 text-[11px] uppercase tracking-wide text-slate-500">
                      <th className="px-4 py-3 font-medium">Publication Title</th>
                      <th className="px-4 py-3 font-medium">Language</th>
                      <th className="px-4 py-3 font-medium">Periodicity</th>
                      <th className="px-4 py-3 font-medium">Match Type</th>
                      <th className="px-4 py-3 font-medium">Similarity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {registeredMatches.map((match, i) => {
                      const score = formatScore(match.score);
                      return (
                        <tr
                          key={i}
                          className="border-b border-slate-100 last:border-0"
                        >
                          <td className="px-4 py-3 font-medium text-slate-900">
                            {match.title ?? "—"}
                          </td>
                          <td className="px-4 py-3 text-slate-600">
                            {match.language ?? "—"}
                          </td>
                          <td className="px-4 py-3 text-slate-600">
                            {match.periodicity ?? "—"}
                          </td>
                          <td className="px-4 py-3 text-slate-600">
                            {formatMatchTypes(match.match_types)}
                          </td>
                          <td className="px-4 py-3 tabular-nums text-slate-600">
                            {score !== null ? `${score}%` : "—"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}

        {/* ------------------------------------------------------------------ */}
        {/* APPLICATION HISTORY / SIMILAR APPLICATIONS                        */}
        {/* ------------------------------------------------------------------ */}
        {!error && result && (
          <section aria-labelledby="applications-heading" className="mt-12">
            <SectionHeading
              title="Similar Applications"
              description="Titles from applications currently pending with PRGI that resemble the proposed title, shown for reference. A similar pending application is a reference point, not a rejection."
            />

            {applicationMatches.length === 0 ? (
              <EmptyRow>No similar applications found.</EmptyRow>
            ) : (
              <div className="overflow-x-auto border border-slate-200">
                <table className="w-full min-w-[640px] border-collapse text-left text-[13px]">
                  <thead>
                    <tr className="border-b border-slate-300 bg-slate-50 text-[11px] uppercase tracking-wide text-slate-500">
                      <th className="px-4 py-3 font-medium">Proposed Title</th>
                      <th className="px-4 py-3 font-medium">Language</th>
                      <th className="px-4 py-3 font-medium">Periodicity</th>
                      <th className="px-4 py-3 font-medium">Match Type</th>
                      <th className="px-4 py-3 font-medium">Similarity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {applicationMatches.map((match, i) => {
                      const score = formatScore(match.score);
                      return (
                        <tr
                          key={i}
                          className="border-b border-slate-100 last:border-0"
                        >
                          <td className="px-4 py-3 font-medium text-slate-900">
                            {match.title ?? "—"}
                          </td>
                          <td className="px-4 py-3 text-slate-600">
                            {match.language ?? "—"}
                          </td>
                          <td className="px-4 py-3 text-slate-600">
                            {match.periodicity ?? "—"}
                          </td>
                          <td className="px-4 py-3 text-slate-600">
                            {formatMatchTypes(match.match_types)}
                          </td>
                          <td className="px-4 py-3 tabular-nums text-slate-600">
                            {score !== null ? `${score}%` : "—"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}
      </main>

      <footer className="mt-16 w-full border-t border-slate-200">
        <div className="px-[4vw] py-6 text-[12px] text-slate-400">
          Content owned and managed by the Press Registrar General of India ·
          Ministry of Information &amp; Broadcasting · Government of India
        </div>
      </footer>
    </div>
  );
}

export default App;