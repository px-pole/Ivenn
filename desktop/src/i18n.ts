import i18next from 'i18next'
import LanguageDetector from 'i18next-browser-languagedetector'
import { initReactI18next } from 'react-i18next'
import enTranslations from './locales/en.json'
import deTranslations from './locales/de.json'
import frTranslations from './locales/fr.json'
import esTranslations from './locales/es.json'

const resources = {
  en: { translation: enTranslations },
  de: { translation: deTranslations },
  fr: { translation: frTranslations },
  es: { translation: esTranslations },
}

i18next
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
    },
    interpolation: {
      escapeValue: false,
    },
  })

export default i18next
