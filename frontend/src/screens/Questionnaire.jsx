import { useState } from 'react';
import CompositionRow, { CommonIngredientsDatalist } from './CompositionRow.jsx';
import {
  PROTECTION_TARGET_OPTIONS,
  INTENDED_USE_OPTIONS,
  CLASSICAL_BASIS_OPTIONS,
  NOVELTY_OPTIONS,
  INGREDIENT_SOURCE_OPTIONS,
  DEVELOPMENT_STATUS_OPTIONS,
  OBJECTIVE_OPTIONS,
} from '../data/options.js';
import './Questionnaire.css';

let rowIdCounter = 0;
const newRow = () => ({
  id: `row-${rowIdCounter++}`,
  ingredient: '',
  quantity: '',
  unit: '',
  is_active: false,
});

/**
 * FE-03/04. Client-side progressive disclosure only (backend's intake_gating
 * / PIP-04 isn't built yet per the repo notes — this screen just chooses
 * not to send fields for questions it never showed, which the /intake
 * endpoint's own docstring says is a valid way to handle gating from this
 * side). Section numbers in comments below refer to build spec §3.
 */
export default function Questionnaire({ onSubmit, loading, error }) {
  const [productName, setProductName] = useState('');
  const [protectionTarget, setProtectionTarget] = useState('');
  const [composition, setComposition] = useState([newRow()]);
  const [intendedUse, setIntendedUse] = useState('');
  const [classicalBasis, setClassicalBasis] = useState('');
  const [classicalReference, setClassicalReference] = useState('');
  const [novelty, setNovelty] = useState('');
  const [ingredientSources, setIngredientSources] = useState([]);
  const [originKnown, setOriginKnown] = useState('');
  const [originRegion, setOriginRegion] = useState('');
  const [developmentStatus, setDevelopmentStatus] = useState('');
  const [objectives, setObjectives] = useState([]);
  const [formError, setFormError] = useState(null);

  const needsComposition =
    protectionTarget === 'formulation' ||
    protectionTarget === 'biological_resource' ||
    protectionTarget === 'unsure';
  const needsFormulationDetail = protectionTarget === 'formulation';
  const showNovelty = !(classicalBasis === 'yes' && classicalReference.trim());
  const needsSourceDetail =
    protectionTarget === 'formulation' || protectionTarget === 'biological_resource';
  const showOriginQuestion =
    needsSourceDetail && (ingredientSources.includes('plant') || ingredientSources.includes('animal'));

  const toggleInList = (list, setList, value) => {
    setList(list.includes(value) ? list.filter((v) => v !== value) : [...list, value]);
  };

  const updateRow = (id, updated) =>
    setComposition((rows) => rows.map((r) => (r.id === id ? updated : r)));
  const removeRow = (id) => setComposition((rows) => rows.filter((r) => r.id !== id));
  const addRow = () => setComposition((rows) => [...rows, newRow()]);

  const handleSubmit = (e) => {
    e.preventDefault();
    setFormError(null);

    if (!protectionTarget) {
      setFormError('Please tell us what you\u2019re trying to protect.');
      return;
    }
    if (objectives.length === 0) {
      setFormError('Please select at least one thing you want to know.');
      return;
    }

    const fields = {
      protection_target: protectionTarget,
      objective: objectives,
      development_status: developmentStatus || undefined,
    };

    if (productName.trim()) fields.product_name = productName.trim();

    if (needsComposition) {
      const cleanRows = composition
        .filter((r) => r.ingredient.trim())
        .map((r) => ({
          ingredient: r.ingredient.trim(),
          quantity: r.quantity.trim() || null,
          unit: r.unit.trim() || null,
          is_active: r.is_active,
        }));
      if (cleanRows.length > 0) fields.composition = cleanRows;
    }

    if (needsFormulationDetail) {
      if (intendedUse) fields.intended_use = intendedUse;
      if (classicalBasis) fields.classical_basis = classicalBasis;
      if (classicalBasis === 'yes' && classicalReference.trim()) {
        fields.classical_reference = classicalReference.trim();
      }
      if (showNovelty && novelty) fields.novelty = novelty;
    }

    if (needsSourceDetail) {
      if (ingredientSources.length > 0) fields.ingredient_sources = ingredientSources;
      if (showOriginQuestion && originKnown) {
        fields.biological_origin_known = originKnown;
        if (originKnown === 'yes' && originRegion.trim()) {
          fields.biological_origin_region = originRegion.trim();
        }
      }
    }

    onSubmit(fields);
  };

  return (
    <form className="questionnaire" onSubmit={handleSubmit}>
      <CommonIngredientsDatalist />

      <h2 className="questionnaire__title">Tell us about your product</h2>
      <p className="questionnaire__subtitle">
        Only the questions relevant to your answers will appear. Nothing here is stored
        beyond this session.
      </p>

      <div className="questionnaire__field">
        <label>Product name (optional)</label>
        <input
          type="text"
          value={productName}
          onChange={(e) => setProductName(e.target.value)}
          placeholder="e.g. Ashwagandha-Shatavari Rasayana"
        />
      </div>

      <div className="questionnaire__field">
        <label>What are you trying to protect?</label>
        <div className="questionnaire__options-grid">
          {PROTECTION_TARGET_OPTIONS.map((opt) => (
            <label key={opt.value} className="questionnaire__radio">
              <input
                type="radio"
                name="protection_target"
                value={opt.value}
                checked={protectionTarget === opt.value}
                onChange={() => setProtectionTarget(opt.value)}
              />
              {opt.label}
            </label>
          ))}
        </div>
      </div>

      {needsComposition && (
        <div className="questionnaire__field">
          <label>Composition</label>
          <div className="questionnaire__composition">
            {composition.map((row) => (
              <CompositionRow
                key={row.id}
                row={row}
                onChange={(updated) => updateRow(row.id, updated)}
                onRemove={() => removeRow(row.id)}
                canRemove={composition.length > 1}
              />
            ))}
            <button type="button" className="questionnaire__add-row" onClick={addRow}>
              + Add ingredient
            </button>
          </div>
        </div>
      )}

      {needsFormulationDetail && (
        <div className="questionnaire__field">
          <label>Intended use</label>
          <div className="questionnaire__options-grid">
            {INTENDED_USE_OPTIONS.map((opt) => (
              <label key={opt.value} className="questionnaire__radio">
                <input
                  type="radio"
                  name="intended_use"
                  value={opt.value}
                  checked={intendedUse === opt.value}
                  onChange={() => setIntendedUse(opt.value)}
                />
                {opt.label}
              </label>
            ))}
          </div>
        </div>
      )}

      {needsFormulationDetail && (
        <div className="questionnaire__field">
          <label>Is it based on a classical/existing Ayurvedic formulation?</label>
          <div className="questionnaire__options-grid">
            {CLASSICAL_BASIS_OPTIONS.map((opt) => (
              <label key={opt.value} className="questionnaire__radio">
                <input
                  type="radio"
                  name="classical_basis"
                  value={opt.value}
                  checked={classicalBasis === opt.value}
                  onChange={() => setClassicalBasis(opt.value)}
                />
                {opt.label}
              </label>
            ))}
          </div>
          {classicalBasis === 'yes' && (
            <input
              type="text"
              className="questionnaire__followup"
              placeholder="Name of the classical formulation (optional)"
              value={classicalReference}
              onChange={(e) => setClassicalReference(e.target.value)}
            />
          )}
        </div>
      )}

      {needsFormulationDetail && showNovelty && (
        <div className="questionnaire__field">
          <label>Is the formulation new, modified, or existing?</label>
          <div className="questionnaire__options-grid">
            {NOVELTY_OPTIONS.map((opt) => (
              <label key={opt.value} className="questionnaire__radio">
                <input
                  type="radio"
                  name="novelty"
                  value={opt.value}
                  checked={novelty === opt.value}
                  onChange={() => setNovelty(opt.value)}
                />
                {opt.label}
              </label>
            ))}
          </div>
        </div>
      )}

      {needsSourceDetail && (
        <div className="questionnaire__field">
          <label>Source of ingredients (select all that apply)</label>
          <div className="questionnaire__options-grid">
            {INGREDIENT_SOURCE_OPTIONS.map((opt) => (
              <label key={opt.value} className="questionnaire__checkbox">
                <input
                  type="checkbox"
                  checked={ingredientSources.includes(opt.value)}
                  onChange={() => toggleInList(ingredientSources, setIngredientSources, opt.value)}
                />
                {opt.label}
              </label>
            ))}
          </div>
        </div>
      )}

      {showOriginQuestion && (
        <div className="questionnaire__field">
          <label>Do you know the geographic origin of these ingredients?</label>
          <div className="questionnaire__options-grid">
            <label className="questionnaire__radio">
              <input
                type="radio"
                name="origin_known"
                checked={originKnown === 'yes'}
                onChange={() => setOriginKnown('yes')}
              />
              Yes
            </label>
            <label className="questionnaire__radio">
              <input
                type="radio"
                name="origin_known"
                checked={originKnown === 'no'}
                onChange={() => setOriginKnown('no')}
              />
              No
            </label>
          </div>
          {originKnown === 'yes' && (
            <input
              type="text"
              className="questionnaire__followup"
              placeholder="Region (e.g. Western Ghats, India)"
              value={originRegion}
              onChange={(e) => setOriginRegion(e.target.value)}
            />
          )}
        </div>
      )}

      <div className="questionnaire__field">
        <label>Development status</label>
        <div className="questionnaire__options-grid">
          {DEVELOPMENT_STATUS_OPTIONS.map((opt) => (
            <label key={opt.value} className="questionnaire__radio">
              <input
                type="radio"
                name="development_status"
                value={opt.value}
                checked={developmentStatus === opt.value}
                onChange={() => setDevelopmentStatus(opt.value)}
              />
              {opt.label}
            </label>
          ))}
        </div>
      </div>

      <div className="questionnaire__field">
        <label>What do you want to know? (select all that apply)</label>
        <div className="questionnaire__options-grid">
          {OBJECTIVE_OPTIONS.map((opt) => (
            <label key={opt.value} className="questionnaire__checkbox">
              <input
                type="checkbox"
                checked={objectives.includes(opt.value)}
                onChange={() => toggleInList(objectives, setObjectives, opt.value)}
              />
              {opt.label}
            </label>
          ))}
        </div>
      </div>

      {(formError || error) && (
        <p className="questionnaire__error">{formError || error}</p>
      )}

      <button type="submit" className="questionnaire__submit" disabled={loading}>
        {loading ? 'Classifying…' : 'Continue to classification'}
      </button>
    </form>
  );
}
