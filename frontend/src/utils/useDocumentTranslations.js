import { useEffect } from 'react';
import { translateAsync } from './translator.js';

const textState = new WeakMap();
const attributeState = new WeakMap();
const TRANSLATABLE_ATTRIBUTES = ['placeholder', 'title', 'aria-label', 'alt'];
const INDIC_TEXT = /[\u0600-\u06ff\u0900-\u0d7f]/u;
const SKIP_SELECTOR = [
  'script', 'style', 'noscript', 'code', 'pre', 'svg', 'textarea',
  '[data-translation-ignore]',
].join(',');

function hasEnglishText(value) {
  return /[a-z]{2,}/i.test(value);
}

async function translateDisplayText(source, language) {
  // If Bhashini already returned target-script text but left technical words
  // in Latin characters, translate those runs independently. This preserves
  // the surrounding sentence and gives acronyms/terms a script fallback.
  if (INDIC_TEXT.test(source)) {
    const runs = [...source.matchAll(/[A-Za-z][A-Za-z0-9]*(?:[-/][A-Za-z0-9]+)*/g)];
    if (!runs.length) return source;
    const rendered = await Promise.all(runs.map(([term]) => translateAsync(term, language)));
    let result = '';
    let cursor = 0;
    runs.forEach((match, index) => {
      result += source.slice(cursor, match.index) + rendered[index];
      cursor = match.index + match[0].length;
    });
    return result + source.slice(cursor);
  }
  return translateAsync(source, language);
}

function isSkipped(node, root) {
  const parent = node.parentElement;
  if (!parent || !root.contains(parent)) return true;
  return Boolean(parent.closest(SKIP_SELECTOR));
}

function translateTextNode(node, language) {
  const current = node.nodeValue || '';
  const state = textState.get(node);
  const source = state && current === state.rendered ? state.source : current;
  if (!source.trim()) return;

  if (language === 'en') {
    if (current !== source) node.nodeValue = source;
    textState.set(node, { source, rendered: source, language });
    return;
  }

  if (state && state.language === language && current === state.rendered) return;
  if (!hasEnglishText(source)) return;

  const nextState = { source, rendered: current, language };
  textState.set(node, nextState);
  translateDisplayText(source, language).then((translated) => {
    if (!node.isConnected || node.nodeValue !== current || textState.get(node) !== nextState) return;
    nextState.rendered = translated;
    node.nodeValue = translated;
  });
}

function translateAttribute(element, name, language) {
  const current = element.getAttribute(name);
  if (current === null || !current.trim()) return;
  let attributes = attributeState.get(element);
  if (!attributes) {
    attributes = new Map();
    attributeState.set(element, attributes);
  }
  const state = attributes.get(name);
  const source = state && current === state.rendered ? state.source : current;

  if (language === 'en') {
    if (current !== source) element.setAttribute(name, source);
    attributes.set(name, { source, rendered: source, language });
    return;
  }
  if (state && state.language === language && current === state.rendered) return;
  if (!hasEnglishText(source)) return;

  const nextState = { source, rendered: current, language };
  attributes.set(name, nextState);
  translateDisplayText(source, language).then((translated) => {
    if (!element.isConnected || element.getAttribute(name) !== current || attributes.get(name) !== nextState) return;
    nextState.rendered = translated;
    element.setAttribute(name, translated);
  });
}

function scan(root, language) {
  if (!root) return;
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let node;
  while ((node = walker.nextNode())) {
    if (!isSkipped(node, root)) translateTextNode(node, language);
  }
  root.querySelectorAll('*').forEach((element) => {
    if (element.closest(SKIP_SELECTOR)) return;
    for (const name of TRANSLATABLE_ATTRIBUTES) translateAttribute(element, name, language);
  });
}

function scanAddedNode(node, root, language) {
  if (node.nodeType === Node.TEXT_NODE) {
    if (!isSkipped(node, root)) translateTextNode(node, language);
    return;
  }
  if (node.nodeType !== Node.ELEMENT_NODE) return;

  if (!node.closest(SKIP_SELECTOR)) {
    for (const name of TRANSLATABLE_ATTRIBUTES) translateAttribute(node, name, language);
  }
  scan(node, language);
}

export default function useDocumentTranslations(language) {
  useEffect(() => {
    const root = document.querySelector('.app-shell');
    if (!root) return undefined;
    scan(root, language);
    // Translate only the changed DOM nodes. Rescanning the entire app after
    // every translated text mutation caused an O(n²) wave of work, which made
    // language changes appear to freeze the page on larger screens.
    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.type === 'characterData') {
          if (!isSkipped(mutation.target, root)) translateTextNode(mutation.target, language);
          continue;
        }
        if (mutation.type === 'attributes') {
          const element = mutation.target;
          if (!element.closest(SKIP_SELECTOR)) translateAttribute(element, mutation.attributeName, language);
          continue;
        }
        for (const added of mutation.addedNodes) scanAddedNode(added, root, language);
      }
    });
    observer.observe(root, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: TRANSLATABLE_ATTRIBUTES });
    return () => observer.disconnect();
  }, [language]);
}
