import { COMMON_INGREDIENTS } from '../data/options.js';

/**
 * Ingredient autocomplete uses a native <datalist> rather than a custom
 * dropdown. This is a deliberate choice, not a shortcut: a custom
 * suggestion list that opens `onFocus` (before the user has typed anything)
 * is exactly the bug the previous bolt.new build hit — the browser's native
 * datalist only ever shows suggestions once there's something to filter on,
 * so that whole bug class doesn't exist here.
 */
export default function CompositionRow({ row, onChange, onRemove, canRemove }) {
  const update = (field, value) => onChange({ ...row, [field]: value });

  return (
    <div className="composition-row">
      <input
        type="text"
        className="composition-row__ingredient"
        placeholder="Ingredient (e.g. Ashwagandha extract)"
        value={row.ingredient}
        onChange={(e) => update('ingredient', e.target.value)}
        list="common-ingredients"
      />
      <input
        type="text"
        className="composition-row__quantity"
        placeholder="Qty"
        value={row.quantity}
        onChange={(e) => update('quantity', e.target.value)}
      />
      <input
        type="text"
        className="composition-row__unit"
        placeholder="Unit (mg, %, ...)"
        value={row.unit}
        onChange={(e) => update('unit', e.target.value)}
      />
      <label className="composition-row__active">
        <input
          type="checkbox"
          checked={row.is_active}
          onChange={(e) => update('is_active', e.target.checked)}
        />
        Active
      </label>
      <button
        type="button"
        className="composition-row__remove"
        onClick={onRemove}
        disabled={!canRemove}
        aria-label="Remove ingredient"
        title="Remove ingredient"
      >
        ×
      </button>
    </div>
  );
}

export function CommonIngredientsDatalist() {
  return (
    <datalist id="common-ingredients">
      {COMMON_INGREDIENTS.map((name) => (
        <option key={name} value={name} />
      ))}
    </datalist>
  );
}
