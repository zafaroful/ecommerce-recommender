import { useCurrency, type Currency } from './CurrencyContext';

const OPTIONS: { value: Currency; label: string }[] = [
  { value: 'USD', label: 'USD $' },
  { value: 'MYR', label: 'MYR RM' },
];

export function CurrencyToggle() {
  const { currency, setCurrency } = useCurrency();
  return (
    <div
      role="group"
      aria-label="Currency"
      className="flex rounded-xl border border-slate-300 bg-white p-1"
    >
      {OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          onClick={() => setCurrency(option.value)}
          aria-pressed={currency === option.value}
          className={`min-h-10 rounded-lg px-3 text-sm font-semibold transition ${
            currency === option.value
              ? 'bg-indigo-600 text-white'
              : 'text-slate-700 hover:bg-slate-100'
          }`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}