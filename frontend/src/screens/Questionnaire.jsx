import { useEffect, useState } from 'react';
import CompositionRow, { CommonIngredientsDatalist } from './CompositionRow.jsx';
import ErrorNotice from '../components/ErrorNotice.jsx';
import useTranslatedTexts from '../utils/useTranslatedTexts.js';
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
export default function Questionnaire({ onSubmit, onDraftChange, initialPip, loading, error, onRestart, currentLang = 'en' }) {
  const initial = initialPip || {};
  const product = initial.product || {};
  const localDraftKey = initial.session_id ? `ip-sakti-case-draft:${initial.session_id}` : '';
  let localDraft = {};
  try { if (localDraftKey) localDraft = JSON.parse(localStorage.getItem(localDraftKey) || '{}'); } catch (_) { /* use the server copy */ }
  const savedProduct = { ...product, ...(localDraft.product || {}) };
  const [productName, setProductName] = useState(localDraft.product_name ?? savedProduct.name ?? '');
  const [protectionTarget, setProtectionTarget] = useState(localDraft.protection_target ?? initial.protection_target ?? '');
  const [composition, setComposition] = useState((localDraft.composition || savedProduct.composition)?.length ? (localDraft.composition || savedProduct.composition).map((row) => ({ ...row, id: `row-${rowIdCounter++}`, quantity: row.quantity || '', unit: row.unit || '' })) : [newRow()]);
  const [intendedUse, setIntendedUse] = useState(localDraft.intended_use ?? savedProduct.intended_use ?? '');
  const [classicalBasis, setClassicalBasis] = useState(localDraft.classical_basis ?? savedProduct.classical_basis ?? '');
  const [classicalReference, setClassicalReference] = useState(localDraft.classical_reference ?? savedProduct.classical_reference ?? '');
  const [novelty, setNovelty] = useState(localDraft.novelty ?? savedProduct.novelty ?? '');
  const [ingredientSources, setIngredientSources] = useState(localDraft.ingredient_sources ?? savedProduct.ingredient_sources ?? []);
  const [originKnown, setOriginKnown] = useState(localDraft.biological_origin_known ?? savedProduct.biological_origin_known ?? '');
  const [originRegion, setOriginRegion] = useState(localDraft.biological_origin_region ?? savedProduct.biological_origin_region ?? '');
  const [developmentStatus, setDevelopmentStatus] = useState(localDraft.development_status ?? savedProduct.development_status ?? '');
  const [objectives, setObjectives] = useState(localDraft.objective ?? initial.objective ?? []);
  const [formError, setFormError] = useState(null);
  const optionLabel = useTranslatedTexts([
    ...PROTECTION_TARGET_OPTIONS, ...INTENDED_USE_OPTIONS, ...CLASSICAL_BASIS_OPTIONS,
    ...NOVELTY_OPTIONS, ...INGREDIENT_SOURCE_OPTIONS, ...DEVELOPMENT_STATUS_OPTIONS,
    ...OBJECTIVE_OPTIONS,
  ].map((option) => option.label).concat([
    'Product Intake Questionnaire', 'Tell us about your product to classify its IP and regulatory pathway.',
    'Product name (optional)', 'What are you trying to protect?', 'Composition', 'Add ingredient',
    'Intended use', 'Is it based on a classical/existing Ayurvedic formulation?',
    'Is the formulation new, modified, or existing?', 'Source of ingredients (select all that apply)',
    'Do you know the geographic origin of these ingredients?', 'Yes', 'No', 'Development status',
    'What do you want to know? (select all that apply)', 'Classifying…', 'Analyze & Classify',
    'e.g. Ashwagandha-Shatavari Rasayana', 'Name of the classical formulation (optional)',
    'Region (e.g. Western Ghats, India)',
    'Please tell us what you’re trying to protect.',
    'Please select at least one thing you want to know.',
  ]), currentLang);

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

  useEffect(() => {
    if (!onDraftChange || !initialPip?.session_id) return undefined;
    const draft = { product_name: productName, objective: objectives, protection_target: protectionTarget || null };
    if (needsComposition) draft.composition = composition.filter((row) => row.ingredient.trim()).map(({ ingredient, quantity, unit, is_active }) => ({ ingredient: ingredient.trim(), quantity: quantity || null, unit: unit || null, is_active }));
    else draft.composition = [];
    if (needsFormulationDetail) {
      draft.intended_use = intendedUse || null;
      draft.classical_basis = classicalBasis || null;
      draft.classical_reference = classicalReference;
      draft.novelty = novelty || null;
    } else { draft.intended_use = null; draft.classical_basis = null; draft.classical_reference = null; draft.novelty = null; }
    if (needsSourceDetail) {
      draft.ingredient_sources = ingredientSources;
      draft.biological_origin_known = showOriginQuestion ? (originKnown || null) : null;
      draft.biological_origin_region = showOriginQuestion ? originRegion : null;
    } else { draft.ingredient_sources = []; draft.biological_origin_known = null; draft.biological_origin_region = null; }
    draft.development_status = developmentStatus || null;
    try { localStorage.setItem(localDraftKey, JSON.stringify(draft)); } catch (_) { /* server autosave still runs */ }
    const timer = window.setTimeout(() => {
      onDraftChange(draft);
    }, 350);
    return () => window.clearTimeout(timer);
  }, [onDraftChange, initialPip?.session_id, productName, protectionTarget, composition, intendedUse, classicalBasis, classicalReference, novelty, ingredientSources, originKnown, originRegion, developmentStatus, objectives, needsComposition, needsFormulationDetail, needsSourceDetail, showOriginQuestion]);

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
      setFormError(optionLabel('Please tell us what you\u2019re trying to protect.'));
      return;
    }
    if (objectives.length === 0) {
      setFormError(optionLabel('Please select at least one thing you want to know.'));
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

      <h2 className="questionnaire__title">{optionLabel('Product Intake Questionnaire')}</h2>
      <p className="questionnaire__subtitle">
        {optionLabel('Tell us about your product to classify its IP and regulatory pathway.')}
      </p>

      <div className="questionnaire__field">
        <label>{optionLabel('Product name (optional)')}</label>
        <input
          type="text"
          value={productName}
          onChange={(e) => setProductName(e.target.value)}
          placeholder={optionLabel('e.g. Ashwagandha-Shatavari Rasayana')}
        />
      </div>

      <div className="questionnaire__field">
        <label>{optionLabel('What are you trying to protect?')}</label>
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
              {optionLabel(opt.label)}
            </label>
          ))}
        </div>
      </div>

      {needsComposition && (
        <div className="questionnaire__field">
          <label>{optionLabel('Composition')}</label>
          <div className="questionnaire__composition">
            {composition.map((row) => (
              <CompositionRow
                key={row.id}
                row={row}
                onChange={(updated) => updateRow(row.id, updated)}
                onRemove={() => removeRow(row.id)}
                canRemove={composition.length > 1}
                currentLang={currentLang}
              />

            ))}
            <button type="button" className="questionnaire__add-row" onClick={addRow}>
              + {optionLabel('Add ingredient')}
            </button>
          </div>
        </div>
      )}

      {needsFormulationDetail && (
        <div className="questionnaire__field">
          <label>{optionLabel('Intended use')}</label>
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
                {optionLabel(opt.label)}
              </label>
            ))}
          </div>
        </div>
      )}

      {needsFormulationDetail && (
        <div className="questionnaire__field">
          <label>{optionLabel('Is it based on a classical/existing Ayurvedic formulation?')}</label>
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
                {optionLabel(opt.label)}
              </label>
            ))}
          </div>
          {classicalBasis === 'yes' && (
            <input
              type="text"
              className="questionnaire__followup"
              placeholder={optionLabel('Name of the classical formulation (optional)')}
              value={classicalReference}
              onChange={(e) => setClassicalReference(e.target.value)}
            />
          )}
        </div>
      )}

      {needsFormulationDetail && showNovelty && (
        <div className="questionnaire__field">
          <label>{optionLabel('Is the formulation new, modified, or existing?')}</label>
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
                {optionLabel(opt.label)}
              </label>
            ))}
          </div>
        </div>
      )}

      {needsSourceDetail && (
        <div className="questionnaire__field">
          <label>{optionLabel('Source of ingredients (select all that apply)')}</label>
          <div className="questionnaire__options-grid">
            {INGREDIENT_SOURCE_OPTIONS.map((opt) => (
              <label key={opt.value} className="questionnaire__checkbox">
                <input
                  type="checkbox"
                  checked={ingredientSources.includes(opt.value)}
                  onChange={() => toggleInList(ingredientSources, setIngredientSources, opt.value)}
                />
                {optionLabel(opt.label)}
              </label>
            ))}
          </div>
        </div>
      )}

      {showOriginQuestion && (
        <div className="questionnaire__field">
          <label>{optionLabel('Do you know the geographic origin of these ingredients?')}</label>
          <div className="questionnaire__options-grid">
            <label className="questionnaire__radio">
              <input
                type="radio"
                name="origin_known"
                checked={originKnown === 'yes'}
                onChange={() => setOriginKnown('yes')}
              />
              {optionLabel('Yes')}
            </label>
            <label className="questionnaire__radio">
              <input
                type="radio"
                name="origin_known"
                checked={originKnown === 'no'}
                onChange={() => setOriginKnown('no')}
              />
              {optionLabel('No')}
            </label>
          </div>
          {originKnown === 'yes' && (
            <input
              type="text"
              className="questionnaire__followup"
              placeholder={optionLabel('Region (e.g. Western Ghats, India)')}
              value={originRegion}
              onChange={(e) => setOriginRegion(e.target.value)}
            />
          )}
        </div>
      )}

      <div className="questionnaire__field">
        <label>{optionLabel('Development status')}</label>
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
                {optionLabel(opt.label)}
            </label>
          ))}
        </div>
      </div>

      <div className="questionnaire__field">
        <label>{optionLabel('What do you want to know? (select all that apply)')}</label>
        <div className="questionnaire__options-grid">
          {OBJECTIVE_OPTIONS.map((opt) => (
            <label key={opt.value} className="questionnaire__checkbox">
              <input
                type="checkbox"
                checked={objectives.includes(opt.value)}
                onChange={() => toggleInList(objectives, setObjectives, opt.value)}
              />
              {optionLabel(opt.label)}
            </label>
          ))}
        </div>
      </div>

      {formError && <p className="questionnaire__error">{formError}</p>}
      <ErrorNotice error={error} onRestart={onRestart} currentLang={currentLang} />

      <button type="submit" className="questionnaire__submit" disabled={loading}>
        {loading ? optionLabel('Classifying…') : optionLabel('Analyze & Classify')}
      </button>
    </form>
  );
}
