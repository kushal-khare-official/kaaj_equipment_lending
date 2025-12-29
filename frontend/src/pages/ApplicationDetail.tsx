import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getApplication, latestMatch } from '../api'

type TabId = 'overview' | 'application' | 'kyb' | 'fraud' | 'bank' | 'financial' | 'tax' | 'credit' | 'workflow'

const TABS: { id: TabId; label: string }[] = [
    { id: 'application', label: 'Application Form' },
    { id: 'kyb', label: 'KYB Report' },
    { id: 'fraud', label: 'Fraud Detection' },
    { id: 'bank', label: 'Bank Statement' },
    { id: 'financial', label: 'Financial Statement' },
    { id: 'tax', label: 'Tax Forms' },
    { id: 'credit', label: 'Credit Report' },
    { id: 'workflow', label: 'Workflow' },
]

type Application = {
    id: string
    status: string
    merchant_email: string
    business_name?: string
    loan_type?: string
    guarantors?: Array<{
        id: string
        is_primary: boolean
        first_name?: string
        last_name?: string
        fico?: number
    }>
    business_credit?: {
        paynet_score?: number
        revolving_utilization?: number
    }
    equipment?: Array<{
        id: string
        type?: string
        year?: number
        mileage?: number
        titled?: boolean
        private_party?: boolean
    }>
    loan_request?: {
        amount?: number
        term_months?: number
        down_payment?: number
    }
}

type MatchResult = {
    lender_program_id: string
    lender_name?: string
    program_name?: string
    eligible: boolean
    fit_score?: number
    reasons?: string
    assigned_term_months?: number
    assigned_interest_rate?: number
}

