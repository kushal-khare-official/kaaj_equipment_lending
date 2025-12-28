import { useEffect, useState } from 'react'
import { listLenders, createLender, deleteLender, updateLender } from '../api'
import type { LenderProgramInput, LenderCriteriaInput } from '../api'

type LenderCriteria = {
    id: string
    field_key: string
    data_type: string
    operator: string
    value_min?: string
    value_max?: string
    values?: string[]
    pattern?: string
    description?: string
}

type LenderProgram = {
    id: string
    name: string
    description?: string
    criteria: LenderCriteria[]
}

type Lender = {
    id: string
    name: string
    programs: LenderProgram[]
}

const DATA_TYPES = ['int', 'decimal', 'string', 'bool']
const OPERATORS = ['range', 'in', 'not_in', 'contains', 'boolean']

function CriteriaForm({
    criteria,
    onChange,
    onRemove,
}: {
    criteria: LenderCriteriaInput
    onChange: (c: LenderCriteriaInput) => void
    onRemove: () => void
}) {
    return (
        <div className="border border-slate-200 rounded p-2 bg-slate-50 space-y-2">
            <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-600">Criterion</span>
                <button className="text-xs text-red-600" onClick={onRemove}>Remove</button>
            </div>
            <div className="grid grid-cols-2 gap-2">
                <input
                    className="text-xs border border-slate-300 rounded px-2 py-1"
                    placeholder="Field key (e.g., annual_revenue)"
                    value={criteria.field_key}
                    onChange={(e) => onChange({ ...criteria, field_key: e.target.value })}
                />
                <select
                    className="text-xs border border-slate-300 rounded px-2 py-1"
                    value={criteria.data_type}
                    onChange={(e) => onChange({ ...criteria, data_type: e.target.value })}
                >
                    {DATA_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
                <select
                    className="text-xs border border-slate-300 rounded px-2 py-1"
                    value={criteria.operator}
                    onChange={(e) => onChange({ ...criteria, operator: e.target.value })}
                >
                    {OPERATORS.map((o) => <option key={o} value={o}>{o}</option>)}
                </select>
                <input
                    className="text-xs border border-slate-300 rounded px-2 py-1"
                    placeholder="Description"
                    value={criteria.description || ''}
                    onChange={(e) => onChange({ ...criteria, description: e.target.value })}
                />
            </div>
            {criteria.operator === 'range' && (
                <div className="grid grid-cols-2 gap-2">
                    <input
                        className="text-xs border border-slate-300 rounded px-2 py-1"
                        placeholder="Min value"
                        value={criteria.value_min || ''}
                        onChange={(e) => onChange({ ...criteria, value_min: e.target.value })}
                    />
                    <input
                        className="text-xs border border-slate-300 rounded px-2 py-1"
                        placeholder="Max value"
                        value={criteria.value_max || ''}
                        onChange={(e) => onChange({ ...criteria, value_max: e.target.value })}
                    />
                </div>
            )}
            {(criteria.operator === 'in' || criteria.operator === 'not_in') && (
                <input
                    className="text-xs border border-slate-300 rounded px-2 py-1 w-full"
                    placeholder="Values (comma-separated)"
                    value={criteria.values?.join(', ') || ''}
                    onChange={(e) => onChange({ ...criteria, values: e.target.value.split(',').map(v => v.trim()).filter(Boolean) })}
                />
            )}
            {criteria.operator === 'contains' && (
                <input
                    className="text-xs border border-slate-300 rounded px-2 py-1 w-full"
                    placeholder="Pattern"
                    value={criteria.pattern || ''}
                    onChange={(e) => onChange({ ...criteria, pattern: e.target.value })}
                />
            )}
        </div>
    )
}

function ProgramForm({
    program,
    onChange,
    onRemove,
}: {
    program: LenderProgramInput
    onChange: (p: LenderProgramInput) => void
    onRemove: () => void
}) {
    const addCriteria = () => {
        onChange({
            ...program,
            criteria: [...program.criteria, { field_key: '', data_type: 'int', operator: 'range' }],
        })
    }

    const updateCriteria = (index: number, c: LenderCriteriaInput) => {
        const newCriteria = [...program.criteria]
        newCriteria[index] = c
        onChange({ ...program, criteria: newCriteria })
    }

    const removeCriteria = (index: number) => {
        onChange({ ...program, criteria: program.criteria.filter((_, i) => i !== index) })
    }

    return (
        <div className="border border-slate-300 rounded p-3 bg-white space-y-3">
            <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-700">Program</span>
                <button className="text-xs text-red-600" onClick={onRemove}>Remove Program</button>
            </div>
            <div className="space-y-2">
                <input
                    className="text-sm border border-slate-300 rounded px-2 py-1 w-full"
                    placeholder="Program name"
                    value={program.name}
                    onChange={(e) => onChange({ ...program, name: e.target.value })}
                />
                <input
                    className="text-xs border border-slate-300 rounded px-2 py-1 w-full"
                    placeholder="Description (optional)"
                    value={program.description || ''}
                    onChange={(e) => onChange({ ...program, description: e.target.value })}
                />
            </div>
            <div className="space-y-2">
                <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-slate-600">Criteria ({program.criteria.length})</span>
                    <button className="text-xs rounded bg-slate-200 px-2 py-1" onClick={addCriteria}>+ Add Criterion</button>
                </div>
                {program.criteria.map((c, i) => (
                    <CriteriaForm
                        key={i}
                        criteria={c}
                        onChange={(updated) => updateCriteria(i, updated)}
                        onRemove={() => removeCriteria(i)}
                    />
                ))}
            </div>
        </div>
    )
}

function LenderEditor({
    lender,
    onSave,
    onCancel,
    onDelete,
}: {
    lender: Lender | null
    onSave: (name: string, programs: LenderProgramInput[]) => void
    onCancel: () => void
    onDelete?: () => void
}) {
    const [name, setName] = useState(lender?.name || '')
    const [programs, setPrograms] = useState<LenderProgramInput[]>(
        lender?.programs.map((p) => ({
            name: p.name,
            description: p.description,
            criteria: p.criteria.map((c) => ({
                field_key: c.field_key,
                data_type: c.data_type,
                operator: c.operator,
                value_min: c.value_min,
                value_max: c.value_max,
                values: c.values,
                pattern: c.pattern,
                description: c.description,
            })),
        })) || []
    )

    const addProgram = () => {
        setPrograms([...programs, { name: '', criteria: [] }])
    }

    const updateProgram = (index: number, p: LenderProgramInput) => {
        const newPrograms = [...programs]
        newPrograms[index] = p
        setPrograms(newPrograms)
    }

    const removeProgram = (index: number) => {
        setPrograms(programs.filter((_, i) => i !== index))
    }

    return (
        <div className="border border-slate-300 rounded p-4 bg-slate-50 space-y-4">
            <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-slate-800">
                    {lender ? 'Edit Lender' : 'Create New Lender'}
                </span>
                <div className="flex gap-2">
                    {lender && onDelete && (
                        <button className="text-xs rounded bg-red-600 text-white px-3 py-1" onClick={onDelete}>
                            Delete
                        </button>
                    )}
                    <button className="text-xs rounded bg-slate-300 px-3 py-1" onClick={onCancel}>
                        Cancel
                    </button>
                    <button
                        className="text-xs rounded bg-slate-900 text-white px-3 py-1"
                        onClick={() => onSave(name, programs)}
                    >
                        Save
                    </button>
                </div>
            </div>

            <div>
                <label className="text-xs font-medium text-slate-600 block mb-1">Lender Name</label>
                <input
                    className="text-sm border border-slate-300 rounded px-2 py-1 w-full"
                    placeholder="Lender name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                />
            </div>

            <div className="space-y-3">
                <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-slate-600">Programs ({programs.length})</span>
                    <button className="text-xs rounded bg-blue-600 text-white px-2 py-1" onClick={addProgram}>
                        + Add Program
                    </button>
                </div>
                {programs.map((p, i) => (
                    <ProgramForm
                        key={i}
                        program={p}
                        onChange={(updated) => updateProgram(i, updated)}
                        onRemove={() => removeProgram(i)}
                    />
                ))}
            </div>
        </div>
    )
}

export function UnderwriterPage() {
    const [lenders, setLenders] = useState<Lender[]>([])
    const [uwError, setUwError] = useState<string | null>(null)
    const [editingLender, setEditingLender] = useState<Lender | null>(null)
    const [isCreating, setIsCreating] = useState(false)

    const load = () => {
        listLenders().then(setLenders).catch((e) => setUwError(e.message))
    }

    useEffect(() => {
        load()
    }, [])

    const handleCreate = async (name: string, programs: LenderProgramInput[]) => {
        try {
            await createLender({ name, programs })
            setIsCreating(false)
            setUwError(null)
            load()
        } catch (e: any) {
            setUwError(e.message)
        }
    }

    const handleUpdate = async (name: string, programs: LenderProgramInput[]) => {
        if (!editingLender) return
        try {
            await updateLender(editingLender.id, { name, programs })
            setEditingLender(null)
            setUwError(null)
            load()
        } catch (e: any) {
            setUwError(e.message)
        }
    }

    const handleDelete = async (lenderId: string) => {
        if (!confirm('Are you sure you want to delete this lender?')) return
        try {
            await deleteLender(lenderId)
            setEditingLender(null)
            setUwError(null)
            load()
        } catch (e: any) {
            setUwError(e.message)
        }
    }

    return (
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
                <div className="text-sm font-semibold text-slate-800">Underwriter Console - Lender Policy Management</div>
                <div className="flex gap-2">
                    <button className="text-xs rounded bg-slate-200 px-3 py-1" onClick={load}>
                        Refresh
                    </button>
                    {!isCreating && !editingLender && (
                        <button className="text-xs rounded bg-blue-600 text-white px-3 py-1" onClick={() => setIsCreating(true)}>
                            + New Lender
                        </button>
                    )}
                </div>
            </div>

            {uwError && <div className="text-sm text-red-600 mb-4">{uwError}</div>}

            {isCreating && (
                <div className="mb-4">
                    <LenderEditor
                        lender={null}
                        onSave={handleCreate}
                        onCancel={() => setIsCreating(false)}
                    />
                </div>
            )}

            {editingLender && (
                <div className="mb-4">
                    <LenderEditor
                        lender={editingLender}
                        onSave={handleUpdate}
                        onCancel={() => setEditingLender(null)}
                        onDelete={() => handleDelete(editingLender.id)}
                    />
                </div>
            )}

            <div className="space-y-3">
                {lenders.length === 0 ? (
                    <div className="text-sm text-slate-500">No lenders configured</div>
                ) : (
                    lenders.map((l) => (
                        <div
                            key={l.id}
                            className={`border rounded p-3 ${editingLender?.id === l.id ? 'border-blue-500 bg-blue-50' : 'border-slate-200'}`}
                        >
                            <div className="flex items-center justify-between">
                                <div>
                                    <div className="text-sm font-semibold text-slate-800">{l.name}</div>
                                    <div className="text-xs text-slate-500">
                                        {l.programs.length} program{l.programs.length !== 1 ? 's' : ''}
                                    </div>
                                </div>
                                <div className="flex gap-2">
                                    <button
                                        className="text-xs rounded bg-slate-100 px-2 py-1"
                                        onClick={() => setEditingLender(l)}
                                        disabled={isCreating || !!editingLender}
                                    >
                                        Edit
                                    </button>
                                    <button
                                        className="text-xs rounded bg-red-100 text-red-700 px-2 py-1"
                                        onClick={() => handleDelete(l.id)}
                                        disabled={isCreating || !!editingLender}
                                    >
                                        Delete
                                    </button>
                                </div>
                            </div>
                            {l.programs.length > 0 && (
                                <div className="mt-2 space-y-1">
                                    {l.programs.map((p) => (
                                        <div key={p.id} className="text-xs text-slate-600 bg-slate-50 rounded px-2 py-1">
                                            <span className="font-medium">{p.name}</span>
                                            {p.description && <span className="text-slate-400"> - {p.description}</span>}
                                            <span className="text-slate-400 ml-2">({p.criteria.length} criteria)</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    ))
                )}
            </div>
        </div>
    )
}
