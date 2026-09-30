import { COMMON_INGREDIENTS, QUANTITY_UNIT_OPTIONS } from '../data/options.js';
import TKDL_INGREDIENTS from '../data/tkdl-ingredients.json';
import useTranslatedTexts from '../utils/useTranslatedTexts.js';

export default function CompositionRow({ row, onChange, onRemove, canRemove, currentLang = 'en' }) {
  const update = (field, value) => onChange({ ...row, [field]: value });
  const uiText = useTranslatedTexts([
    'Ingredient (e.g. Ashwagandha extract)', 'Qty', 'Unit (mg, %, ...)', 'Active', 'Remove ingredient',
  ], currentLang);

  return (
    <div className="composition-row">
      <input
        type="text"
        className="composition-row__ingredient"
        placeholder={uiText('Ingredient (e.g. Ashwagandha extract)')}
        value={row.ingredient}
        onChange={(e) => update('ingredient', e.target.value)}
        list="common-ingredients"
      />
      <input
        type="text"
        className="composition-row__quantity"
        placeholder={uiText('Qty')}
        value={row.quantity}
        onChange={(e) => update('quantity', e.target.value)}
      />
      <select
        className="composition-row__unit"
        value={row.unit}
        onChange={(e) => update('unit', e.target.value)}
        aria-label={uiText('Unit (mg, %, ...)')}
      >
        <option value="">{uiText('Unit (mg, %, ...)')}</option>
        {!QUANTITY_UNIT_OPTIONS.some((unit) => unit.value === row.unit) && row.unit && <option value={row.unit}>{row.unit}</option>}
        {QUANTITY_UNIT_OPTIONS.map((unit) => <option key={unit.value} value={unit.value}>{unit.label}</option>)}
      </select>
      <label className="composition-row__active">
        <input
          type="checkbox"
          checked={row.is_active}
          onChange={(e) => update('is_active', e.target.checked)}
        />
        {uiText('Active')}
      </label>
      <button
        type="button"
        className="composition-row__remove"
        onClick={onRemove}
        disabled={!canRemove}
        aria-label={uiText('Remove ingredient')}
        title={uiText('Remove ingredient')}
      >
        ×
      </button>
    </div>
  );
}

export function CommonIngredientsDatalist() {
  return (
    <datalist id="common-ingredients">
      {[...new Set([...COMMON_INGREDIENTS, ...TKDL_INGREDIENTS])].map((name) => (
        <option key={name} value={name} />
      ))}
    </datalist>
  );
}
