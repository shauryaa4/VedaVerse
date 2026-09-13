import { useState, useMemo } from 'react'
import type {
  Session,
  ProtectionTarget,
  IntendedUse,
  ClassicalBasis,
  Novelty,
  IngredientSource,
  DevelopmentStatus,
  Objective,
  Composition,
} from '../types'
import { ProgressBar } from '../components/ProgressBar'
import { Button } from '../components/Button'
import { UNIT_OPTIONS } from '../data/ingredients'
import autocompleteData from '../data/ingredient_autocomplete_index.json'

interface QuestionnaireProps {
  session: Session
  onUpdate: (patch: Partial<Session>) => void
  onComplete: () => void
  onBack: () => void
}

interface QuestionDef {
  id: string
  title: string
  hint?: string
}

export function Questionnaire({ session, onUpdate, onComplete, onBack }: QuestionnaireProps) {
  const pt = session.protection_target

  const questions: QuestionDef[] = [
    { id: 'protection_target', title: 'What are you trying to protect?', hint: 'Select one option.' },
  ]

  if (pt === 'formulation' || pt === 'biological_resource' || pt === 'unsure') {
    questions.push({ id: 'composition', title: 'What is the composition of your product?', hint: 'Add each ingredient with its quantity, unit, and whether it is an active ingredient.' })
  }

  if (pt === 'formulation') {
    questions.push({ id: 'intended_use', title: 'What is the intended use of your product?', hint: 'Select one option.' })
    questions.push({ id: 'classical_basis', title: 'Is your formulation based on a classical or existing Ayurvedic formulation?', hint: 'If yes, you can name the reference text.' })
  }

  if (pt === 'formulation' && session.product.classical_basis !== 'yes') {
    questions.push({ id: 'novelty', title: 'Is the formulation new, modified, or existing?', hint: 'Select one option.' })
  }

  if (pt === 'formulation' || pt === 'biological_resource') {
    questions.push({ id: 'ingredient_sources', title: 'What are the sources of your ingredients?', hint: 'Select all that apply.' })
  }

  questions.push({ id: 'development_status', title: 'What is the development status of your product?', hint: 'Select one option.' })
  questions.push({ id: 'objective', title: 'What do you want to know?', hint: 'Select all that apply — these guide your query later.' })

  const [step, setStep] = useState(0)
  const total = questions.length
  const current = questions[step]

  const isStepValid = useMemo(() => {
    switch (current.id) {
      case 'protection_target':
        return session.protection_target !== null
      case 'composition':
        return isCompositionValid(session.product.composition)
      case 'intended_use':
        return session.product.intended_use !== null
      case 'classical_basis':
        return session.product.classical_basis !== null
      case 'novelty':
        return session.product.novelty !== null
      case 'ingredient_sources':
        return session.product.ingredient_sources.length > 0
      case 'development_status':
        return session.product.development_status !== null
      case 'objective':
        return session.objective.length > 0
      default:
        return true
    }
  }, [current.id, session])

  const goNext = () => {
    if (!isStepValid) return
    if (step < total - 1) setStep(step + 1)
    else onComplete()
  }

  const goBack = () => {
    if (step > 0) setStep(step - 1)
    else onBack()
  }

  return (
    <div className="fade-in">
      <ProgressBar current={step + 1} total={total} />
      <div className="card card-padded">
        <h2 className="question-title">{current.title}</h2>
        {current.hint && <p className="question-hint">{current.hint}</p>}

        {current.id === 'protection_target' && (
          <ProtectionTargetQ value={pt} onChange={(v) => onUpdate({ protection_target: v })} />
        )}
        {current.id === 'composition' && (
          <CompositionQ
            value={session.product.composition}
            onChange={(v) => onUpdate({ product: { ...session.product, composition: v } })}
          />
        )}
        {current.id === 'intended_use' && (
          <SingleSelectQ
            options={[
              { value: 'therapeutic', label: 'Therapeutic', desc: 'Treating or preventing disease' },
              { value: 'food_supplement', label: 'Food supplement', desc: 'Dietary/nutritional support' },
              { value: 'cosmetic', label: 'Cosmetic', desc: 'External application for beauty/care' },
              { value: 'agricultural', label: 'Agricultural', desc: 'Plant or crop-related use' },
              { value: 'research', label: 'Research', desc: 'Experimental or academic use' },
              { value: 'other', label: 'Other', desc: 'Something else' },
            ]}
            value={session.product.intended_use}
            onChange={(v) => onUpdate({ product: { ...session.product, intended_use: v as IntendedUse } })}
          />
        )}
        {current.id === 'classical_basis' && (
          <ClassicalBasisQ
            value={session.product.classical_basis}
            reference={session.product.classical_reference}
            onChange={(v) => onUpdate({ product: { ...session.product, classical_basis: v } })}
            onRefChange={(v) => onUpdate({ product: { ...session.product, classical_reference: v } })}
          />
        )}
        {current.id === 'novelty' && (
          <SingleSelectQ
            options={[
              { value: 'existing', label: 'Existing', desc: 'Already known and described in texts' },
              { value: 'modified', label: 'Modified', desc: 'Variation of a known formulation' },
              { value: 'new_combination', label: 'New combination', desc: 'Novel combination of known ingredients' },
              { value: 'unknown', label: 'Not sure', desc: 'Uncertain about novelty' },
            ]}
            value={session.product.novelty}
            onChange={(v) => onUpdate({ product: { ...session.product, novelty: v as Novelty } })}
          />
        )}
        {current.id === 'ingredient_sources' && (
          <IngredientSourcesQ
            value={session.product.ingredient_sources}
            geoKnown={session.product.biological_origin_known}
            geoRegion={session.product.biological_origin_region}
            onChange={(v) => onUpdate({ product: { ...session.product, ingredient_sources: v } })}
            onGeoKnownChange={(v) => onUpdate({ product: { ...session.product, biological_origin_known: v } })}
            onGeoRegionChange={(v) => onUpdate({ product: { ...session.product, biological_origin_region: v } })}
          />
        )}
        {current.id === 'development_status' && (
          <SingleSelectQ
            options={[
              { value: 'concept', label: 'Concept', desc: 'Idea stage, no prototype yet' },
              { value: 'prototype', label: 'Prototype', desc: 'Initial formulation prepared' },
              { value: 'developed', label: 'Developed', desc: 'Finalized and tested' },
              { value: 'marketed', label: 'Marketed', desc: 'Currently sold or distributed' },
              { value: 'filed_ip', label: 'Filed IP', desc: 'IP application submitted' },
            ]}
            value={session.product.development_status}
            onChange={(v) => onUpdate({ product: { ...session.product, development_status: v as DevelopmentStatus } })}
          />
        )}
        {current.id === 'objective' && (
          <MultiSelectQ
            options={[
              { value: 'patentability', label: 'Patentability' },
              { value: 'regulatory_category', label: 'Regulatory category' },
              { value: 'trademark', label: 'Trademark' },
              { value: 'prior_art', label: 'Prior art' },
              { value: 'abs_relevance', label: 'ABS relevance' },
              { value: 'legal_pathway', label: 'Legal pathway' },
              { value: 'general', label: 'General' },
            ]}
            value={session.objective}
            onChange={(v) => onUpdate({ objective: v as Objective[] })}
          />
        )}

        {!isStepValid && (
          <div className="validation-warning">
            {current.id === 'composition'
              ? 'Add at least one ingredient with a name, valid quantity, and unit to continue.'
              : 'Please select an option to continue.'}
          </div>
        )}

        <div className="nav-row">
          <Button variant="ghost" onClick={goBack}>Back</Button>
          <Button variant="primary" onClick={goNext} disabled={!isStepValid}>
            {step < total - 1 ? 'Continue' : 'See Classification'}
          </Button>
        </div>
      </div>
    </div>
  )
}

