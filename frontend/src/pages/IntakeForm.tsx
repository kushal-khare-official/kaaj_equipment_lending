import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { businessSearch, businessPrefill, createApplication } from '../api'

type BusinessSearchResult = {
    id: string
    legal_name: string
    city: string
    state: string
}

type IntakeFormData = {
    business_name: string
    business_id: string | null
    loan_type: 'Equipment Finance' | 'Working Capital' | 'Refinance'
    loan_amount: string
    equipment_type: string
    email: string
}

const initialFormData: IntakeFormData = {
    business_name: '',
    business_id: null,
    loan_type: 'Equipment Finance',
    loan_amount: '',
    equipment_type: '',
    email: '',
}

export function IntakeFormPage() {
    const navigate = useNavigate()
    const [formData, setFormData] = useState<IntakeFormData>(initialFormData)
    const [searchResults, setSearchResults] = useState<BusinessSearchResult[]>([])
    const [showDropdown, setShowDropdown] = useState(false)
    const [loading, setLoading] = useState(false)
    const [searchLoading, setSearchLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const handleSearchChange = async (value: string) => {
        setFormData(prev => ({ ...prev, business_name: value.toUpperCase(), business_id: null }))
        if (value.length >= 2) {
            setSearchLoading(true)
            try {
                const res = await businessSearch(value)
                if (res.status === 'success') {
                    setSearchResults(res.results || [])
                    setShowDropdown(true)
                }
            } catch (e) {
                console.error('Search error:', e)
                setSearchResults([])
            } finally {
                setSearchLoading(false)
            }
        } else {
            setShowDropdown(false)
            setSearchResults([])
        }
    }

    const handleSelectBusiness = async (result: BusinessSearchResult) => {
        setFormData(prev => ({
            ...prev,
            business_name: result.legal_name,
            business_id: result.id,
        }))
        setShowDropdown(false)

        // Prefill email if available
        try {
            const prefillRes = await businessPrefill(result.id)
            if (prefillRes.status === 'success' && prefillRes.data?.email) {
                setFormData(prev => ({ ...prev, email: prefillRes.data.email }))
            }
        } catch (e) {
            console.error('Prefill error:', e)
        }
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setError(null)

        try {
            // Create application with basic info
            const payload = {
                merchant_email: formData.email,
                business_name: formData.business_name,
                loan_type: formData.loan_type,
                equipment: formData.loan_type === 'Equipment Finance' && formData.equipment_type
                    ? [{ type: formData.equipment_type }]
                    : [],
                loan_request: formData.loan_amount
                    ? { amount: Number(formData.loan_amount.replace(/[^0-9.]/g, '')) }
                    : undefined,
            }

            const res = await createApplication(payload)
            // Navigate to the full application form with the new application ID
            navigate(`/apply/${res.id}`)
        } catch (e: any) {
            setError(e.message || 'Failed to create application')
        } finally {
            setLoading(false)
        }
    }

    const isValid = formData.business_name && formData.email && formData.loan_amount

    return (
        <div className="mx-auto max-w-2xl">
            <div className="rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
                <div className="text-center mb-8">
                    <h1 className="text-2xl font-semibold text-slate-900">Get Started with Your Loan Application</h1>
                    <p className="mt-2 text-sm text-slate-600">
                        Tell us a bit about your business and financing needs to begin.
                    </p>
                </div>

                {error && (
                    <div className="mb-6 rounded-md bg-red-50 p-4 text-sm text-red-700">{error}</div>
                )}

                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Business Name with Search */}
                    <div>
                        <label className="block text-sm font-medium text-slate-700">Legal Business Name *</label>
                        <div className="relative mt-1">
                            <input
                                type="text"
                                className="w-full rounded-md border border-slate-300 px-4 py-3 text-sm uppercase focus:border-slate-500 focus:outline-none"
                                value={formData.business_name}
                                onChange={(e) => handleSearchChange(e.target.value)}
                                onFocus={() => searchResults.length > 0 && setShowDropdown(true)}
                                placeholder="Start typing to search..."
                            />
                            {searchLoading && (
                                <div className="absolute right-3 top-3">
                                    <svg className="h-5 w-5 animate-spin text-slate-400" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                    </svg>
                                </div>
                            )}
                            {showDropdown && searchResults.length > 0 && (
                                <div className="absolute z-10 mt-1 w-full rounded-md border border-slate-200 bg-white shadow-lg">
                                    <ul className="max-h-60 overflow-auto py-1">
                                        {searchResults.map((result) => (
                                            <li
                                                key={result.id}
                                                className="cursor-pointer px-4 py-3 hover:bg-slate-100"
                                                onClick={() => handleSelectBusiness(result)}
                                            >
                                                <div className="font-medium text-slate-900">{result.legal_name}</div>
                                                <div className="text-sm text-slate-500">{result.city}, {result.state}</div>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                        {formData.business_id && (
                            <div className="mt-2 flex items-center gap-2">
                                <svg className="h-4 w-4 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                </svg>
                                <span className="text-sm text-emerald-700">Business found in database</span>
                            </div>
                        )}
                    </div>

                    {/* Loan Type */}
                    <div>
                        <label className="block text-sm font-medium text-slate-700">Type of Loan *</label>
                        <select
                            className="mt-1 w-full rounded-md border border-slate-300 px-4 py-3 text-sm focus:border-slate-500 focus:outline-none"
                            value={formData.loan_type}
                            onChange={(e) => setFormData(prev => ({ ...prev, loan_type: e.target.value as IntakeFormData['loan_type'] }))}
                        >
                            <option value="Equipment Finance">Equipment Finance</option>
                            <option value="Working Capital">Working Capital</option>
                            <option value="Refinance">Refinance</option>
                        </select>
                    </div>

                    {/* Loan Amount */}
                    <div>
                        <label className="block text-sm font-medium text-slate-700">Loan Amount *</label>
                        <div className="relative mt-1">
                            <span className="absolute left-4 top-3 text-slate-500">$</span>
                            <input
                                type="text"
                                className="w-full rounded-md border border-slate-300 pl-8 pr-4 py-3 text-sm focus:border-slate-500 focus:outline-none"
                                value={formData.loan_amount}
                                onChange={(e) => setFormData(prev => ({ ...prev, loan_amount: e.target.value }))}
                                placeholder="75,000"
                            />
                        </div>
                    </div>

                    {/* Equipment Type (conditional) */}
                    {formData.loan_type === 'Equipment Finance' && (
                        <div>
                            <label className="block text-sm font-medium text-slate-700">Equipment Type</label>
                            <input
                                type="text"
                                className="mt-1 w-full rounded-md border border-slate-300 px-4 py-3 text-sm focus:border-slate-500 focus:outline-none"
                                value={formData.equipment_type}
                                onChange={(e) => setFormData(prev => ({ ...prev, equipment_type: e.target.value }))}
                                placeholder="Truck, Trailer, Construction Equipment, etc."
                            />
                        </div>
                    )}

                    {/* Email */}
                    <div>
                        <label className="block text-sm font-medium text-slate-700">Email Address *</label>
                        <input
                            type="email"
                            className="mt-1 w-full rounded-md border border-slate-300 px-4 py-3 text-sm focus:border-slate-500 focus:outline-none"
                            value={formData.email}
                            onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                            placeholder="you@company.com"
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={!isValid || loading}
                        className="w-full rounded-md bg-slate-900 px-6 py-3 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-50"
                    >
                        {loading ? 'Creating Application...' : 'Continue to Full Application'}
                    </button>
                </form>

                <p className="mt-6 text-center text-xs text-slate-500">
                    By continuing, you agree to our terms of service and privacy policy.
                </p>
            </div>
        </div>
    )
}
