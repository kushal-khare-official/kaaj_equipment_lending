import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
    businessPrefill,
    businessSearch,
    createApplication,
    creditCheck,
    getApplication,
    health,
    kybCheck,
    kycCheck,
    latestMatch,
    updateApplication,
} from '../api'

type BusinessSearchResult = {
    id: string
    legal_name: string
    city: string
    state: string
}

// Types
type Address = {
    street: string
    city: string
    state: string
    zip: string
}

type Guarantor = {
    first_name: string
    last_name: string
    title: string
    ownership_pct: number
    address: Address
    phone: string
    email: string
    ssn: string
    fico?: number
    kyc_verified?: boolean
    is_primary: boolean
}

type BusinessInfo = {
    legal_name: string
    dba: string
    address: Address
    phone: string
    email: string
    tin: string
    paynet_score?: number
}

type Equipment = {
    type: string
    make: string
    model: string
    year: string
    mileage: string
    titled: boolean
    private_party: boolean
}

type LoanDetails = {
    loan_type: 'Equipment Finance' | 'Working Capital' | 'Refinance'
    amount: string
    term_months: string
    down_payment: string
    equipment: Equipment[]
}

type FormData = {
    business: BusinessInfo
    guarantors: Guarantor[]
    loan: LoanDetails
    documents: { type: string; uploaded: boolean }[]
    terms_accepted: boolean
    signature: string
}

const STEPS = [
    { id: 1, name: 'Business Info', description: 'Legal business information' },
    { id: 2, name: 'Guarantors', description: 'Owner and guarantor details' },
    { id: 3, name: 'Loan Details', description: 'Loan type and amount' },
    { id: 4, name: 'Documents', description: 'Required documents' },
    { id: 5, name: 'Review & Sign', description: 'Review matches and sign' },
    { id: 6, name: 'Complete', description: 'Application submitted' },
]

const emptyAddress: Address = { street: '', city: '', state: '', zip: '' }

const emptyGuarantor: Guarantor = {
    first_name: '',
    last_name: '',
    title: '',
    ownership_pct: 0,
    address: { ...emptyAddress },
    phone: '',
    email: '',
    ssn: '',
    is_primary: false,
}

const emptyEquipment: Equipment = {
    type: '',
    make: '',
    model: '',
    year: '',
    mileage: '',
    titled: false,
    private_party: false,
}

const initialFormData: FormData = {
    business: {
        legal_name: '',
        dba: '',
        address: { ...emptyAddress },
        phone: '',
        email: '',
        tin: '',
    },
    guarantors: [],
    loan: {
        loan_type: 'Equipment Finance',
        amount: '',
        term_months: '',
        down_payment: '',
        equipment: [{ ...emptyEquipment }],
    },
    documents: [],
    terms_accepted: false,
    signature: '',
}

// Stepper Component
function Stepper({ currentStep, steps }: { currentStep: number; steps: typeof STEPS }) {
    return (
        <nav aria-label="Progress" className="mb-8">
            <ol className="flex items-center">
                {steps.map((step, idx) => (
                    <li key={step.id} className={`relative ${idx !== steps.length - 1 ? 'flex-1' : ''}`}>
                        <div className="flex items-center">
                            <div
                                className={`flex h-10 w-10 items-center justify-center rounded-full border-2 text-sm font-semibold
                                    ${currentStep > step.id
                                        ? 'border-emerald-600 bg-emerald-600 text-white'
                                        : currentStep === step.id
                                            ? 'border-slate-900 bg-slate-900 text-white'
                                            : 'border-slate-300 bg-white text-slate-500'
                                    }`}
                            >
                                {currentStep > step.id ? (
                                    <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                    </svg>
                                ) : (
                                    step.id
                                )}
                            </div>
                            {idx !== steps.length - 1 && (
                                <div className={`h-0.5 w-75 ${currentStep > step.id ? 'bg-emerald-600' : 'bg-slate-300'}`} />
                            )}
                        </div>
                        <div className="mt-2">
                            <span className={`text-xs font-semibold ${currentStep >= step.id ? 'text-slate-900' : 'text-slate-500'}`}>
                                {step.name}
                            </span>
                        </div>
                    </li>
                ))}
            </ol>
        </nav>
    )
}

