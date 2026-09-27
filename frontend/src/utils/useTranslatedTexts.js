import { useEffect, useMemo, useState } from 'react';
import { t, translateAsync } from './translator.js';

// UI-only translations. API values and legal/citation identifiers remain untouched.
export default function useTranslatedTexts(texts, language) {
  const key = JSON.stringify([...new Set(texts.filter((value) => typeof value === 'string' && value))]);
  const uniqueTexts = useMemo(() => JSON.parse(key), [key]);
  const [result, setResult] = useState({ language: 'en', key: '', values: {} });

  useEffect(() => {
    let active = true;
    if (language === 'en') return () => { active = false; };

    // Reveal translations as each one arrives. A slow or failed request must
    // not hold back every other label on the page.
    let cursor = 0;
    const worker = async () => {
      while (active && cursor < uniqueTexts.length) {
        const source = uniqueTexts[cursor++];
        if (t(source, language) !== source) continue;
        const translated = await translateAsync(source, language);
        if (active && translated !== source) {
          setResult((previous) => ({
            language, key,
            values: {
              ...(previous.language === language && previous.key === key ? previous.values : {}),
              [source]: translated,
            },
          }));
        }
      }
    };
    for (let i = 0; i < Math.min(4, uniqueTexts.length); i++) worker();
    return () => { active = false; };
  }, [language, uniqueTexts, key]);

  return (source) => language === 'en' ? source
    : (result.language === language && result.key === key && result.values[source]) || t(source, language);
}