// --- Validation helpers ---

function isQuantityValid(q: string): boolean {
  if (q === '') return false
  return /^\d*\.?\d+$/.test(q) && parseFloat(q) > 0
}

function isCompositionValid(rows: Composition[]): boolean {
  const filled = rows.filter((r) => r.ingredient.trim() !== '' || r.quantity !== '' || r.unit !== '')
  if (filled.length === 0) return false
  return filled.every((r) => r.ingredient.trim() !== '' && isQuantityValid(r.quantity) && r.unit !== '')
}

// --- Sub-components ---

interface Opt { value: string; label: string; desc?: string }

function SingleSelectQ({ options, value, onChange }: { options: Opt[]; value: string | null; onChange: (v: string) => void }) {
  return (
    <div>
      {options.map((o) => (
        <div key={o.value} className={`option-card ${value === o.value ? 'selected' : ''}`} onClick={() => onChange(o.value)}>
          <div className="option-radio" />
          <div>
            <div className="option-label">{o.label}</div>
            {o.desc && <div className="option-desc">{o.desc}</div>}
          </div>
        </div>
      ))}
    </div>
  )
}

function MultiSelectQ({ options, value, onChange }: { options: Opt[]; value: string[]; onChange: (v: string[]) => void }) {
  const toggle = (v: string) => {
    if (value.includes(v)) onChange(value.filter((x) => x !== v))
    else onChange([...value, v])
  }
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
      {options.map((o) => (
        <div key={o.value} className={`chip ${value.includes(o.value) ? 'active' : ''}`} onClick={() => toggle(o.value)}>
          {o.label}
        </div>
      ))}
    </div>
  )
}

