import { useEffect, useState } from 'react'

type Theme = 'light' | 'dark'

export function useTheme(): [Theme, (theme: Theme) => void] {
  const [theme, setThemeState] = useState<Theme>(() => {
    // Check if user has saved preference
    const saved = localStorage.getItem('theme') as Theme | null
    if (saved) return saved

    // Check system preference
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark'
    }

    return 'light'
  })

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme)
    localStorage.setItem('theme', newTheme)
    document.documentElement.setAttribute('data-theme', newTheme)
  }

  useEffect(() => {
    // Apply theme to document
    document.documentElement.setAttribute('data-theme', theme)

    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handleChange = (e: MediaQueryListEvent) => {
      const newTheme: Theme = e.matches ? 'dark' : 'light'
      // Only update if user hasn't set a preference
      if (!localStorage.getItem('theme')) {
        setThemeState(newTheme)
        document.documentElement.setAttribute('data-theme', newTheme)
      }
    }

    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [theme])

  return [theme, setTheme]
}