export function ApplicationDetailPage() {
    const { applicationId } = useParams<{ applicationId: string }>()
    const navigate = useNavigate()
    const [activeTab, setActiveTab] = useState<TabId>('application')
    const [application, setApplication] = useState<Application | null>(null)
    const [matchResults, setMatchResults] = useState<MatchResult[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        if (!applicationId) return

        const loadData = async () => {
            setLoading(true)
            try {
                const [appData, matchData] = await Promise.all([
                    getApplication(applicationId),
                    latestMatch(applicationId).catch(() => null),
                ])
                setApplication(appData)
                if (matchData?.results) {
                    setMatchResults(matchData.results)
                }
            } catch (e: any) {
                setError(e.message || 'Failed to load application')
            } finally {
                setLoading(false)
            }
        }

        loadData()
    }, [applicationId])

    const formatDate = (dateStr?: string) => {
        if (!dateStr) return '—'
        return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    }

    const formatCurrency = (amount?: number) => {
        if (!amount) return '—'
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0 }).format(amount)
    }

    const eligibleMatches = matchResults.filter(r => r.eligible)
    const criteriaCount = matchResults.length > 0 ? `${eligibleMatches.length}/${matchResults.length}` : '—'

    if (loading) {
        return (
            <div className="flex items-center justify-center py-20">
                <svg className="h-8 w-8 animate-spin text-slate-400" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                <span className="ml-3 text-slate-600">Loading application...</span>
            </div>
        )
    }

    if (error || !application) {
        return (
            <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
                <p className="text-red-700">{error || 'Application not found'}</p>
                <button
                    className="mt-4 rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
                    onClick={() => navigate('/applications')}
                >
                    Back to Applications
                </button>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Header with banner */}
            <div className="relative overflow-hidden rounded-lg bg-gradient-to-r from-violet-600 to-indigo-600 text-white">
                <div className="absolute right-4 top-4">
                    <span className="rounded bg-white/20 px-2 py-1 text-xs font-medium">
                        All data in this demo is sample data
                    </span>
                </div>
                <div className="px-6 py-8">
                    <div className="flex items-center gap-2 text-sm text-violet-200">
                        <span>{formatDate(new Date().toISOString())}</span>
                    </div>
                    <h1 className="mt-2 text-2xl font-bold">{application.business_name || 'Application'}</h1>
                    <div className="mt-4 flex items-center gap-4">
                        <span className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-medium ${
                            eligibleMatches.length > 0
                                ? 'bg-emerald-500/20 text-emerald-100'
                                : 'bg-amber-500/20 text-amber-100'
                        }`}>
                            {criteriaCount} Criteria met
                        </span>
                        <div className="flex gap-2">
                            <button className="rounded-md bg-emerald-500 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-600">
                                Approve
                            </button>
                            <button className="rounded-md bg-white/10 px-4 py-2 text-sm font-medium text-white hover:bg-white/20">
                                Reject
                            </button>
                        </div>
                    </div>
                </div>

                {/* AI Analysis Summary */}
                {eligibleMatches.length > 0 && (
                    <div className="border-t border-white/10 bg-white/5 px-6 py-4">
                        <p className="text-sm text-violet-100">
                            Given the company's strong financial performance, active status, and the purpose of the loan,{' '}
                            {application.business_name || 'this business'} presents a favorable case for the requested{' '}
                            {application.loan_type || 'financing'}.
                        </p>
                        <button className="mt-2 text-sm font-medium text-violet-200 hover:text-white">
                            Read full AI Analysis
                        </button>
                    </div>
                )}

                {/* Loan Summary Stats */}
                <div className="border-t border-white/10 bg-white/5 px-6 py-4">
                    <div className="grid grid-cols-6 gap-6 text-center">
                        <div>
                            <div className="text-xs text-violet-200">Amount</div>
                            <div className="mt-1 text-lg font-semibold">{formatCurrency(application.loan_request?.amount)}</div>
                        </div>
                        <div>
                            <div className="text-xs text-violet-200">Category</div>
                            <div className="mt-1 text-lg font-semibold">{application.loan_type || '—'}</div>
                        </div>
                        {eligibleMatches[0]?.assigned_term_months && (
                            <div>
                                <div className="text-xs text-violet-200">Term</div>
                                <div className="mt-1 text-lg font-semibold">{eligibleMatches[0].assigned_term_months} mo</div>
                            </div>
                        )}
                        {eligibleMatches[0]?.assigned_interest_rate && (
                            <div>
                                <div className="text-xs text-violet-200">Interest Rate</div>
                                <div className="mt-1 text-lg font-semibold">{eligibleMatches[0].assigned_interest_rate}%</div>
                            </div>
                        )}
                        {application.business_credit?.paynet_score && (
                            <div>
                                <div className="text-xs text-violet-200">PayNet Score</div>
                                <div className="mt-1 text-lg font-semibold">{application.business_credit.paynet_score}</div>
                            </div>
                        )}
                        {application.guarantors?.[0]?.fico && (
                            <div>
                                <div className="text-xs text-violet-200">FICO</div>
                                <div className="mt-1 text-lg font-semibold">{application.guarantors[0].fico}</div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Tabs */}
            <div className="border-b border-slate-200">
                <nav className="flex gap-6 overflow-x-auto">
                    {TABS.map((tab) => (
                        <button
                            key={tab.id}
                            className={`whitespace-nowrap border-b-2 px-1 py-3 text-sm font-medium transition-colors ${
                                activeTab === tab.id
                                    ? 'border-slate-900 text-slate-900'
                                    : 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700'
                            }`}
                            onClick={() => setActiveTab(tab.id)}
                        >
                            {tab.label}
                        </button>
                    ))}
                </nav>
            </div>

            {/* Tab Content */}
            <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
                {activeTab === 'application' && (
                    <ApplicationFormTab application={application} />
                )}
                {activeTab === 'kyb' && (
                    <KYBReportTab application={application} />
                )}
                {activeTab === 'fraud' && (
                    <FraudDetectionTab application={application} />
                )}
                {activeTab === 'bank' && (
                    <BankStatementTab application={application} matchResults={eligibleMatches} />
                )}
                {activeTab === 'financial' && (
                    <FinancialStatementTab application={application} />
                )}
                {activeTab === 'tax' && (
                    <TaxFormsTab application={application} />
                )}
                {activeTab === 'credit' && (
                    <CreditReportTab application={application} />
                )}
                {activeTab === 'workflow' && (
                    <WorkflowTab application={application} />
                )}
            </div>
        </div>
    )
}

// Application Form Tab
function ApplicationFormTab({ application }: { application: Application }) {
    const [viewMode, setViewMode] = useState<'raw' | 'files'>('raw')
    const [ownerIndex, setOwnerIndex] = useState(0)

    const guarantor = application.guarantors?.[ownerIndex]
    const totalOwners = application.guarantors?.length || 0

    return (
        <div>
            {/* Sub-tabs */}
            <div className="border-b border-slate-200 px-6">
                <div className="flex gap-4">
                    <button
                        className={`border-b-2 py-3 text-sm font-medium ${viewMode === 'raw' ? 'border-slate-900 text-slate-900' : 'border-transparent text-slate-500'}`}
                        onClick={() => setViewMode('raw')}
                    >
                        Raw
                    </button>
                    <button
                        className={`border-b-2 py-3 text-sm font-medium ${viewMode === 'files' ? 'border-slate-900 text-slate-900' : 'border-transparent text-slate-500'}`}
                        onClick={() => setViewMode('files')}
                    >
                        Files
                    </button>
                </div>
            </div>

            <div className="p-6">
                {/* Owner Information */}
                <div className="rounded-lg border border-slate-200 p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-slate-900">Owner Information</h3>
                        {totalOwners > 1 && (
                            <div className="flex items-center gap-2">
                                <button
                                    className="rounded p-1 hover:bg-slate-100 disabled:opacity-50"
                                    disabled={ownerIndex === 0}
                                    onClick={() => setOwnerIndex(ownerIndex - 1)}
                                >
                                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                                    </svg>
                                </button>
                                <span className="text-sm text-slate-500">{ownerIndex + 1} of {totalOwners}</span>
                                <button
                                    className="rounded p-1 hover:bg-slate-100 disabled:opacity-50"
                                    disabled={ownerIndex >= totalOwners - 1}
                                    onClick={() => setOwnerIndex(ownerIndex + 1)}
                                >
                                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                    </svg>
                                </button>
                            </div>
                        )}
                    </div>

                    <div className="grid grid-cols-2 gap-6">
                        <div>
                            <div className="text-xs text-slate-500">Name</div>
                            <div className="mt-1 font-medium text-slate-900">
                                {guarantor?.first_name} {guarantor?.last_name}
                            </div>
                        </div>
                        <div>
                            <div className="text-xs text-slate-500">SSN</div>
                            <div className="mt-1 font-medium text-slate-900">***-**-****</div>
                        </div>
                        <div>
                            <div className="text-xs text-slate-500">Date of Birth</div>
                            <div className="mt-1 font-medium text-slate-900">—</div>
                        </div>
                        <div>
                            <div className="text-xs text-slate-500">Email</div>
                            <div className="mt-1 font-medium text-slate-900">{application.merchant_email || '—'}</div>
                        </div>
                        <div>
                            <div className="text-xs text-slate-500">Phone</div>
                            <div className="mt-1 font-medium text-slate-900">—</div>
                        </div>
                        <div>
                            <div className="text-xs text-slate-500">Address</div>
                            <div className="mt-1 font-medium text-slate-900">—</div>
                        </div>
                        <div>
                            <div className="text-xs text-slate-500">FICO Score</div>
                            <div className="mt-1 font-medium text-slate-900">{guarantor?.fico || '—'}</div>
                        </div>
                        <div>
                            <div className="text-xs text-slate-500">Ownership Percentage</div>
                            <div className="mt-1 font-medium text-slate-900">{guarantor?.is_primary ? '100%' : '—'}</div>
                        </div>
                    </div>
                </div>

                {/* Business Information */}
                <div className="mt-6 rounded-lg border border-slate-200 p-6">
                    <h3 className="text-lg font-semibold text-slate-900 mb-4">Business Information</h3>
                    <div className="grid grid-cols-2 gap-6">
                        <div>
                            <div className="text-xs text-slate-500">Business Name</div>
                            <div className="mt-1 font-medium text-slate-900">{application.business_name || '—'}</div>
                        </div>
                        <div>
                            <div className="text-xs text-slate-500">PayNet Score</div>
                            <div className="mt-1 font-medium text-slate-900">{application.business_credit?.paynet_score || '—'}</div>
                        </div>
                        <div>
                            <div className="text-xs text-slate-500">Email</div>
                            <div className="mt-1 font-medium text-slate-900">{application.merchant_email}</div>
                        </div>
                        <div>
                            <div className="text-xs text-slate-500">Loan Type</div>
                            <div className="mt-1 font-medium text-slate-900">{application.loan_type || '—'}</div>
                        </div>
                    </div>
                </div>

                {/* Equipment Information */}
                {application.equipment && application.equipment.length > 0 && (
                    <div className="mt-6 rounded-lg border border-slate-200 p-6">
                        <h3 className="text-lg font-semibold text-slate-900 mb-4">Equipment Information</h3>
                        {application.equipment.map((eq, idx) => (
                            <div key={eq.id || idx} className="grid grid-cols-3 gap-6 mb-4">
                                <div>
                                    <div className="text-xs text-slate-500">Type</div>
                                    <div className="mt-1 font-medium text-slate-900">{eq.type || '—'}</div>
                                </div>
                                <div>
                                    <div className="text-xs text-slate-500">Year</div>
                                    <div className="mt-1 font-medium text-slate-900">{eq.year || '—'}</div>
                                </div>
                                <div>
                                    <div className="text-xs text-slate-500">Mileage</div>
                                    <div className="mt-1 font-medium text-slate-900">
                                        {eq.mileage ? eq.mileage.toLocaleString() : '—'}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Loan Request */}
                {application.loan_request && (
                    <div className="mt-6 rounded-lg border border-slate-200 p-6">
                        <h3 className="text-lg font-semibold text-slate-900 mb-4">Loan Request</h3>
                        <div className="grid grid-cols-3 gap-6">
                            <div>
                                <div className="text-xs text-slate-500">Amount</div>
                                <div className="mt-1 font-medium text-slate-900">
                                    {application.loan_request.amount
                                        ? `$${Number(application.loan_request.amount).toLocaleString()}`
                                        : '—'}
                                </div>
                            </div>
                            <div>
                                <div className="text-xs text-slate-500">Term</div>
                                <div className="mt-1 font-medium text-slate-900">
                                    {application.loan_request.term_months ? `${application.loan_request.term_months} months` : '—'}
                                </div>
                            </div>
                            <div>
                                <div className="text-xs text-slate-500">Down Payment</div>
                                <div className="mt-1 font-medium text-slate-900">
                                    {application.loan_request.down_payment
                                        ? `$${Number(application.loan_request.down_payment).toLocaleString()}`
                                        : '—'}
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

// KYB Report Tab
function KYBReportTab({ application }: { application: Application }) {
    // Mock KYB data based on application
    const kybData = {
        overallMatch: 90,
        businessNameMatch: true,
        ownerMatch: false,
        cityMatch: false,
        legalName: application.business_name || 'Unknown',
        filingNumber: '8180835',
        filingDate: 'Apr 10, 2024',
        timeInBusiness: '1 years 3 months',
        address: '1401 21ST ST STE 8 SACRAMENTO, CA 95811',
        status: 'Active',
        entityType: 'Stock Corporation – Out of State – Stock',
        agentName: '1505 Corporation REGISTERED AGENTS INC',
        state: 'California',
    }

    return (
        <div className="p-6">
            <div className="flex gap-6">
                {/* Left Panel - KYB Details */}
                <div className="flex-1">
                    {/* Match Score */}
                    <div className="mb-6">
                        <div className="flex items-center gap-3">
                            <span className="text-lg font-semibold text-slate-900">Overall Match: {kybData.overallMatch}%</span>
                            <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">
                                Strong Match
                            </span>
                        </div>
                        <div className="mt-3 flex flex-wrap gap-2">
                            <span className={`rounded-full px-2 py-1 text-xs ${kybData.businessNameMatch ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>
                                {kybData.businessNameMatch ? '✓' : '✗'} 100% match for business name
                            </span>
                            <span className={`rounded-full px-2 py-1 text-xs ${kybData.ownerMatch ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}>
                                {kybData.ownerMatch ? '✓' : '○'} Owner does not match
                            </span>
                            <span className={`rounded-full px-2 py-1 text-xs ${kybData.cityMatch ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}>
                                {kybData.cityMatch ? '✓' : '○'} City does not match
                            </span>
                        </div>
                    </div>

                    {/* Business Details */}
                    <div className="space-y-4 rounded-lg border border-slate-200 p-6">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <div className="text-xs text-slate-500">Legal name</div>
                                <div className="mt-1 flex items-center gap-2 font-medium text-slate-900">
                                    {kybData.legalName}
                                    <span className="rounded bg-emerald-100 p-0.5 text-emerald-600">
                                        <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                        </svg>
                                    </span>
                                </div>
                            </div>
                            <div>
                                <div className="text-xs text-slate-500">Filing number</div>
                                <div className="mt-1 font-medium text-slate-900">{kybData.filingNumber}</div>
                            </div>
                            <div>
                                <div className="text-xs text-slate-500">Filing date</div>
                                <div className="mt-1 font-medium text-slate-900">{kybData.filingDate}</div>
                            </div>
                            <div>
                                <div className="text-xs text-slate-500">Time in Business</div>
                                <div className="mt-1 font-medium text-slate-900">{kybData.timeInBusiness}</div>
                            </div>
                            <div className="col-span-2">
                                <div className="text-xs text-slate-500">Address</div>
                                <div className="mt-1 font-medium text-slate-900">{kybData.address}</div>
                            </div>
                            <div>
                                <div className="text-xs text-slate-500">Status</div>
                                <div className="mt-1">
                                    <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">
                                        {kybData.status}
                                    </span>
                                </div>
                            </div>
                            <div>
                                <div className="text-xs text-slate-500">Entity type</div>
                                <div className="mt-1 font-medium text-slate-900">{kybData.entityType}</div>
                            </div>
                            <div>
                                <div className="text-xs text-slate-500">Agent name</div>
                                <div className="mt-1 font-medium text-slate-900">{kybData.agentName}</div>
                            </div>
                            <div>
                                <div className="text-xs text-slate-500">State</div>
                                <div className="mt-1 font-medium text-slate-900">{kybData.state}</div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Panel - Preview */}
                <div className="w-80">
                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                        <div className="mb-3 flex items-center justify-between">
                            <span className="text-sm font-medium text-slate-700">Business Search</span>
                            <span className="text-xs text-slate-500">100%</span>
                        </div>
                        <div className="aspect-[4/5] rounded bg-white shadow-sm"></div>
                    </div>
                </div>
            </div>
        </div>
    )
}