function ProtectionTargetQ({ value, onChange }: { value: ProtectionTarget | null; onChange: (v: ProtectionTarget) => void }) {
  return (
    <SingleSelectQ
      options={[
        { value: 'formulation', label: 'Formulation', desc: 'A specific product composition' },
        { value: 'brand', label: 'Brand / Logo', desc: 'A name, logo, or trademark' },
        { value: 'process', label: 'Process', desc: 'A manufacturing or extraction method' },
        { value: 'biological_resource', label: 'Biological resource', desc: 'A plant, animal, or microbial material' },
        { value: 'traditional_knowledge', label: 'Traditional knowledge', desc: 'Community-held knowledge' },
        { value: 'unsure', label: 'Not sure', desc: 'Help me figure it out' },
      ]}
      value={value}
      onChange={(v) => onChange(v as ProtectionTarget)}
    />
  )
}

function CompositionQ({ value, onChange }: { value: Composition[]; onChange: (v: Composition[]) => void }) {
  const [browseRowIdx, setBrowseRowIdx] = useState<number | null>(null)
  const addRow = () => onChange([...value, { ingredient: '', quantity: '', unit: '', is_active: false }])
  const removeRow = (i: number) => onChange(value.filter((_, idx) => idx !== i))
  const updateRow = (i: number, patch: Partial<Composition>) => onChange(value.map((r, idx) => idx === i ? { ...r, ...patch } : r))

  return (
    <div>
      <div className="composition-header">
        <div>Ingredient</div><div>Qty</div><div>Unit</div><div>Active</div><div></div>
      </div>
      {value.map((row, i) => (
        <CompositionRow
          key={i}
          row={row}
          onUpdate={(patch) => updateRow(i, patch)}
          onRemove={() => removeRow(i)}
          onBrowse={() => setBrowseRowIdx(i)}
        />
      ))}
      <div className="composition-actions">
        <button className="composition-add" onClick={addRow}>+ Add ingredient</button>
        <button className="composition-browse-btn" onClick={() => setBrowseRowIdx(value.length - 1)}>Browse all ingredients</button>
      </div>
      {browseRowIdx !== null && (
        <IngredientBrowseModal
          onSelect={(name) => {
            updateRow(browseRowIdx, { ingredient: name })
            setBrowseRowIdx(null)
          }}
          onClose={() => setBrowseRowIdx(null)}
        />
      )}
    </div>
  )
}

