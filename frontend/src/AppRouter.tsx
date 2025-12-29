import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom'
import { BorrowerPage } from './pages/Borrower'
import { IntakeFormPage } from './pages/IntakeForm'
import { ApplicationsPage } from './pages/Applications'
import { ApplicationDetailPage } from './pages/ApplicationDetail'
import { UnderwriterPage } from './pages/Underwriter'
import { LoginPage } from './pages/Login'
import { ProtectedRoute, useAuth } from './components/ProtectedRoute'

function Shell({ children }: { children: React.ReactNode }) {
    const location = useLocation()
    const path = location.pathname
    const isUw = path.startsWith('/uw')
    const isAppList = path.startsWith('/applications')
    const isLogin = path === '/login'
    const { isAuthenticated, username, logout } = useAuth()

    // Don't show shell on login page
    if (isLogin) {
        return <>{children}</>
    }

    return (
        <div className="min-h-screen bg-slate-50 text-slate-900">
            <header className="border-b border-slate-200 bg-white">
                <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
                    <div className="text-lg font-semibold">Lender Matching Platform</div>
                    <div className="flex items-center gap-2">
                        {!isAuthenticated && (
                            <Link
                                className={`rounded px-3 py-2 text-sm font-semibold ${isAppList ? 'bg-slate-900 text-white' : 'bg-white text-slate-700 border border-slate-200'}`}
                                to="/login">
                                Login
                            </Link>
                        )}
                        {isAuthenticated && (
                            <>
                                <Link
                                    className={`rounded px-3 py-2 text-sm font-semibold ${isAppList ? 'bg-slate-900 text-white' : 'bg-white text-slate-700 border border-slate-200'}`}
                                    to="/applications">
                                    Applications
                                </Link>
                                <Link
                                    className={`rounded px-3 py-2 text-sm font-semibold ${isUw && !isAppList ? 'bg-slate-900 text-white' : 'bg-white text-slate-700 border border-slate-200'}`}
                                    to="/uw">
                                    Lender Config
                                </Link>
                                <div className="ml-2 flex items-center gap-2 border-l border-slate-200 pl-2">
                                    <span className="text-xs text-slate-600">
                                        {username}
                                    </span>
                                    <button
                                        onClick={logout}
                                        className="rounded px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100"
                                    >
                                        Logout
                                    </button>
                                </div>
                            </>
                        )}
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
                    <Route path="/login" element={<LoginPage />} />
                    <Route path="/apply" element={<IntakeFormPage />} />
                    <Route path="/apply/:applicationId" element={<BorrowerPage />} />
                    <Route
                        path="/applications"
                        element={
                            <ProtectedRoute>
                                <ApplicationsPage />
                            </ProtectedRoute>
                        }
                    />
                    <Route
                        path="/applications/:applicationId"
                        element={
                            <ProtectedRoute>
                                <ApplicationDetailPage />
                            </ProtectedRoute>
                        }
                    />
                    <Route
                        path="/uw"
                        element={
                            <ProtectedRoute>
                                <UnderwriterPage />
                            </ProtectedRoute>
                        }
                    />
                    <Route path="*" element={<Navigate to="/apply" replace />} />
                </Routes>
            </Shell>
        </BrowserRouter>
    )
}

