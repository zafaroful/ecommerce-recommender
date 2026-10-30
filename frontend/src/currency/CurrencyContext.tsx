import { createContext, useContext, useState, type ReactNode } from 'react';

export type Currency = 'USD' | 'MYR';

const STORAGE_KEY = 'recomify-currency';
const envRate = Number(import.meta.env.VITE_USD_TO_MYR);
// Display-only conversion rate. Set VITE_USD_TO_MYR to change it.
const USD_TO_MYR = Number.isFinite(envRate) && envRate > 0 ? envRate : 4.1;

interface CurrencyValue {
  currency: Currency;
  setCurrency: (currency: Currency) => void;
  formatPrice: (priceUsd: number) => string;
}

const CurrencyContext = createContext<CurrencyValue | null>(null);

function readSavedCurrency(): Currency {
  try {
    return localStorage.getItem(STORAGE_KEY) === 'MYR' ? 'MYR' : 'USD';
  } catch {
    return 'USD';
  }
}

export function CurrencyProvider({ children }: { children: ReactNode }) {
  const [currency, setCurrencyState] = useState<Currency>(readSavedCurrency);

  function setCurrency(next: Currency) {
    setCurrencyState(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // Saving the choice is optional.
    }
  }

  function formatPrice(priceUsd: number): string {
    const amount = currency === 'MYR' ? priceUsd * USD_TO_MYR : priceUsd;
    return new Intl.NumberFormat(currency === 'MYR' ? 'en-MY' : 'en-US', {
      style: 'currency',
      currency,
    }).format(amount);
  }

  return (
    <CurrencyContext.Provider value={{ currency, setCurrency, formatPrice }}>
      {children}
    </CurrencyContext.Provider>
  );
}

export function useCurrency(): CurrencyValue {
  const value = useContext(CurrencyContext);
  if (!value) throw new Error('useCurrency must be used inside CurrencyProvider');
  return value;
}