import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listApplications } from '../api'

type ApplicationRow = {
    id: string
    status: string
    merchant_email?: string
    business_name?: string
    loan_type?: string
    loan_amount?: number
    created_at?: string
    criteria_met?: string
    fit_score?: number
}

export function ApplicationsPage() {
    const navigate = useNavigate()
    const [applications, setApplications] = useState<ApplicationRow[]>([])
    const [appFilter, setAppFilter] = useState<string>('All')
    const [appSearch, setAppSearch] = useState<string>('')
    const [error, setError] = useState<string | null>(null)
    const [loading, setLoading] = useState(true)

    const load = () => {
        setLoading(true)
        listApplications()
            .then(setApplications)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false))
    }

    useEffect(() => {
        load()
    }, [])

    const filteredApplications = applications
        .filter((a) => {
            if (appFilter === 'All') return true
            if (appFilter === 'Granted') return a.status?.toLowerCase() === 'approved' || a.status?.toLowerCase() === 'granted'
            if (appFilter === 'Rejected') return a.status?.toLowerCase() === 'declined'
            if (appFilter === 'New') return a.status?.toLowerCase() === 'processing'
            if (appFilter === 'Submitted') return a.status?.toLowerCase() === 'submitted'
            return true
        })
        .filter((a) =>
            appSearch
                ? (a.business_name || a.merchant_email || a.id).toLowerCase().includes(appSearch.toLowerCase())
                : true
        )

    const formatDate = (dateStr?: string) => {
        if (!dateStr) return '—'
        const date = new Date(dateStr)
        return date.toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' })
    }

    const formatAmount = (amount?: number) => {
        if (!amount) return '—'
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(amount)
    }

    const formatLoanType = (type?: string) => {
        if (!type) return '—'
        return type.replace(/_/g, ' ')
    }

    const getStatusBadge = (status: string) => {
        const s = (status || '').toLowerCase()
        if (s === 'approved' || s === 'granted') {
            return <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-medium text-emerald-700">Granted</span>
        }
        if (s === 'declined' || s === 'rejected') {
            return <span className="rounded-full bg-rose-100 px-2.5 py-1 text-xs font-medium text-rose-700">Rejected</span>
        }
        if (s === 'submitted') {
            return <span className="rounded-full bg-blue-100 px-2.5 py-1 text-xs font-medium text-blue-700">Submitted</span>
        }
        if (s === 'processing') {
            return <span className="rounded-full bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-700">New</span>
        }
        return <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">{status || '—'}</span>
    }

    const handleRowClick = (id: string) => {
        navigate(`/applications/${id}`)
    }

    return (
        <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
            {/* Header */}
            <div className="border-b border-slate-200 px-6 py-5">
                <div className="flex items-center justify-between">
                    <h1 className="text-2xl font-semibold text-slate-900">Loan applications</h1>
                </div>

                {/* Filters */}
                <div className="mt-4 flex flex-wrap items-center gap-3">
                    <span className="text-sm text-slate-500">Show</span>
                    {['All', 'Granted', 'Rejected', 'New', 'Submitted'].map((f) => (
                        <button
                            key={f}
                            className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${appFilter === f
                                ? 'border-slate-900 bg-slate-900 text-white'
                                : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300'
                                }`}
                            onClick={() => setAppFilter(f)}
                        >
                            {f}
                        </button>
                    ))}
                    <div className="ml-auto flex items-center gap-3">
                        <div className="relative">
                            <svg className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                            <input
                                className="w-56 rounded-lg border border-slate-200 bg-white py-1.5 pl-9 pr-3 text-sm placeholder-slate-400 focus:border-slate-400 focus:outline-none"
                                placeholder="Filter"
                                value={appSearch}
                                onChange={(e) => setAppSearch(e.target.value)}
                            />
                        </div>
                    </div>
                </div>
            </div>

            {/* Error Message */}
            {error && (
                <div className="mx-6 mt-4 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div>
            )}

            {/* Table */}
            <div className="overflow-x-auto">
                <table className="min-w-full">
                    <thead>
                        <tr className="border-b border-slate-200 bg-slate-50">
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                                Company name
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                                Applied on
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                                Category
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                                Amount
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                                Criteria met
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                                Status
                            </th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                        {loading ? (
                            <tr>
                                <td className="px-6 py-8 text-center text-slate-500" colSpan={6}>
                                    <div className="flex items-center justify-center">
                                        <svg className="h-5 w-5 animate-spin text-slate-400" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                        </svg>
                                        <span className="ml-2">Loading applications...</span>
                                    </div>
                                </td>
                            </tr>
                        ) : filteredApplications.length === 0 ? (
                            <tr>
                                <td className="px-6 py-8 text-center text-slate-500" colSpan={6}>
                                    No applications found
                                </td>
                            </tr>
                        ) : (
                            filteredApplications.map((a) => (
                                <tr
                                    key={a.id}
                                    className="cursor-pointer transition-colors hover:bg-slate-50"
                                    onClick={() => handleRowClick(a.id)}
                                >
                                    <td className="px-6 py-4">
                                        <span className="font-medium text-slate-900">
                                            {a.business_name || a.merchant_email || a.id.slice(0, 8)}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-slate-600">
                                        {formatDate(a.created_at)}
                                    </td>
                                    <td className="px-6 py-4 text-sm text-slate-700">
                                        {formatLoanType(a.loan_type)}
                                    </td>
                                    <td className="px-6 py-4 text-sm font-medium text-slate-900">
                                        {formatAmount(a.loan_amount)}
                                    </td>
                                    <td className="px-6 py-4 text-sm text-slate-600">
                                        {a.criteria_met ? (
                                            <span className={a.criteria_met.startsWith('0') ? 'text-rose-600' : 'text-emerald-600'}>
                                                {a.criteria_met}
                                            </span>
                                        ) : '—'}
                                        {a.fit_score !== undefined && a.fit_score !== null && (
                                            <span className="ml-1 text-slate-400">avg</span>
                                        )}
                                    </td>
                                    <td className="px-6 py-4">
                                        {getStatusBadge(a.status)}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