interface AutocompleteEntry {
  name: string
  scientific_name: string
  traditional_name: string
  source_category: string
}

function CompositionRow({ row, onUpdate, onRemove, onBrowse }: { row: Composition; onUpdate: (patch: Partial<Composition>) => void; onRemove: () => void; onBrowse: () => void }) {
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [activeIdx, setActiveIdx] = useState(-1)

  const suggestions = useMemo(() => {
    const q = row.ingredient.toLowerCase().trim()
    if (!q) return (autocompleteData as AutocompleteEntry[]).slice(0, 8)
    return (autocompleteData as AutocompleteEntry[]).filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        s.scientific_name.toLowerCase().includes(q) ||
        s.traditional_name.toLowerCase().includes(q)
    )
  }, [row.ingredient])

  const selectSuggestion = (name: string) => {
    onUpdate({ ingredient: name })
    setShowSuggestions(false)
    setActiveIdx(-1)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showSuggestions || suggestions.length === 0) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActiveIdx((p) => Math.min(p + 1, suggestions.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIdx((p) => Math.max(p - 1, 0))
    } else if (e.key === 'Enter' && activeIdx >= 0) {
      e.preventDefault()
      selectSuggestion(suggestions[activeIdx].name)
    } else if (e.key === 'Escape') {
      setShowSuggestions(false)
      setActiveIdx(-1)
    }
  }

  const qtyValid = row.quantity === '' || isQuantityValid(row.quantity)
  const showQtyError = row.quantity !== '' && !qtyValid

  return (
    <div className="composition-row">
      <div className="autocomplete-wrap">
        <input
          className="input"
          placeholder="e.g. Ashwagandha"
          value={row.ingredient}
          onChange={(e) => { onUpdate({ ingredient: e.target.value }); setShowSuggestions(true); setActiveIdx(-1) }}
          onFocus={() => setShowSuggestions(true)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
          onKeyDown={handleKeyDown}
        />
        <button type="button" className="autocomplete-browse-btn" onClick={onBrowse} aria-label="Browse all ingredients" title="Browse all ingredients">&#9776;</button>
        {showSuggestions && suggestions.length > 0 && (
          <div className="autocomplete-list">
            {suggestions.slice(0, 6).map((s, idx) => (
              <div
                key={s.name}
                className={`autocomplete-item ${idx === activeIdx ? 'active-suggestion' : ''}`}
                onMouseDown={() => selectSuggestion(s.name)}
              >
                <div className="autocomplete-name">{s.name}</div>
                <div className="autocomplete-sci">{s.scientific_name}{s.traditional_name ? ` — ${s.traditional_name}` : ''}</div>
              </div>
            ))}
          </div>
        )}
      </div>
      <div>
        <input
          className={`input ${showQtyError ? 'input-error' : ''}`}
          placeholder="500"
          value={row.quantity}
          onChange={(e) => onUpdate({ quantity: e.target.value })}
          inputMode="decimal"
        />
        {showQtyError && <div className="field-error">Enter a valid number</div>}
      </div>
      <select
        className="unit-select"
        value={row.unit}
        onChange={(e) => onUpdate({ unit: e.target.value })}
      >
        <option value="" disabled>—</option>
        {UNIT_OPTIONS.map((u) => (
          <option key={u} value={u}>{u}</option>
        ))}
      </select>
      <div className="composition-check">
        <input type="checkbox" checked={row.is_active} onChange={(e) => onUpdate({ is_active: e.target.checked })} />
      </div>
      <button className="composition-remove" onClick={onRemove} aria-label="Remove">&times;</button>
    </div>
  )
}