// Step 1: Business Information
function BusinessInfoStep({
    data,
    onChange,
    searchResults,
    onSearch,
    onSelectBusiness,
    loading,
}: {
    data: BusinessInfo
    onChange: (data: BusinessInfo) => void
    searchResults: BusinessSearchResult[]
    onSearch: (name: string) => void
    onSelectBusiness: (id: string) => void
    loading: boolean
}) {
    const [searchTerm, setSearchTerm] = useState(data.legal_name || '')
    const [showDropdown, setShowDropdown] = useState(false)
    const [selectedBusinessId, setSelectedBusinessId] = useState<string | null>(null)

    // Sync searchTerm when data.legal_name changes (e.g., from prefill)
    useEffect(() => {
        if (data.legal_name && data.legal_name !== searchTerm) {
            setSearchTerm(data.legal_name)
        }
    }, [data.legal_name])

    const handleSearchChange = (value: string) => {
        setSearchTerm(value.toUpperCase())
        if (value.length >= 2) {
            onSearch(value)
            setShowDropdown(true)
        } else {
            setShowDropdown(false)
        }
    }

    const handleSelectBusiness = (result: BusinessSearchResult) => {
        setSearchTerm(result.legal_name)
        setSelectedBusinessId(result.id)
        setShowDropdown(false)
        onSelectBusiness(result.id)
    }

    return (
        <div className="space-y-6">
            <h2 className="text-xl font-semibold text-slate-900">Business Legal Information</h2>
            <p className="text-sm text-slate-600">Enter your legal business name to search and auto-fill available information.</p>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-slate-700">Legal Business Name *</label>
                    <div className="relative mt-1">
                        <div className="flex gap-2">
                            <input
                                type="text"
                                className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm uppercase focus:border-slate-500 focus:outline-none"
                                value={searchTerm}
                                onChange={(e) => handleSearchChange(e.target.value)}
                                onFocus={() => searchResults.length > 0 && setShowDropdown(true)}
                                placeholder="Start typing to search..."
                            />
                            {loading && (
                                <span className="flex items-center text-sm text-slate-500">
                                    <svg className="mr-2 h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                    </svg>
                                    Loading...
                                </span>
                            )}
                        </div>
                        {showDropdown && searchResults.length > 0 && (
                            <div className="absolute z-10 mt-1 w-full rounded-md border border-slate-200 bg-white shadow-lg">
                                <ul className="max-h-60 overflow-auto py-1">
                                    {searchResults.map((result) => (
                                        <li
                                            key={result.id}
                                            className={`cursor-pointer px-4 py-3 hover:bg-slate-100 ${selectedBusinessId === result.id ? 'bg-slate-50' : ''}`}
                                            onClick={() => handleSelectBusiness(result)}
                                        >
                                            <div className="font-medium text-slate-900">{result.legal_name}</div>
                                            <div className="text-sm text-slate-500">{result.city}, {result.state}</div>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                        {showDropdown && searchResults.length === 0 && searchTerm.length >= 2 && !loading && (
                            <div className="absolute z-10 mt-1 w-full rounded-md border border-slate-200 bg-white p-4 shadow-lg">
                                <p className="text-sm text-slate-500">No businesses found matching "{searchTerm}"</p>
                            </div>
                        )}
                    </div>
                    {selectedBusinessId && data.legal_name && (
                        <div className="mt-2 flex items-center gap-2">
                            <svg className="h-4 w-4 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            <span className="text-sm text-emerald-700">Business selected: {data.legal_name}</span>
                        </div>
                    )}
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700">DBA (Doing Business As)</label>
                    <input
                        type="text"
                        className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                        value={data.dba}
                        onChange={(e) => onChange({ ...data, dba: e.target.value })}
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700">TIN (Tax ID) *</label>
                    <input
                        type="text"
                        className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                        value={data.tin}
                        onChange={(e) => onChange({ ...data, tin: e.target.value })}
                        placeholder="XX-XXXXXXX"
                    />
                </div>

                <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-slate-700">Street Address *</label>
                    <input
                        type="text"
                        className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                        value={data.address.street}
                        onChange={(e) => onChange({ ...data, address: { ...data.address, street: e.target.value } })}
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700">City *</label>
                    <input
                        type="text"
                        className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                        value={data.address.city}
                        onChange={(e) => onChange({ ...data, address: { ...data.address, city: e.target.value } })}
                    />
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-slate-700">State *</label>
                        <input
                            type="text"
                            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                            value={data.address.state}
                            onChange={(e) => onChange({ ...data, address: { ...data.address, state: e.target.value } })}
                            maxLength={2}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-700">ZIP *</label>
                        <input
                            type="text"
                            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                            value={data.address.zip}
                            onChange={(e) => onChange({ ...data, address: { ...data.address, zip: e.target.value } })}
                            maxLength={10}
                        />
                    </div>
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700">Business Phone *</label>
                    <input
                        type="tel"
                        className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                        value={data.phone}
                        onChange={(e) => onChange({ ...data, phone: e.target.value })}
                        placeholder="(XXX) XXX-XXXX"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700">Business Email *</label>
                    <input
                        type="email"
                        className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                        value={data.email}
                        onChange={(e) => onChange({ ...data, email: e.target.value })}
                    />
                </div>
            </div>

            {data.paynet_score !== undefined && (
                <div className="rounded-md bg-emerald-50 p-4">
                    <div className="flex items-center">
                        <svg className="h-5 w-5 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        <span className="ml-2 text-sm font-medium text-emerald-800">
                            PayNet Score: {data.paynet_score}
                        </span>
                    </div>
                </div>
            )}
        </div>
    )
}

// Step 2: Guarantors Information
function GuarantorsStep({
    guarantors,
    onChange,
    onRunChecks,
    loading,
}: {
    guarantors: Guarantor[]
    onChange: (guarantors: Guarantor[]) => void
    onRunChecks: (index: number) => void
    loading: number | null
}) {
    const addGuarantor = () => {
        onChange([...guarantors, { ...emptyGuarantor, is_primary: guarantors.length === 0 }])
    }

    const removeGuarantor = (index: number) => {
        const updated = guarantors.filter((_, i) => i !== index)
        if (updated.length > 0 && !updated.some(g => g.is_primary)) {
            updated[0].is_primary = true
        }
        onChange(updated)
    }

    const updateGuarantor = (index: number, field: keyof Guarantor, value: any) => {
        const updated = [...guarantors]
        if (field === 'is_primary' && value === true) {
            updated.forEach((g, i) => {
                g.is_primary = i === index
            })
        } else {
            (updated[index] as any)[field] = value
        }
        onChange(updated)
    }

    const updateGuarantorAddress = (index: number, field: keyof Address, value: string) => {
        const updated = [...guarantors]
        updated[index].address = { ...updated[index].address, [field]: value }
        onChange(updated)
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-xl font-semibold text-slate-900">Guarantors Information</h2>
                    <p className="text-sm text-slate-600">Add all owners/guarantors with 20% or more ownership.</p>
                </div>
                <button
                    type="button"
                    onClick={addGuarantor}
                    className="inline-flex items-center rounded-md bg-slate-900 px-3 py-2 text-sm font-semibold text-white hover:bg-slate-800"
                >
                    <svg className="mr-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Add Guarantor
                </button>
            </div>

            {guarantors.length === 0 && (
                <div className="rounded-md border-2 border-dashed border-slate-300 p-8 text-center">
                    <p className="text-sm text-slate-500">No guarantors added yet. Click "Add Guarantor" to begin.</p>
                </div>
            )}

            {guarantors.map((guarantor, idx) => (
                <div key={idx} className="rounded-lg border border-slate-200 bg-white p-6">
                    <div className="mb-4 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <h3 className="text-lg font-medium text-slate-900">Guarantor {idx + 1}</h3>
                            <label className="flex items-center gap-2 text-sm">
                                <input
                                    type="checkbox"
                                    checked={guarantor.is_primary}
                                    onChange={(e) => updateGuarantor(idx, 'is_primary', e.target.checked)}
                                    className="rounded border-slate-300"
                                />
                                Primary
                            </label>
                        </div>
                        <button
                            type="button"
                            onClick={() => removeGuarantor(idx)}
                            className="text-sm text-red-600 hover:text-red-800"
                        >
                            Remove
                        </button>
                    </div>

                    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                        <div>
                            <label className="block text-sm font-medium text-slate-700">First Name *</label>
                            <input
                                type="text"
                                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                                value={guarantor.first_name}
                                onChange={(e) => updateGuarantor(idx, 'first_name', e.target.value)}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-700">Last Name *</label>
                            <input
                                type="text"
                                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                                value={guarantor.last_name}
                                onChange={(e) => updateGuarantor(idx, 'last_name', e.target.value)}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-700">Title</label>
                            <input
                                type="text"
                                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                                value={guarantor.title}
                                onChange={(e) => updateGuarantor(idx, 'title', e.target.value)}
                                placeholder="CEO, Owner, etc."
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-700">Ownership %</label>
                            <input
                                type="number"
                                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                                value={guarantor.ownership_pct || ''}
                                onChange={(e) => updateGuarantor(idx, 'ownership_pct', Number(e.target.value))}
                                min={0}
                                max={100}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-700">Phone *</label>
                            <input
                                type="tel"
                                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                                value={guarantor.phone}
                                onChange={(e) => updateGuarantor(idx, 'phone', e.target.value)}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-700">Email *</label>
                            <input
                                type="email"
                                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                                value={guarantor.email}
                                onChange={(e) => updateGuarantor(idx, 'email', e.target.value)}
                            />
                        </div>
                        <div className="md:col-span-3">
                            <label className="block text-sm font-medium text-slate-700">Street Address *</label>
                            <input
                                type="text"
                                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                                value={guarantor.address.street}
                                onChange={(e) => updateGuarantorAddress(idx, 'street', e.target.value)}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-700">City *</label>
                            <input
                                type="text"
                                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                                value={guarantor.address.city}
                                onChange={(e) => updateGuarantorAddress(idx, 'city', e.target.value)}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-700">State *</label>
                            <input
                                type="text"
                                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                                value={guarantor.address.state}
                                onChange={(e) => updateGuarantorAddress(idx, 'state', e.target.value)}
                                maxLength={2}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-700">ZIP *</label>
                            <input
                                type="text"
                                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                                value={guarantor.address.zip}
                                onChange={(e) => updateGuarantorAddress(idx, 'zip', e.target.value)}
                            />
                        </div>
                        <div className="md:col-span-2">
                            <label className="block text-sm font-medium text-slate-700">SSN *</label>
                            <input
                                type="text"
                                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                                value={guarantor.ssn}
                                onChange={(e) => updateGuarantor(idx, 'ssn', e.target.value)}
                                placeholder="XXX-XX-XXXX"
                            />
                        </div>
                        <div className="flex items-end">
                            <button
                                type="button"
                                onClick={() => onRunChecks(idx)}
                                disabled={!guarantor.ssn || loading === idx}
                                className="w-full rounded-md bg-slate-100 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-200 disabled:opacity-50"
                            >
                                {loading === idx ? 'Running...' : 'Run Credit/KYC'}
                            </button>
                        </div>
                    </div>

                    {(guarantor.fico !== undefined || guarantor.kyc_verified !== undefined) && (
                        <div className="mt-4 flex gap-4">
                            {guarantor.fico !== undefined && (
                                <div className="rounded-md bg-emerald-50 px-3 py-2">
                                    <span className="text-sm font-medium text-emerald-800">FICO: {guarantor.fico}</span>
                                </div>
                            )}
                            {guarantor.kyc_verified !== undefined && (
                                <div className={`rounded-md px-3 py-2 ${guarantor.kyc_verified ? 'bg-emerald-50' : 'bg-red-50'}`}>
                                    <span className={`text-sm font-medium ${guarantor.kyc_verified ? 'text-emerald-800' : 'text-red-800'}`}>
                                        KYC: {guarantor.kyc_verified ? 'Verified' : 'Failed'}
                                    </span>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            ))}
        </div>
    )
}

// Step 3: Loan Details
function LoanDetailsStep({
    data,
    onChange,
}: {
    data: LoanDetails
    onChange: (data: LoanDetails) => void
}) {
    const addEquipment = () => {
        onChange({ ...data, equipment: [...data.equipment, { ...emptyEquipment }] })
    }

    const removeEquipment = (index: number) => {
        onChange({ ...data, equipment: data.equipment.filter((_, i) => i !== index) })
    }

    const updateEquipment = (index: number, field: keyof Equipment, value: any) => {
        const updated = [...data.equipment]
            ; (updated[index] as any)[field] = value
        onChange({ ...data, equipment: updated })
    }

    return (
        <div className="space-y-6">
            <h2 className="text-xl font-semibold text-slate-900">Loan Details</h2>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                    <label className="block text-sm font-medium text-slate-700">Type of Loan *</label>
                    <select
                        className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                        value={data.loan_type}
                        onChange={(e) => onChange({ ...data, loan_type: e.target.value as LoanDetails['loan_type'] })}
                    >
                        <option value="Equipment Finance">Equipment Finance</option>
                        <option value="Working Capital">Working Capital</option>
                        <option value="Refinance">Refinance</option>
                    </select>
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700">Loan Amount *</label>
                    <div className="relative mt-1">
                        <span className="absolute left-3 top-2 text-slate-500">$</span>
                        <input
                            type="text"
                            className="w-full rounded-md border border-slate-300 pl-7 pr-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                            value={data.amount}
                            onChange={(e) => onChange({ ...data, amount: e.target.value })}
                            placeholder="75,000"
                        />
                    </div>
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700">Down Payment</label>
                    <div className="relative mt-1">
                        <span className="absolute left-3 top-2 text-slate-500">$</span>
                        <input
                            type="text"
                            className="w-full rounded-md border border-slate-300 pl-7 pr-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                            value={data.down_payment}
                            onChange={(e) => onChange({ ...data, down_payment: e.target.value })}
                            placeholder="10,000"
                        />
                    </div>
                </div>
            </div>

            {data.loan_type === 'Equipment Finance' && (
                <div className="mt-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-medium text-slate-900">Equipment Details</h3>
                        <button
                            type="button"
                            onClick={addEquipment}
                            className="inline-flex items-center rounded-md bg-slate-100 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-200"
                        >
                            <svg className="mr-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                            </svg>
                            Add Equipment
                        </button>
                    </div>

                    {data.equipment.map((eq, idx) => (
                        <div key={idx} className="mb-4 rounded-lg border border-slate-200 bg-slate-50 p-4">
                            <div className="flex items-center justify-between mb-3">
                                <span className="text-sm font-medium text-slate-700">Equipment {idx + 1}</span>
                                {data.equipment.length > 1 && (
                                    <button
                                        type="button"
                                        onClick={() => removeEquipment(idx)}
                                        className="text-sm text-red-600 hover:text-red-800"
                                    >
                                        Remove
                                    </button>
                                )}
                            </div>
                            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                                <div>
                                    <label className="block text-xs font-medium text-slate-600">Type</label>
                                    <input
                                        type="text"
                                        className="mt-1 w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm focus:border-slate-500 focus:outline-none"
                                        value={eq.type}
                                        onChange={(e) => updateEquipment(idx, 'type', e.target.value)}
                                        placeholder="Truck, Trailer, etc."
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-slate-600">Make</label>
                                    <input
                                        type="text"
                                        className="mt-1 w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm focus:border-slate-500 focus:outline-none"
                                        value={eq.make}
                                        onChange={(e) => updateEquipment(idx, 'make', e.target.value)}
                                        placeholder="Freightliner"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-slate-600">Model</label>
                                    <input
                                        type="text"
                                        className="mt-1 w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm focus:border-slate-500 focus:outline-none"
                                        value={eq.model}
                                        onChange={(e) => updateEquipment(idx, 'model', e.target.value)}
                                        placeholder="Cascadia"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-slate-600">Year</label>
                                    <input
                                        type="text"
                                        className="mt-1 w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm focus:border-slate-500 focus:outline-none"
                                        value={eq.year}
                                        onChange={(e) => updateEquipment(idx, 'year', e.target.value)}
                                        placeholder="2020"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-slate-600">Mileage</label>
                                    <input
                                        type="text"
                                        className="mt-1 w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm focus:border-slate-500 focus:outline-none"
                                        value={eq.mileage}
                                        onChange={(e) => updateEquipment(idx, 'mileage', e.target.value)}
                                        placeholder="50,000"
                                    />
                                </div>
                                <div className="flex items-end gap-4">
                                    <label className="flex items-center gap-2 text-sm">
                                        <input
                                            type="checkbox"
                                            checked={eq.titled}
                                            onChange={(e) => updateEquipment(idx, 'titled', e.target.checked)}
                                            className="rounded border-slate-300"
                                        />
                                        Titled
                                    </label>
                                    <label className="flex items-center gap-2 text-sm">
                                        <input
                                            type="checkbox"
                                            checked={eq.private_party}
                                            onChange={(e) => updateEquipment(idx, 'private_party', e.target.checked)}
                                            className="rounded border-slate-300"
                                        />
                                        Private Party
                                    </label>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

// Step 4: Documents
function DocumentsStep({
    documents,
    onChange,
}: {
    documents: { type: string; uploaded: boolean }[]
    onChange: (docs: { type: string; uploaded: boolean }[]) => void
}) {
    const requiredDocs = [
        { type: 'drivers_license', label: "Driver's License" },
        { type: 'bank_statements', label: 'Bank Statements (3 months)' },
        { type: 'tax_returns', label: 'Business Tax Returns' },
        { type: 'equipment_invoice', label: 'Equipment Invoice/Bill of Sale' },
    ]

    const toggleUpload = (docType: string) => {
        const existing = documents.find(d => d.type === docType)
        if (existing) {
            onChange(documents.map(d => d.type === docType ? { ...d, uploaded: !d.uploaded } : d))
        } else {
            onChange([...documents, { type: docType, uploaded: true }])
        }
    }

    return (
        <div className="space-y-6">
            <h2 className="text-xl font-semibold text-slate-900">Additional Documents</h2>
            <p className="text-sm text-slate-600">
                Upload the required documents to complete your application. Additional documents may be requested.
            </p>

            <div className="space-y-3">
                {requiredDocs.map((doc) => {
                    const uploaded = documents.find(d => d.type === doc.type)?.uploaded || false
                    return (
                        <div
                            key={doc.type}
                            className={`flex items-center justify-between rounded-lg border p-4 ${uploaded ? 'border-emerald-300 bg-emerald-50' : 'border-slate-200 bg-white'
                                }`}
                        >
                            <div className="flex items-center gap-3">
                                {uploaded ? (
                                    <svg className="h-5 w-5 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                    </svg>
                                ) : (
                                    <svg className="h-5 w-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                    </svg>
                                )}
                                <span className={`text-sm font-medium ${uploaded ? 'text-emerald-800' : 'text-slate-700'}`}>
                                    {doc.label}
                                </span>
                            </div>
                            <button
                                type="button"
                                onClick={() => toggleUpload(doc.type)}
                                className={`rounded-md px-3 py-1.5 text-sm font-medium ${uploaded
                                    ? 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'
                                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                                    }`}
                            >
                                {uploaded ? 'Uploaded' : 'Upload'}
                            </button>
                        </div>
                    )
                })}
            </div>

            <div className="rounded-md bg-amber-50 p-4">
                <div className="flex">
                    <svg className="h-5 w-5 text-amber-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    <p className="ml-3 text-sm text-amber-700">
                        Note: In this demo, clicking "Upload" simulates a successful upload. In production, this would open a file picker.
                    </p>
                </div>
            </div>
        </div>
    )
}

// Step 5: Review & Sign
function ReviewSignStep({
    formData,
    termsAccepted,
    signature,
    onTermsChange,
    onSignatureChange,
    matchResults,
    matchLoading,
}: {
    formData: FormData
    termsAccepted: boolean
    signature: string
    onTermsChange: (accepted: boolean) => void
    onSignatureChange: (sig: string) => void
    matchResults: any[] | null
    matchLoading: boolean
}) {
    const eligibleMatches = matchResults?.filter((r: any) => r.eligible) || []
    const hasEligibleMatch = eligibleMatches.length > 0

    return (
        <div className="space-y-6">
            <h2 className="text-xl font-semibold text-slate-900">Review & Sign</h2>

            {/* Summary */}
            <div className="space-y-4">
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                    <h3 className="text-sm font-semibold text-slate-800 mb-2">Business Information</h3>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                        <div><span className="text-slate-500">Legal Name:</span> {formData.business.legal_name}</div>
                        <div><span className="text-slate-500">TIN:</span> {formData.business.tin}</div>
                        <div><span className="text-slate-500">Email:</span> {formData.business.email}</div>
                        <div><span className="text-slate-500">Phone:</span> {formData.business.phone}</div>
                        {formData.business.paynet_score && (
                            <div><span className="text-slate-500">PayNet Score:</span> {formData.business.paynet_score}</div>
                        )}
                    </div>
                </div>

                <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                    <h3 className="text-sm font-semibold text-slate-800 mb-2">Guarantors ({formData.guarantors.length})</h3>
                    {formData.guarantors.map((g, idx) => (
                        <div key={idx} className="text-sm mb-2">
                            <span className="font-medium">{g.first_name} {g.last_name}</span>
                            {g.is_primary && <span className="ml-2 text-xs bg-slate-200 px-1.5 py-0.5 rounded">Primary</span>}
                            {g.fico && <span className="ml-2 text-slate-500">FICO: {g.fico}</span>}
                            {g.kyc_verified && <span className="ml-2 text-emerald-600">KYC Verified</span>}
                        </div>
                    ))}
                </div>

                <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                    <h3 className="text-sm font-semibold text-slate-800 mb-2">Loan Details</h3>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                        <div><span className="text-slate-500">Type:</span> {formData.loan.loan_type}</div>
                        <div><span className="text-slate-500">Amount:</span> ${formData.loan.amount}</div>
                    </div>
                    {formData.loan.loan_type === 'Equipment Finance' && formData.loan.equipment.length > 0 && (
                        <div className="mt-2 text-sm">
                            <span className="text-slate-500">Equipment:</span>{' '}
                            {formData.loan.equipment.map((eq, idx) => (
                                <span key={idx}>{eq.year} {eq.make} {eq.model}{idx < formData.loan.equipment.length - 1 ? ', ' : ''}</span>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Match Results */}
            <div className="rounded-lg border border-slate-200 bg-white p-4">
                <h3 className="text-sm font-semibold text-slate-800 mb-3">Lender Match Results</h3>
                {matchLoading ? (
                    <div className="flex items-center justify-center py-6">
                        <svg className="h-6 w-6 animate-spin text-slate-500" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        <span className="ml-2 text-sm text-slate-500">Evaluating lender matches...</span>
                    </div>
                ) : matchResults && matchResults.length > 0 ? (
                    <div className="space-y-3">
                        {matchResults.map((r: any, idx: number) => (
                            <div key={r.lender_program_id || idx} className={`rounded-md border p-3 ${r.eligible ? 'border-emerald-200 bg-emerald-50' : 'border-slate-200 bg-slate-50'}`}>
                                <div className="flex items-center justify-between">
                                    <span className="font-medium text-slate-900">
                                        {r.lender_name || 'Lender'} - {r.program_name || 'Program'}
                                    </span>
                                    <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${r.eligible ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}`}>
                                        {r.eligible ? 'Eligible' : 'Not Eligible'}
                                    </span>
                                </div>
                                {r.eligible && (
                                    <div className="mt-1 flex gap-4 text-sm text-slate-600">
                                        {r.fit_score !== undefined && <span>Fit Score: {r.fit_score}%</span>}
                                        {r.assigned_term_months && <span>Term: {r.assigned_term_months} months</span>}
                                        {r.assigned_interest_rate && <span>Rate: {r.assigned_interest_rate}%</span>}
                                    </div>
                                )}
                                {r.reasons && !r.eligible && (
                                    <div className="mt-1 text-xs text-slate-500">{r.reasons}</div>
                                )}
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="text-sm text-slate-500">No match results available.</p>
                )}
            </div>

            {/* Not Eligible Message */}
            {!matchLoading && matchResults && !hasEligibleMatch && (
                <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
                    <svg className="mx-auto h-12 w-12 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <h3 className="mt-4 text-lg font-semibold text-red-800">We're Sorry</h3>
                    <p className="mt-2 text-sm text-red-700">
                        Unfortunately, we are unable to match your application with any of our lending partners at this time.
                        This may be due to specific eligibility criteria not being met.
                    </p>
                    <p className="mt-3 text-sm text-red-600">
                        Please review the match results above for details, or contact our support team for assistance.
                    </p>
                </div>
            )}

            {/* Terms - Only show if eligible */}
            {hasEligibleMatch && (
                <div className="rounded-lg border border-slate-200 bg-white p-4">
                    <h3 className="text-sm font-semibold text-slate-800 mb-3">Terms and Conditions</h3>
                    <div className="h-32 overflow-y-auto rounded border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600 mb-4">
                        <p className="mb-2">By submitting this application, I/we certify that:</p>
                        <ol className="list-decimal list-inside space-y-1">
                            <li>All information provided is true and accurate to the best of my/our knowledge.</li>
                            <li>I/we authorize the lender to obtain credit reports and verify all information.</li>
                            <li>I/we understand this is an application and not a commitment to lend.</li>
                            <li>I/we agree to the privacy policy and terms of service.</li>
                            <li>I/we consent to receive communications regarding this application.</li>
                        </ol>
                    </div>
                    <label className="flex items-center gap-2">
                        <input
                            type="checkbox"
                            checked={termsAccepted}
                            onChange={(e) => onTermsChange(e.target.checked)}
                            className="rounded border-slate-300"
                        />
                        <span className="text-sm text-slate-700">I have read and agree to the terms and conditions</span>
                    </label>
                </div>
            )}

            {/* Signature - Only show if eligible */}
            {hasEligibleMatch && (
                <div className="rounded-lg border border-slate-200 bg-white p-4">
                    <h3 className="text-sm font-semibold text-slate-800 mb-3">Electronic Signature</h3>
                    <div>
                        <label className="block text-sm font-medium text-slate-700">Type your full legal name to sign</label>
                        <input
                            type="text"
                            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                            value={signature}
                            onChange={(e) => onSignatureChange(e.target.value)}
                            placeholder="John Smith"
                        />
                    </div>
                    {signature && (
                        <div className="mt-3 rounded bg-slate-50 p-3">
                            <p className="text-xs text-slate-500">Electronic signature preview:</p>
                            <p className="mt-1 font-serif text-2xl italic text-slate-800">{signature}</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

// Step 6: Success
function SuccessStep({
    applicationId,
    matchResults,
}: {
    applicationId: string
    matchResults: any[] | null
}) {
    const eligibleMatches = matchResults?.filter((r: any) => r.eligible) || []

    return (
        <div className="space-y-6">
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-8 text-center">
                <svg className="mx-auto h-16 w-16 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <h2 className="mt-4 text-2xl font-semibold text-emerald-900">Application Submitted Successfully!</h2>
                <p className="mt-2 text-sm text-emerald-700">
                    Your loan application has been submitted and signed.
                </p>
                <p className="mt-1 text-sm text-emerald-600">
                    Application ID: <span className="font-mono font-semibold">{applicationId}</span>
                </p>
            </div>

            {eligibleMatches.length > 0 && (
                <div className="rounded-lg border border-slate-200 bg-white p-6">
                    <h3 className="text-lg font-semibold text-slate-900 mb-4">Matched Lender Programs</h3>
                    <div className="space-y-3">
                        {eligibleMatches.map((r: any, idx: number) => (
                            <div key={r.lender_program_id || idx} className="rounded-md border border-emerald-200 bg-emerald-50 p-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <span className="font-semibold text-slate-900">
                                            {r.lender_name || 'Lender'} - {r.program_name || 'Program'}
                                        </span>
                                        <div className="flex gap-3 mt-1">
                                            {r.fit_score !== undefined && (
                                                <span className="text-sm text-slate-600">Fit Score: {r.fit_score}%</span>
                                            )}
                                            {r.assigned_term_months && (
                                                <span className="text-sm font-medium text-emerald-700">Term: {r.assigned_term_months} months</span>
                                            )}
                                            {r.assigned_interest_rate && (
                                                <span className="text-sm font-medium text-emerald-700">Rate: {r.assigned_interest_rate}%</span>
                                            )}
                                        </div>
                                    </div>
                                    <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">
                                        Matched
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <div className="rounded-lg border border-slate-200 bg-slate-50 p-6">
                <h3 className="text-sm font-semibold text-slate-800 mb-2">What Happens Next?</h3>
                <ol className="list-decimal list-inside space-y-2 text-sm text-slate-600">
                    <li>Our underwriting team will review your application within 1-2 business days.</li>
                    <li>You may be contacted for additional documentation if needed.</li>
                    <li>Once approved, you'll receive loan terms and funding details via email.</li>
                    <li>Questions? Contact our support team at support@example.com</li>
                </ol>
            </div>
        </div>
    )
}

// Main Component
export function BorrowerPage() {
    const { applicationId: urlApplicationId } = useParams<{ applicationId: string }>()
    const [apiStatus, setApiStatus] = useState<string>('Checking API...')
    const [currentStep, setCurrentStep] = useState(1)
    const [formData, setFormData] = useState<FormData>(initialFormData)
    const [initialLoading, setInitialLoading] = useState(!!urlApplicationId)
    const [prefillLoading, setPrefillLoading] = useState(false)
    const [guarantorCheckLoading, setGuarantorCheckLoading] = useState<number | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [applicationId, setApplicationId] = useState<string | null>(null)
    const [matchStatus, setMatchStatus] = useState<any | null>(null)
    const [matchLoading, setMatchLoading] = useState(false)
    const [businessSearchResults, setBusinessSearchResults] = useState<BusinessSearchResult[]>([])

    useEffect(() => {
        health()
            .then(() => setApiStatus('API reachable'))
            .catch(() => setApiStatus('API not reachable'))
    }, [])

    // Load existing application data from URL parameter
    useEffect(() => {
        if (!urlApplicationId) return

        const loadApplication = async () => {
            setInitialLoading(true)
            try {
                const app = await getApplication(urlApplicationId)

                // Try to get additional data from prefill API using business name
                let prefillData: any = null
                let kybData: any = null

                if (app.business_name) {
                    try {
                        // Search for the business first
                        const searchRes = await businessSearch(app.business_name)
                        if (searchRes.status === 'success' && searchRes.results?.length > 0) {
                            // Use the first matching business
                            const businessId = searchRes.results[0].id

                            // Get prefill and KYB data in parallel
                            const [prefillRes, kybRes] = await Promise.all([
                                businessPrefill(businessId),
                                kybCheck(businessId),
                            ])

                            if (prefillRes.status === 'success') {
                                prefillData = prefillRes.data
                            }
                            kybData = kybRes
                        }
                    } catch (e) {
                        console.error('Prefill API error:', e)
                    }
                }

                // Restore current step if saved
                if (app.current_step && app.current_step > 1) {
                    setCurrentStep(app.current_step)
                }

                // Prefill form data from existing application + prefill API data
                setFormData(prev => ({
                    ...prev,
                    business: {
                        legal_name: app.business_name || '',
                        dba: prefillData?.dba || '',
                        address: prefillData?.address || { ...emptyAddress },
                        phone: prefillData?.phone || '',
                        email: app.merchant_email || prefillData?.email || '',
                        tin: prefillData?.tin || '',
                        paynet_score: kybData?.paynet_score || app.business_credit?.paynet_score,
                    },
                    guarantors: prefillData?.guarantors?.map((g: any, idx: number) => ({
                        first_name: g.first_name || '',
                        last_name: g.last_name || '',
                        title: g.title || '',
                        ownership_pct: g.ownership_pct || 0,
                        address: g.address || { ...emptyAddress },
                        phone: g.phone || '',
                        email: g.email || '',
                        ssn: '',
                        fico: undefined,
                        kyc_verified: undefined,
                        is_primary: idx === 0,
                    })) || app.guarantors?.map((g: any, idx: number) => ({
                        first_name: g.first_name || '',
                        last_name: g.last_name || '',
                        title: '',
                        ownership_pct: 0,
                        address: { ...emptyAddress },
                        phone: '',
                        email: '',
                        ssn: '',
                        fico: g.fico,
                        kyc_verified: undefined,
                        is_primary: g.is_primary || idx === 0,
                    })) || [],
                    loan: {
                        ...prev.loan,
                        loan_type: (app.loan_type as LoanDetails['loan_type']) || 'Equipment Finance',
                        amount: app.loan_request?.amount?.toString() || '',
                        term_months: app.loan_request?.term_months?.toString() || '',
                        down_payment: app.loan_request?.down_payment?.toString() || '',
                        equipment: app.equipment?.length > 0
                            ? app.equipment.map((eq: any) => ({
                                type: eq.type || '',
                                make: '',
                                model: '',
                                year: eq.year?.toString() || '',
                                mileage: eq.mileage?.toString() || '',
                                titled: eq.titled || false,
                                private_party: eq.private_party || false,
                            }))
                            : [{ ...emptyEquipment }],
                    },
                }))
            } catch (e: any) {
                console.error('Failed to load application:', e)
                setError('Failed to load application data')
            } finally {
                setInitialLoading(false)
            }
        }

        loadApplication()
    }, [urlApplicationId])

    // Handle business search
    const handleBusinessSearch = async (searchTerm: string) => {
        setPrefillLoading(true)
        try {
            const res = await businessSearch(searchTerm)
            if (res.status === 'success') {
                setBusinessSearchResults(res.results || [])
            }
        } catch (e: any) {
            console.error('Search error:', e)
            setBusinessSearchResults([])
        } finally {
            setPrefillLoading(false)
        }
    }

    // Handle business selection and prefill
    const handleSelectBusiness = async (businessId: string) => {
        setPrefillLoading(true)
        try {
            const [prefillRes, kybRes] = await Promise.all([
                businessPrefill(businessId),
                kybCheck(businessId),
            ])

            if (prefillRes.status === 'success' && prefillRes.data) {
                const data = prefillRes.data
                setFormData(prev => ({
                    ...prev,
                    business: {
                        legal_name: data.legal_name || prev.business.legal_name,
                        dba: data.dba || '',
                        address: data.address || prev.business.address,
                        phone: data.phone || '',
                        email: data.email || '',
                        tin: data.tin || '',
                        paynet_score: kybRes.paynet_score,
                    },
                    guarantors: data.guarantors?.map((g: any, idx: number) => ({
                        first_name: g.first_name || '',
                        last_name: g.last_name || '',
                        title: g.title || '',
                        ownership_pct: g.ownership_pct || 0,
                        address: g.address || { ...emptyAddress },
                        phone: g.phone || '',
                        email: g.email || '',
                        ssn: '',
                        is_primary: idx === 0,
                    })) || prev.guarantors,
                }))
            }
        } catch (e: any) {
            console.error('Prefill error:', e)
        } finally {
            setPrefillLoading(false)
        }
    }

    // Handle guarantor credit/KYC checks
    const handleGuarantorChecks = async (index: number) => {
        const guarantor = formData.guarantors[index]
        if (!guarantor.ssn) return

        setGuarantorCheckLoading(index)
        try {
            const [creditRes, kycRes] = await Promise.all([
                creditCheck(guarantor.ssn, guarantor.first_name, guarantor.last_name),
                kycCheck(guarantor.ssn, guarantor.first_name, guarantor.last_name,
                    `${guarantor.address.street}, ${guarantor.address.city}, ${guarantor.address.state} ${guarantor.address.zip}`),
            ])

            const updated = [...formData.guarantors]
            updated[index] = {
                ...updated[index],
                fico: creditRes.details?.fico || creditRes.score,
                kyc_verified: kycRes.verified,
            }
            setFormData(prev => ({ ...prev, guarantors: updated }))
        } catch (e: any) {
            console.error('Check error:', e)
        } finally {
            setGuarantorCheckLoading(null)
        }
    }

    // Trigger matching when entering step 5
    const triggerMatching = async () => {
        if (matchStatus?.results) return // Already have results

        setMatchLoading(true)
        try {
            // Submit application to get match results
            const body = {
                merchant_email: formData.business.email,
                business_name: formData.business.legal_name,
                loan_type: formData.loan.loan_type,
                guarantors: formData.guarantors.map(g => ({
                    is_primary: g.is_primary,
                    first_name: g.first_name,
                    last_name: g.last_name,
                    fico: g.fico,
                })),
                business_credit: formData.business.paynet_score ? {
                    paynet_score: formData.business.paynet_score,
                } : undefined,
                equipment: formData.loan.loan_type === 'Equipment Finance'
                    ? formData.loan.equipment.map(eq => ({
                        type: eq.type || formData.loan.loan_type,
                        year: eq.year ? Number(eq.year) : undefined,
                        mileage: eq.mileage ? Number(eq.mileage.replace(/[^0-9]/g, '')) : undefined,
                        titled: eq.titled,
                        private_party: eq.private_party,
                    }))
                    : [],
                loan_request: {
                    amount: formData.loan.amount ? Number(formData.loan.amount.replace(/[^0-9.]/g, '')) : undefined,
                    down_payment: formData.loan.down_payment ? Number(formData.loan.down_payment.replace(/[^0-9.]/g, '')) : undefined,
                },
            }
            const res = await createApplication(body)
            setApplicationId(res.id)

            // Fetch match results
            const matchRes = await latestMatch(res.id)
            setMatchStatus(matchRes)
        } catch (e: any) {
            console.error('Matching error:', e)
            setError('Failed to evaluate lender matches')
        } finally {
            setMatchLoading(false)
        }
    }

    const eligibleMatches = matchStatus?.results?.filter((r: any) => r.eligible) || []
    const hasEligibleMatch = eligibleMatches.length > 0

    const canProceed = () => {
        switch (currentStep) {
            case 1:
                return formData.business.legal_name && formData.business.tin && formData.business.email
            case 2:
                return formData.guarantors.length > 0 && formData.guarantors.every(g => g.first_name && g.last_name && g.ssn)
            case 3:
                return formData.loan.amount && formData.loan.loan_type
            case 4:
                return true
            case 5:
                // If not eligible, they can't proceed (no button shown anyway)
                // If eligible, need terms accepted and signature
                return hasEligibleMatch && formData.terms_accepted && formData.signature
            case 6:
                return false // Final step, no next
            default:
                return true
        }
    }

    // Save application progress after each step
    const saveApplicationProgress = async (nextStep: number) => {
        if (!applicationId) return

        try {
            const updateData: Record<string, unknown> = {
                current_step: nextStep,
            }

            // Save data based on which step we're leaving
            if (currentStep === 1) {
                updateData.business_name = formData.business.legal_name
                updateData.merchant_email = formData.business.email || 'applicant@example.com'
            } else if (currentStep === 2) {
                updateData.guarantors = formData.guarantors.map(g => ({
                    is_primary: g.is_primary,
                    first_name: g.first_name,
                    last_name: g.last_name,
                    fico: g.fico,
                }))
                updateData.business_credit = {
                    paynet_score: formData.business.paynet_score,
                }
            } else if (currentStep === 3) {
                updateData.loan_type = formData.loan.loan_type
                updateData.loan_request = {
                    amount: formData.loan.amount ? parseFloat(formData.loan.amount) : null,
                    down_payment: formData.loan.down_payment ? parseFloat(formData.loan.down_payment) : null,
                }
                updateData.equipment = formData.loan.equipment.map(e => ({
                    type: e.type,
                    year: e.year ? parseInt(e.year) : null,
                    mileage: e.mileage ? parseInt(e.mileage) : null,
                    titled: e.titled,
                    private_party: e.private_party,
                }))
            }

            await updateApplication(applicationId, updateData)
        } catch (e) {
            console.error('Failed to save application progress:', e)
            // Don't block navigation on save failure
        }
    }

    const handleNext = async () => {
        if (currentStep === 4) {
            // Moving to step 5, trigger matching
            await saveApplicationProgress(5)
            setCurrentStep(5)
            await triggerMatching()
        } else if (currentStep === 5 && hasEligibleMatch) {
            // Moving to success step
            await saveApplicationProgress(6)
            setCurrentStep(6)
        } else if (currentStep < 5) {
            await saveApplicationProgress(currentStep + 1)
            setCurrentStep(currentStep + 1)
        }
    }

    const handleBack = () => {
        if (currentStep > 1 && currentStep < 6) {
            setCurrentStep(currentStep - 1)
        }
    }

    // Show loading state while fetching existing application
    if (initialLoading) {
        return (
            <div className="mx-auto max-w-4xl">
                <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
                    <div className="flex items-center justify-center py-12">
                        <svg className="h-8 w-8 animate-spin text-slate-600" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        <span className="ml-3 text-slate-600">Loading application...</span>
                    </div>
                </div>
            </div>
        )
    }

    return (
        <div className="mx-auto max-w-4xl">
            <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex items-center justify-between mb-6">
                    <h1 className="text-2xl font-semibold text-slate-900">Loan Application</h1>
                    <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                        {apiStatus}
                    </span>
                </div>

                <Stepper currentStep={currentStep} steps={STEPS} />

                {error && (
                    <div className="mb-6 rounded-md bg-red-50 p-4 text-sm text-red-700">{error}</div>
                )}

                <div className="min-h-[400px]">
                    {currentStep === 1 && (
                        <BusinessInfoStep
                            data={formData.business}
                            onChange={(business) => setFormData(prev => ({ ...prev, business }))}
                            searchResults={businessSearchResults}
                            onSearch={handleBusinessSearch}
                            onSelectBusiness={handleSelectBusiness}
                            loading={prefillLoading}
                        />
                    )}
                    {currentStep === 2 && (
                        <GuarantorsStep
                            guarantors={formData.guarantors}
                            onChange={(guarantors) => setFormData(prev => ({ ...prev, guarantors }))}
                            onRunChecks={handleGuarantorChecks}
                            loading={guarantorCheckLoading}
                        />
                    )}
                    {currentStep === 3 && (
                        <LoanDetailsStep
                            data={formData.loan}
                            onChange={(loan) => setFormData(prev => ({ ...prev, loan }))}
                        />
                    )}
                    {currentStep === 4 && (
                        <DocumentsStep
                            documents={formData.documents}
                            onChange={(documents) => setFormData(prev => ({ ...prev, documents }))}
                        />
                    )}
                    {currentStep === 5 && (
                        <ReviewSignStep
                            formData={formData}
                            termsAccepted={formData.terms_accepted}
                            signature={formData.signature}
                            onTermsChange={(terms_accepted) => setFormData(prev => ({ ...prev, terms_accepted }))}
                            onSignatureChange={(signature) => setFormData(prev => ({ ...prev, signature }))}
                            matchResults={matchStatus?.results || null}
                            matchLoading={matchLoading}
                        />
                    )}
                    {currentStep === 6 && applicationId && (
                        <SuccessStep
                            applicationId={applicationId}
                            matchResults={matchStatus?.results || null}
                        />
                    )}
                </div>

                {/* Footer - hide on success step */}
                {currentStep < 6 && (
                    <div className="mt-8 flex items-center justify-between border-t border-slate-200 pt-6">
                        <button
                            type="button"
                            onClick={handleBack}
                            disabled={currentStep === 1}
                            className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                        >
                            Back
                        </button>
                        <div className="flex items-center gap-3">
                            <span className="text-sm text-slate-500">Step {currentStep} of {STEPS.length}</span>
                            {/* Show button based on step and eligibility */}
                            {currentStep === 5 && !matchLoading && !hasEligibleMatch ? (
                                <span className="text-sm text-slate-500">Unable to proceed - no eligible lenders</span>
                            ) : (
                                <button
                                    type="button"
                                    onClick={handleNext}
                                    disabled={!canProceed() || matchLoading}
                                    className="rounded-md bg-slate-900 px-6 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-50"
                                >
                                    {matchLoading ? 'Evaluating...' : currentStep === 5 ? 'Sign & Submit' : 'Continue'}
                                </button>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
