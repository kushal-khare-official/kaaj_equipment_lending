import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'

export function LoginPage() {
    const navigate = useNavigate()
    const location = useLocation()
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    // Get the redirect path from location state, default to /uw
    const from = (location.state as any)?.from?.pathname || '/applications'

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError('')
        setLoading(true)

        // Simulate API call delay
        await new Promise(resolve => setTimeout(resolve, 500))

        // Mock authentication - accept any username/password
        // In production, this would validate against a real auth service
        if (username && password) {
            // Store mock auth token
            localStorage.setItem('auth_token', 'mock_token_' + username)
            localStorage.setItem('auth_user', username)

            // Redirect to the page they tried to visit or default location
            navigate(from, { replace: true })
        } else {
            setError('Please enter both username and password')
        }

        setLoading(false)
    }

    return (
        <div className="min-h-screen bg-slate-50 flex items-center justify-center px-6 py-12">
            <div className="w-full max-w-md">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-slate-900">Lender Matching Platform</h1>
                    <p className="mt-2 text-sm text-slate-600">Sign in to access the underwriter portal</p>
                </div>

                <div className="rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
                    <h2 className="text-xl font-semibold text-slate-900 mb-6">Sign In</h2>

                    {error && (
                        <div className="mb-4 rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">
                                Username
                            </label>
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                                placeholder="Enter any username"
                                autoFocus
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">
                                Password
                            </label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                                placeholder="Enter any password"
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full rounded-md bg-slate-900 px-6 py-2.5 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-50"
                        >
                            {loading ? 'Signing in...' : 'Sign In'}
                        </button>
                    </form>

                    <div className="mt-6 rounded-md bg-slate-50 p-4">
                        <p className="text-xs text-slate-600 mb-2">
                            <strong>Demo Mode:</strong> This is a mocked login for demonstration purposes.
                        </p>
                        <p className="text-xs text-slate-500">
                            Enter any username and password to access the protected pages. No actual authentication is performed.
                        </p>
                    </div>
                </div>

                <div className="mt-6 text-center">
                    <button
                        onClick={() => navigate('/')}
                        className="text-sm text-slate-600 hover:text-slate-900"
                    >
                        ← Back to home
                    </button>
                </div>
            </div>
        </div>
    )
}