// Fraud Detection Tab
function FraudDetectionTab({ application }: { application: Application }) {
    const fraudChecks = [
        { name: 'Identity Verification', status: 'passed', score: 95 },
        { name: 'Address Verification', status: 'passed', score: 88 },
        { name: 'Business Verification', status: 'passed', score: 92 },
        { name: 'Document Authenticity', status: 'pending', score: null },
        { name: 'Bank Account Verification', status: 'passed', score: 90 },
    ]

    return (
        <div className="p-6">
            <div className="mb-6">
                <h3 className="text-lg font-semibold text-slate-900">Fraud Detection Summary</h3>
                <p className="mt-1 text-sm text-slate-600">
                    Automated fraud checks for {application.business_name || 'this application'}
                </p>
            </div>

            <div className="grid gap-4">
                {fraudChecks.map((check) => (
                    <div key={check.name} className="flex items-center justify-between rounded-lg border border-slate-200 p-4">
                        <div className="flex items-center gap-3">
                            {check.status === 'passed' ? (
                                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-100">
                                    <svg className="h-4 w-4 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                    </svg>
                                </div>
                            ) : check.status === 'failed' ? (
                                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-red-100">
                                    <svg className="h-4 w-4 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                                    </svg>
                                </div>
                            ) : (
                                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-amber-100">
                                    <svg className="h-4 w-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                </div>
                            )}
                            <div>
                                <div className="font-medium text-slate-900">{check.name}</div>
                                <div className="text-xs text-slate-500 capitalize">{check.status}</div>
                            </div>
                        </div>
                        {check.score !== null && (
                            <div className="text-right">
                                <div className="text-lg font-semibold text-slate-900">{check.score}%</div>
                                <div className="text-xs text-slate-500">Confidence</div>
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    )
}

// Bank Statement Tab
function BankStatementTab({ application, matchResults }: { application: Application; matchResults: MatchResult[] }) {
    const bankData = {
        grossProfitMargin: 25.0,
        netProfit: 10.58,
        dscr: 1.40,
        assetTurnover: 0.63,
        debtToAssets: 1.07,
        debtToEquity: 0.63,
        netIncome: 59782.00,
        operatingActivities: 49782.00,
        operatingExpenses: 9782.00,
        avgBalance: 14782.00,
        minBalance: -20800.30,
        negativeBalanceDays: 5,
    }

    const topMatch = matchResults[0]

    return (
        <div className="p-6">
            {/* Header */}
            <div className="mb-6 flex items-center justify-between">
                <div>
                    <h3 className="text-xl font-semibold text-slate-900">{application.business_name || 'Business'}</h3>
                    <div className="mt-1 flex items-center gap-2">
                        <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">
                            7/8 Criteria met
                        </span>
                    </div>
                    <p className="mt-2 text-sm text-slate-600">
                        Given the company's strong financial performance, active status, and the purpose of the loan,{' '}
                        {application.business_name || 'this business'} presents a favorable case for the requested{' '}
                        {application.loan_type || 'financing'}.
                    </p>
                </div>
                <div className="flex gap-2">
                    <button className="rounded-md bg-emerald-500 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-600">
                        Approve
                    </button>
                    <button className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
                        Reject
                    </button>
                </div>
            </div>

            {/* Loan Summary */}
            <div className="mb-6 grid grid-cols-4 gap-4">
                <div className="rounded-lg border border-slate-200 p-4">
                    <div className="text-xs text-slate-500">Amount</div>
                    <div className="mt-1 text-lg font-semibold">
                        ${application.loan_request?.amount ? Number(application.loan_request.amount).toLocaleString() : '—'}
                    </div>
                </div>
                <div className="rounded-lg border border-slate-200 p-4">
                    <div className="text-xs text-slate-500">Category</div>
                    <div className="mt-1 text-lg font-semibold">{application.loan_type || '—'}</div>
                </div>
                {topMatch?.assigned_term_months && (
                    <div className="rounded-lg border border-slate-200 p-4">
                        <div className="text-xs text-slate-500">Term</div>
                        <div className="mt-1 text-lg font-semibold">{topMatch.assigned_term_months} months</div>
                    </div>
                )}
                {topMatch?.assigned_interest_rate && (
                    <div className="rounded-lg border border-slate-200 p-4">
                        <div className="text-xs text-slate-500">Interest Rate</div>
                        <div className="mt-1 text-lg font-semibold">{topMatch.assigned_interest_rate}%</div>
                    </div>
                )}
            </div>

            {/* Financial Ratios */}
            <div className="mb-6 grid grid-cols-6 gap-4">
                <div className="rounded-lg border border-slate-200 p-4">
                    <div className="text-xs text-slate-500">Gross profit margin</div>
                    <div className="mt-1 text-xl font-semibold text-slate-900">{bankData.grossProfitMargin}%</div>
                    <div className="mt-1 flex items-center text-xs text-emerald-600">
                        <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
                        </svg>
                        32% in May 2023
                    </div>
                </div>
                <div className="rounded-lg border border-slate-200 p-4">
                    <div className="text-xs text-slate-500">Net profit</div>
                    <div className="mt-1 text-xl font-semibold text-slate-900">{bankData.netProfit}%</div>
                    <div className="mt-1 flex items-center text-xs text-emerald-600">
                        <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
                        </svg>
                        28% in May 2023
                    </div>
                </div>
                <div className="rounded-lg border border-slate-200 p-4">
                    <div className="text-xs text-slate-500">DSCR</div>
                    <div className="mt-1 text-xl font-semibold text-slate-900">{bankData.dscr}</div>
                    <div className="mt-1 flex items-center text-xs text-emerald-600">
                        <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
                        </svg>
                        15% in May 2023
                    </div>
                </div>
                <div className="rounded-lg border border-slate-200 p-4">
                    <div className="text-xs text-slate-500">Asset turnover</div>
                    <div className="mt-1 text-xl font-semibold text-slate-900">{bankData.assetTurnover}</div>
                    <div className="mt-1 flex items-center text-xs text-red-600">
                        <svg className="h-3 w-3 rotate-180" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
                        </svg>
                        32% in May 2023
                    </div>
                </div>
                <div className="rounded-lg border border-slate-200 p-4">
                    <div className="text-xs text-slate-500">Debt to assets Ratio</div>
                    <div className="mt-1 text-xl font-semibold text-slate-900">{bankData.debtToAssets}</div>
                    <div className="mt-1 flex items-center text-xs text-red-600">
                        <svg className="h-3 w-3 rotate-180" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
                        </svg>
                        32% in May 2023
                    </div>
                </div>
                <div className="rounded-lg border border-slate-200 p-4">
                    <div className="text-xs text-slate-500">Debt to equity ratio</div>
                    <div className="mt-1 text-xl font-semibold text-slate-900">{bankData.debtToEquity}</div>
                    <div className="mt-1 flex items-center text-xs text-amber-600">
                        <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM7 9a1 1 0 000 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                        </svg>
                        18.6% in May 2023
                    </div>
                </div>
            </div>

            {/* Transactions and Balance */}
            <div className="grid grid-cols-2 gap-6">
                <div>
                    <h4 className="mb-4 text-sm font-semibold uppercase text-slate-500">Transactions Amount by Category</h4>
                    <div className="grid grid-cols-3 gap-4">
                        <div className="rounded-lg border border-slate-200 p-4">
                            <div className="text-xs text-slate-500">Net Income</div>
                            <div className="mt-1 text-lg font-semibold text-slate-900">
                                ${bankData.netIncome.toLocaleString()}
                            </div>
                        </div>
                        <div className="rounded-lg border border-slate-200 p-4">
                            <div className="text-xs text-slate-500">Operating activities</div>
                            <div className="mt-1 text-lg font-semibold text-slate-900">
                                ${bankData.operatingActivities.toLocaleString()}
                            </div>
                        </div>
                        <div className="rounded-lg border border-slate-200 p-4">
                            <div className="text-xs text-slate-500">Operating expenses</div>
                            <div className="mt-1 text-lg font-semibold text-slate-900">
                                ${bankData.operatingExpenses.toLocaleString()}
                            </div>
                        </div>
                    </div>
                    {/* Chart placeholder */}
                    <div className="mt-4 h-40 rounded-lg border border-slate-200 bg-slate-50"></div>
                </div>
                <div>
                    <h4 className="mb-4 text-sm font-semibold uppercase text-slate-500">Daily Ending Balance</h4>
                    <div className="grid grid-cols-3 gap-4">
                        <div className="rounded-lg border border-slate-200 p-4">
                            <div className="text-xs text-slate-500">Avg. balance</div>
                            <div className="mt-1 text-lg font-semibold text-slate-900">
                                ${bankData.avgBalance.toLocaleString()}
                            </div>
                        </div>
                        <div className="rounded-lg border border-slate-200 p-4">
                            <div className="text-xs text-slate-500">Minimum balance</div>
                            <div className="mt-1 text-lg font-semibold text-red-600">
                                -${Math.abs(bankData.minBalance).toLocaleString()}
                            </div>
                        </div>
                        <div className="rounded-lg border border-slate-200 p-4">
                            <div className="text-xs text-slate-500">Negative balances days</div>
                            <div className="mt-1 text-lg font-semibold text-slate-900">{bankData.negativeBalanceDays}</div>
                        </div>
                    </div>
                    {/* Chart placeholder */}
                    <div className="mt-4 h-40 rounded-lg border border-slate-200 bg-slate-50"></div>
                </div>
            </div>
        </div>
    )
}

// Financial Statement Tab
function FinancialStatementTab({ application }: { application: Application }) {
    return (
        <div className="p-6">
            <div className="mb-6">
                <h3 className="text-lg font-semibold text-slate-900">Financial Statements</h3>
                <p className="mt-1 text-sm text-slate-600">
                    Financial statement analysis for {application.business_name || 'this business'}
                </p>
            </div>

            <div className="rounded-lg border border-slate-200 bg-slate-50 p-8 text-center">
                <svg className="mx-auto h-12 w-12 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h4 className="mt-4 text-sm font-medium text-slate-900">No Financial Statements Uploaded</h4>
                <p className="mt-1 text-sm text-slate-500">
                    Financial statements will appear here once they are uploaded and processed.
                </p>
            </div>
        </div>
    )
}

// Tax Forms Tab
function TaxFormsTab({ application }: { application: Application }) {
    return (
        <div className="p-6">
            <div className="mb-6">
                <h3 className="text-lg font-semibold text-slate-900">Tax Forms</h3>
                <p className="mt-1 text-sm text-slate-600">
                    Tax documents for {application.business_name || 'this business'}
                </p>
            </div>

            <div className="rounded-lg border border-slate-200 bg-slate-50 p-8 text-center">
                <svg className="mx-auto h-12 w-12 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2z" />
                </svg>
                <h4 className="mt-4 text-sm font-medium text-slate-900">No Tax Forms Uploaded</h4>
                <p className="mt-1 text-sm text-slate-500">
                    Tax forms will appear here once they are uploaded and processed.
                </p>
            </div>
        </div>
    )
}

// Credit Report Tab
function CreditReportTab({ application }: { application: Application }) {
    const guarantor = application.guarantors?.[0]

    return (
        <div className="p-6">
            <div className="mb-6">
                <h3 className="text-lg font-semibold text-slate-900">Credit Report</h3>
                <p className="mt-1 text-sm text-slate-600">
                    Credit information for {guarantor?.first_name} {guarantor?.last_name}
                </p>
            </div>

            <div className="grid grid-cols-3 gap-6">
                <div className="rounded-lg border border-slate-200 p-6 text-center">
                    <div className="text-3xl font-bold text-slate-900">{guarantor?.fico || '—'}</div>
                    <div className="mt-1 text-sm text-slate-500">FICO Score</div>
                    {guarantor?.fico && guarantor.fico >= 700 && (
                        <div className="mt-2 text-xs text-emerald-600">Good Standing</div>
                    )}
                </div>
                <div className="rounded-lg border border-slate-200 p-6 text-center">
                    <div className="text-3xl font-bold text-slate-900">
                        {application.business_credit?.paynet_score || '—'}
                    </div>
                    <div className="mt-1 text-sm text-slate-500">PayNet Score</div>
                </div>
                <div className="rounded-lg border border-slate-200 p-6 text-center">
                    <div className="text-3xl font-bold text-slate-900">
                        {application.business_credit?.revolving_utilization || '—'}%
                    </div>
                    <div className="mt-1 text-sm text-slate-500">Revolving Utilization</div>
                </div>
            </div>

            <div className="mt-6 rounded-lg border border-slate-200 bg-slate-50 p-8 text-center">
                <svg className="mx-auto h-12 w-12 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h4 className="mt-4 text-sm font-medium text-slate-900">Full Credit Report</h4>
                <p className="mt-1 text-sm text-slate-500">
                    Detailed credit report will be available after authorization.
                </p>
            </div>
        </div>
    )
}

// Workflow Tab
function WorkflowTab({ application: _application }: { application: Application }) {
    const workflowSteps = [
        { name: 'Application Submitted', status: 'completed', date: 'Dec 29, 2024 10:30 AM' },
        { name: 'KYB Verification', status: 'completed', date: 'Dec 29, 2024 10:31 AM' },
        { name: 'Credit Check', status: 'completed', date: 'Dec 29, 2024 10:31 AM' },
        { name: 'Document Review', status: 'in_progress', date: null },
        { name: 'Underwriting', status: 'pending', date: null },
        { name: 'Final Decision', status: 'pending', date: null },
    ]

    return (
        <div className="p-6">
            <div className="mb-6">
                <h3 className="text-lg font-semibold text-slate-900">Application Workflow</h3>
                <p className="mt-1 text-sm text-slate-600">Track the progress of this application</p>
            </div>

            <div className="space-y-4">
                {workflowSteps.map((step, idx) => (
                    <div key={step.name} className="flex items-start gap-4">
                        <div className="flex flex-col items-center">
                            {step.status === 'completed' ? (
                                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-100">
                                    <svg className="h-4 w-4 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                    </svg>
                                </div>
                            ) : step.status === 'in_progress' ? (
                                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100">
                                    <div className="h-3 w-3 animate-pulse rounded-full bg-blue-500"></div>
                                </div>
                            ) : (
                                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100">
                                    <div className="h-2 w-2 rounded-full bg-slate-400"></div>
                                </div>
                            )}
                            {idx < workflowSteps.length - 1 && (
                                <div className={`h-8 w-0.5 ${step.status === 'completed' ? 'bg-emerald-200' : 'bg-slate-200'}`}></div>
                            )}
                        </div>
                        <div className="flex-1 pb-4">
                            <div className="font-medium text-slate-900">{step.name}</div>
                            {step.date && <div className="text-sm text-slate-500">{step.date}</div>}
                            {step.status === 'in_progress' && (
                                <div className="mt-1 text-sm text-blue-600">In Progress</div>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}
