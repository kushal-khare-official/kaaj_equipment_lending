import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom'
import { BorrowerPage } from './pages/Borrower'
import { ApplicationsPage } from './pages/Applications'
import { UnderwriterPage } from './pages/Underwriter'

function Shell({ children }: { children: React.ReactNode }) {
    const location = useLocation()
    const path = location.pathname
    const isUw = path.startsWith('/uw')
    const isAppList = path.startsWith('/applications')

    return (
        <div className="min-h-screen bg-slate-50 text-slate-900">
            <header className="border-b border-slate-200 bg-white">
                <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
                    <div className="text-lg font-semibold">Lender Matching Platform</div>
                    <div className="flex gap-2">
                        <Link
                            className={`rounded px-3 py-2 text-sm font-semibold ${!isUw && !isAppList ? 'bg-slate-900 text-white' : 'bg-white text-slate-700 border border-slate-200'
                                }`}
                            to="/apply"
                        >
                            Borrower
                        </Link>
                        <Link
                            className={`rounded px-3 py-2 text-sm font-semibold ${isUw && !isAppList ? 'bg-slate-900 text-white' : 'bg-white text-slate-700 border border-slate-200'
                                }`}
                            to="/uw"
                        >
                            Underwriter
                        </Link>
                        <Link
                            className={`rounded px-3 py-2 text-sm font-semibold ${isAppList ? 'bg-slate-900 text-white' : 'bg-white text-slate-700 border border-slate-200'
                                }`}
                            to="/applications"
                        >
                            Applications
                        </Link>
                    </div>
                </div>
            </header>
            <main className="mx-auto max-w-5xl px-6 py-10 space-y-6">{children}</main>
        </div>
    )
}

export function AppRouter() {
    return (
        <BrowserRouter>
            <Shell>
                <Routes>
                    <Route path="/apply" element={<BorrowerPage />} />
                    <Route path="/applications" element={<ApplicationsPage />} />
                    <Route path="/uw" element={<UnderwriterPage />} />
                    <Route path="*" element={<Navigate to="/apply" replace />} />
                </Routes>
            </Shell>
        </BrowserRouter>
    )
}

