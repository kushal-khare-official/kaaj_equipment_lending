import { useEffect, useState } from 'react'
import { listApplications, requestDoc, rerunMatch } from '../api'

type ApplicationRow = { id: string; status: string; merchant_email?: string; created_at?: string }

export function ApplicationsPage() {
    const [applications, setApplications] = useState<ApplicationRow[]>([])
    const [selectedAppId, setSelectedAppId] = useState<string | null>(null)
    const [appFilter, setAppFilter] = useState<string>('All')
    const [appSearch, setAppSearch] = useState<string>('')
    const [error, setError] = useState<string | null>(null)

    const load = () => {
        listApplications().then(setApplications).catch((e) => setError(e.message))
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
                ? (a.merchant_email || a.id).toLowerCase().includes(appSearch.toLowerCase())
                : true
        )

    return (
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
                <div className="text-2xl font-semibold text-slate-900">Loan applications</div>
                <button className="text-xs rounded bg-slate-900 text-white px-3 py-2" onClick={load}>
                    Refresh
                </button>
            </div>
            {error && <div className="text-sm text-red-600 mb-2">{error}</div>}
            <div className="flex flex-wrap items-center gap-2 mb-4">
                {['All', 'Granted', 'Rejected', 'New', 'Submitted'].map((f) => (
                    <button
                        key={f}
                        className={`rounded border px-3 py-1 text-xs font-semibold ${appFilter === f ? 'border-slate-900 text-slate-900 bg-slate-100' : 'border-slate-200 text-slate-600'
                            }`}
                        onClick={() => setAppFilter(f)}
                    >
                        {f}
                    </button>
                ))}
                <input
                    className="ml-auto w-48 rounded border border-slate-200 px-3 py-1 text-sm"
                    placeholder="Search"
                    value={appSearch}
                    onChange={(e) => setAppSearch(e.target.value)}
                />
            </div>
            <div className="overflow-x-auto">
                <table className="min-w-full text-sm text-slate-800">
                    <thead className="text-xs uppercase text-slate-500">
                        <tr className="border-b border-slate-200">
                            <th className="px-3 py-2 text-left">Company name</th>
                            <th className="px-3 py-2 text-left">Applied on</th>
                            <th className="px-3 py-2 text-left">Category</th>
                            <th className="px-3 py-2 text-left">Amount</th>
                            <th className="px-3 py-2 text-left">Criteria met</th>
                            <th className="px-3 py-2 text-left">Status</th>
                            <th className="px-3 py-2 text-left"></th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredApplications.length === 0 ? (
                            <tr>
                                <td className="px-3 py-4 text-slate-500" colSpan={7}>
                                    No applications
                                </td>
                            </tr>
                        ) : (
                            filteredApplications.map((a) => (
                                <tr
                                    key={a.id}
                                    className={`border-b border-slate-100 ${selectedAppId === a.id ? 'bg-slate-50' : ''}`}
                                >
                                    <td className="px-3 py-3 font-semibold">{a.merchant_email || a.id}</td>
                                    <td className="px-3 py-3 text-slate-600">
                                        {a.created_at ? new Date(a.created_at).toLocaleDateString() : '—'}
                                    </td>
                                    <td className="px-3 py-3 text-slate-700">Equipment financing</td>
                                    <td className="px-3 py-3 text-slate-900">$—</td>
                                    <td className="px-3 py-3 text-slate-600">—</td>
                                    <td className="px-3 py-3">
                                        <span
                                            className={`rounded-full px-2 py-1 text-xs font-semibold ${(a.status || '').toLowerCase() === 'approved'
                                                ? 'bg-emerald-100 text-emerald-700'
                                                : (a.status || '').toLowerCase() === 'declined'
                                                    ? 'bg-rose-100 text-rose-700'
                                                    : 'bg-slate-100 text-slate-700'
                                                }`}
                                        >
                                            {a.status || '—'}
                                        </span>
                                    </td>
                                    <td className="px-3 py-3 space-x-2 text-xs">
                                        <button
                                            className="rounded bg-slate-100 px-2 py-1"
                                            onClick={() => setSelectedAppId(a.id)}
                                        >
                                            Select
                                        </button>
                                        <button
                                            className="rounded bg-blue-600 text-white px-2 py-1"
                                            onClick={() => rerunMatch(a.id).catch((e) => setError(e.message))}
                                        >
                                            Rerun
                                        </button>
                                        <button
                                            className="rounded bg-amber-600 text-white px-2 py-1"
                                            onClick={() => requestDoc(a.id, 'bank_statements').catch((e) => setError(e.message))}
                                        >
                                            Req docs
                                        </button>
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

