import './App.css'

function App() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div className="text-lg font-semibold">Lender Matching Platform</div>
          <div className="text-sm text-slate-500">Phase 1 scaffold</div>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-6 py-10">
        <div className="rounded-lg border border-dashed border-slate-300 bg-white p-6">
          <h1 className="text-xl font-semibold text-slate-900">Frontend scaffold ready</h1>
          <p className="mt-2 text-sm text-slate-600">
            React + TypeScript + Vite + Tailwind are configured. Replace this placeholder with the
            merchant and underwriter flows in later phases.
          </p>
        </div>
      </main>
    </div>
  )
}

export default App
