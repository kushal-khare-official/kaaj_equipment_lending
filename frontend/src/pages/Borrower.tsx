// Borrower page moved to dedicated route in AppRouter
import { useEffect, useState } from 'react'
import {
    createApplication,
    health,
    latestMatch,
    listDocuments,
    listLenders,
    listMatchRuns,
} from '../api'

type Lender = { id: string; name: string }

export function BorrowerPage() {
    const [apiStatus, setApiStatus] = useState<string>('Checking API...')
    const [lenders, setLenders] = useState<Lender[]>([])
    const [error, setError] = useState<string | null>(null)
    const [submitMsg, setSubmitMsg] = useState<string | null>(null)
    const [loading, setLoading] = useState(false)
    const [applicationId, setApplicationId] = useState<string | null>(null)
    const [documents, setDocuments] = useState<any[]>([])
    const [matchStatus, setMatchStatus] = useState<any | null>(null)
    const [matchHistory, setMatchHistory] = useState<any[]>([])

    const [loanType, setLoanType] = useState('Equipment Finance')
    const [equipmentMake, setEquipmentMake] = useState('Freightliner')
    const [equipmentModel, setEquipmentModel] = useState('Cascadia 2018')
    const [amount, setAmount] = useState('75000')
    const [businessName, setBusinessName] = useState('KAAJ TECHNOLOGIES INC.')
    const [merchantEmail, setMerchantEmail] = useState('ops@kaajtech.com')
    const [fico, setFico] = useState('700')

    useEffect(() => {
        health()
            .then(() => setApiStatus('API reachable'))
            .catch(() => setApiStatus('API not reachable'))
        listLenders()
            .then(setLenders)
            .catch((e) => setError(e.message))
    }, [])

    const submitApplication = async () => {
        setSubmitMsg(null)
        setError(null)
        setLoading(true)
        try {
            const body = {
                merchant_email: merchantEmail,
                guarantors: [{ is_primary: true, fico: fico ? Number(fico) : undefined }],
                equipment: [
                    {
                        type: loanType,
                        year: equipmentModel.match(/\d{4}/)?.[0] ? Number(equipmentModel.match(/\d{4}/)![0]) : undefined,
                        mileage: undefined,
                        titled: true,
                        private_party: false,
                    },
                ],
                loan_request: { amount: amount ? Number(amount.replace(/[^0-9.]/g, '')) : undefined },
            }
            const res = await createApplication(body)
            setApplicationId(res.id)
            setSubmitMsg(`Application created: ${res.id}`)
        } catch (e: any) {
            setError(e.message)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        if (!applicationId) return

        // Fetch data immediately when applicationId is set
        const fetchData = () => {
            listDocuments(applicationId).then(setDocuments).catch(() => { })
            latestMatch(applicationId).then(setMatchStatus).catch(() => { })
            listMatchRuns(applicationId).then(setMatchHistory).catch(() => { })
        }

        fetchData()

        // Only poll if match status is not yet complete (status is 'running' or null)
        // Poll less frequently (10 seconds) to reduce server load
        const interval = setInterval(() => {
            // Only continue polling if we don't have a completed match yet
            if (!matchStatus || matchStatus.status === 'running') {
                fetchData()
            }
        }, 10000)

        return () => clearInterval(interval)
    }, [applicationId, matchStatus?.status])

    return (
        <div className="space-y-6">
            <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex items-center justify-between">
                    <h1 className="text-2xl font-semibold text-slate-900">Tell us about your equipment finance need</h1>
                    <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                        {apiStatus}
                    </span>
                </div>
                {error && <div className="mt-3 text-sm text-red-600">{error}</div>}
                <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div>
                        <label className="text-sm font-semibold text-slate-800">What type of loan are you looking for?</label>
                        <select
                            className="mt-2 w-full rounded border border-slate-300 px-3 py-2 text-base"
                            value={loanType}
                            onChange={(e) => setLoanType(e.target.value)}
                        >
                            <option>Equipment Finance</option>
                            <option>Working Capital</option>
                            <option>Refinance</option>
                        </select>
                    </div>
                    <div />
                    <div>
                        <label className="text-base font-semibold text-slate-900">Make of the equipment</label>
                        <input
                            className="mt-2 w-full rounded border border-slate-300 px-3 py-2 text-base"
                            value={equipmentMake}
                            onChange={(e) => setEquipmentMake(e.target.value)}
                        />
                    </div>
                    <div>
                        <label className="text-base font-semibold text-slate-900">Model of the equipment</label>
                        <input
                            className="mt-2 w-full rounded border border-slate-300 px-3 py-2 text-base"
                            value={equipmentModel}
                            onChange={(e) => setEquipmentModel(e.target.value)}
                        />
                    </div>
                    <div>
                        <label className="text-base font-semibold text-slate-900">Amount of loan needed</label>
                        <input
                            className="mt-2 w-full rounded border border-slate-300 px-3 py-2 text-base"
                            value={amount}
                            onChange={(e) => setAmount(e.target.value)}
                        />
                    </div>
                    <div>
                        <label className="text-base font-semibold text-slate-900">Your legal business name</label>
                        <input
                            className="mt-2 w-full rounded border border-slate-300 px-3 py-2 text-base uppercase"
                            value={businessName}
                            onChange={(e) => setBusinessName(e.target.value)}
                        />
                    </div>
                    <div>
                        <label className="text-base font-semibold text-slate-900">Merchant email</label>
                        <input
                            className="mt-2 w-full rounded border border-slate-300 px-3 py-2 text-base"
                            value={merchantEmail}
                            onChange={(e) => setMerchantEmail(e.target.value)}
                        />
                    </div>
                    <div>
                        <label className="text-base font-semibold text-slate-900">Primary guarantor FICO</label>
                        <input
                            className="mt-2 w-full rounded border border-slate-300 px-3 py-2 text-base"
                            value={fico}
                            onChange={(e) => setFico(e.target.value)}
                        />
                    </div>
                </div>
                <div className="mt-6 flex items-center gap-3">
                    <button
                        className="inline-flex items-center justify-center rounded bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
                        onClick={submitApplication}
                        disabled={loading}
                    >
                        {loading ? 'Submitting...' : 'Submit application'}
                    </button>
                    {submitMsg && <span className="text-sm text-emerald-700">{submitMsg}</span>}
                </div>
            </div>

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
                    <div className="text-sm font-semibold text-slate-800 mb-2">Match status</div>
                    {applicationId ? (
                        matchStatus ? (
                            <div className="text-sm text-slate-700">
                                Latest fit score: {matchStatus.fit_score ?? 'N/A'}
                                <div className="mt-2">
                                    {matchStatus.results?.map((r: any) => (
                                        <div key={r.lender_program_id} className="mb-2 border-b border-slate-100 pb-2">
                                            <div className="font-semibold">{r.lender_program_id}</div>
                                            <div className="text-xs text-slate-600">Eligible: {String(r.eligible)}</div>
                                            <div className="text-xs text-slate-600">Reasons: {r.reasons}</div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ) : (
                            <div className="text-sm text-slate-500">Waiting for match run...</div>
                        )
                    ) : (
                        <div className="text-sm text-slate-500">Submit an application to see status.</div>
                    )}
                </div>
                <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
                    <div className="text-sm font-semibold text-slate-800 mb-2">Documents</div>
                    {applicationId ? (
                        documents.length === 0 ? (
                            <div className="text-sm text-slate-500">No documents requested.</div>
                        ) : (
                            <ul className="text-sm text-slate-700 space-y-1">
                                {documents.map((d: any) => (
                                    <li key={d.id} className="flex justify-between">
                                        <span>{d.type}</span>
                                        <span className="text-xs text-slate-500">{d.status}</span>
                                    </li>
                                ))}
                            </ul>
                        )
                    ) : (
                        <div className="text-sm text-slate-500">Submit an application to view docs.</div>
                    )}
                </div>
                <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm lg:col-span-2">
                    <div className="text-sm font-semibold text-slate-800 mb-2">Match history</div>
                    {applicationId && matchHistory.length > 0 ? (
                        <ul className="text-sm text-slate-700 space-y-1">
                            {matchHistory.map((r: any) => (
                                <li key={r.id} className="flex items-center gap-2">
                                    <span className="text-xs text-slate-500">{r.id}</span>
                                    <span className="text-xs text-slate-500">status: {r.status}</span>
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <div className="text-sm text-slate-500">No runs yet.</div>
                    )}
                </div>
            </div>
        </div>
    )
}