function IngredientBrowseModal({ onSelect, onClose }: { onSelect: (name: string) => void; onClose: () => void }) {
  const grouped = useMemo(() => {
    const sorted = [...(autocompleteData as AutocompleteEntry[])].sort((a, b) =>
      a.name.localeCompare(b.name, undefined, { sensitivity: 'base' })
    )
    const map: Record<string, AutocompleteEntry[]> = {}
    for (const entry of sorted) {
      const letter = entry.name[0].toUpperCase()
      if (!map[letter]) map[letter] = []
      map[letter].push(entry)
    }
    return Object.entries(map).sort(([a], [b]) => a.localeCompare(b))
  }, [])

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal ingredient-browse-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">Browse All Ingredients</div>
          <button className="modal-close" onClick={onClose} aria-label="Close">&times;</button>
        </div>
        <div className="modal-body ingredient-browse-body">
          {grouped.map(([letter, entries]) => (
            <div key={letter} className="ingredient-group">
              <div className="ingredient-group-header">{letter}</div>
              {entries.map((entry) => (
                <div
                  key={entry.name}
                  className="ingredient-browse-item"
                  onClick={() => onSelect(entry.name)}
                >
                  <div className="autocomplete-name">{entry.name}</div>
                  <div className="autocomplete-sci">
                    {entry.scientific_name}{entry.source_category ? ` · ${entry.source_category}` : ''}
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function ClassicalBasisQ({
  value, reference, onChange, onRefChange,
}: {
  value: ClassicalBasis | null
  reference: string
  onChange: (v: ClassicalBasis) => void
  onRefChange: (v: string) => void
}) {
  return (
    <div>
      <SingleSelectQ
        options={[
          { value: 'yes', label: 'Yes', desc: 'Based on a known classical formulation' },
          { value: 'no', label: 'No', desc: 'Not based on any classical text' },
          { value: 'partial', label: 'Partially', desc: 'Loosely based on a classical reference' },
          { value: 'unknown', label: "Don't know", desc: 'Not sure about the classical basis' },
        ]}
        value={value}
        onChange={(v) => onChange(v as ClassicalBasis)}
      />
      {value === 'yes' && (
        <div style={{ marginTop: '16px' }}>
          <label style={{ fontSize: '14px', fontWeight: 500, color: 'var(--c-text-secondary)', display: 'block', marginBottom: '6px' }}>
            Reference name (optional)
          </label>
          <input className="input" placeholder="e.g. Charaka Samhita, Ch. 12" value={reference} onChange={(e) => onRefChange(e.target.value)} />
        </div>
      )}
    </div>
  )
}

function IngredientSourcesQ({
  value, geoKnown, geoRegion, onChange, onGeoKnownChange, onGeoRegionChange,
}: {
  value: IngredientSource[]
  geoKnown: boolean | null
  geoRegion: string
  onChange: (v: IngredientSource[]) => void
  onGeoKnownChange: (v: boolean) => void
  onGeoRegionChange: (v: string) => void
}) {
  const toggle = (v: IngredientSource) => {
    if (value.includes(v)) onChange(value.filter((x) => x !== v))
    else onChange([...value, v])
  }
  const showGeo = value.includes('plant') || value.includes('animal')

  return (
    <div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
        {(['plant', 'animal', 'mineral', 'microbial', 'synthetic'] as IngredientSource[]).map((s) => (
          <div key={s} className={`chip ${value.includes(s) ? 'active' : ''}`} onClick={() => toggle(s)}>
            {s.charAt(0).toUpperCase() + s.slice(1)}
          </div>
        ))}
      </div>
      {showGeo && (
        <div style={{ marginTop: '16px' }}>
          <label style={{ fontSize: '14px', fontWeight: 500, color: 'var(--c-text-secondary)', display: 'block', marginBottom: '8px' }}>
            Do you know the geographic origin of the plant/animal source?
          </label>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
            <div className={`chip ${geoKnown === true ? 'active' : ''}`} onClick={() => onGeoKnownChange(true)}>Yes</div>
            <div className={`chip ${geoKnown === false ? 'active' : ''}`} onClick={() => onGeoKnownChange(false)}>No</div>
          </div>
          {geoKnown === true && (
            <input className="input" placeholder="e.g. Western Ghats, India" value={geoRegion} onChange={(e) => onGeoRegionChange(e.target.value)} />
          )}
        </div>
      )}
    </div>
  )
}
