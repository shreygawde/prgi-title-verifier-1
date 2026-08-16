import { useState } from "react";

function App() {
  const [title, setTitle] = useState("");
  const [language, setLanguage] = useState("English");
  const [periodicity, setPeriodicity] = useState("Daily");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleVerify = async () => {
    if (!title.trim()) return;

    setLoading(true);

    try {
      const response = await fetch("http://localhost:5000/api/verify", {
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
    } catch (error) {
      console.error(error);
      alert("Unable to connect to the verification server.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <header className="border-b border-slate-800">
        <div className="mx-auto max-w-6xl px-6 py-5">
          <h1 className="text-2xl font-bold">PRGI Title Verifier</h1>
          <p className="mt-1 text-sm text-slate-400">
            Publication title verification and similarity analysis
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-10">
        <section className="grid gap-8 lg:grid-cols-2">
          {/* INPUT */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
            <h2 className="text-xl font-semibold">Verify a title</h2>

            <p className="mt-2 text-sm text-slate-400">
              Enter the proposed publication details below.
            </p>

            <div className="mt-6 space-y-5">
              <div>
                <label className="mb-2 block text-sm font-medium">
                  Proposed title
                </label>

                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Indian Express"
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none transition focus:border-blue-500"
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium">
                  Language
                </label>

                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none"
                >
                  <option>English</option>
                  <option>Hindi</option>
                  <option>Marathi</option>
                  <option>Gujarati</option>
                  <option>Bengali</option>
                  <option>Tamil</option>
                  <option>Telugu</option>
                  <option>Kannada</option>
                  <option>Malayalam</option>
                  <option>Punjabi</option>
                  <option>Urdu</option>
                </select>
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium">
                  Periodicity
                </label>

                <select
                  value={periodicity}
                  onChange={(e) => setPeriodicity(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none"
                >
                  <option>Daily</option>
                  <option>Weekly</option>
                  <option>Fortnightly</option>
                  <option>Monthly</option>
                  <option>Quarterly</option>
                </select>
              </div>

              <button
                onClick={handleVerify}
                disabled={!title.trim() || loading}
                className="w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {loading ? "Checking..." : "Verify Title"}
              </button>
            </div>
          </div>

          {/* RESULTS */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
            {!result ? (
              <div className="flex h-full min-h-80 items-center justify-center text-center">
                <div>
                  <div className="text-4xl">🔍</div>

                  <p className="mt-4 font-medium">
                    No verification yet
                  </p>

                  <p className="mt-2 text-sm text-slate-400">
                    Enter a title and run the verification.
                  </p>
                </div>
              </div>
            ) : (
              <div>
                {/* Submitted title */}
                <div>
                  <p className="text-sm text-slate-400">
                    Submitted title
                  </p>

                  <h2 className="mt-1 text-2xl font-bold">
                    {result.submitted_title}
                  </h2>
                </div>

                {/* Database status */}
                <div className="mt-6 rounded-xl border border-blue-900/50 bg-blue-950/30 p-5">
                  <p className="text-sm text-slate-400">
                    Database status
                  </p>

                  <p className="mt-1 text-3xl font-bold">
                    {result.status?.replaceAll("_", " ")}
                  </p>

                  <p className="mt-2 text-sm text-slate-400">
                    Found {result.candidates_found} registered titles
                    matching the selected language.
                  </p>
                </div>

                {/* Closest registered titles */}
                <div className="mt-6">
                  <h3 className="font-semibold">
                    Registered titles from PRGI database
                  </h3>

                  <div className="mt-3 space-y-3">
                    {result.matches?.map((match) => (
                      <div
                        key={match.id}
                        className="rounded-lg border border-slate-800 bg-slate-950 p-4"
                      >
                        <p className="font-medium">
                          {match.title}
                        </p>

                        <p className="mt-1 text-xs text-slate-500">
                          {match.language} · {match.periodicity}
                        </p>

                        <p className="mt-1 text-xs text-slate-600">
                          Registration: {match.registration_number}
                        </p>

                        {match.publisher && (
                          <p className="mt-1 text-xs text-slate-600">
                            Publisher: {match.publisher}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;