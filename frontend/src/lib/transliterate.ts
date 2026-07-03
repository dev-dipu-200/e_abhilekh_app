const translitCache: Record<string, string[]> = {}

export async function fetchSuggestions(word: string): Promise<string[]> {
  if (!word.trim()) return []
  const lower = word.toLowerCase()
  if (translitCache[lower]) return translitCache[lower]
  if (/[\u0900-\u097F]/.test(lower)) return [lower]
  try {
    const resp = await fetch(`/api/transliterate?text=${encodeURIComponent(lower)}`)
    const data = await resp.json()
    const suggestions: string[] = data.suggestions || []
    if (suggestions.length) translitCache[lower] = suggestions
    return suggestions
  } catch {
    return []
  }
}

export async function transliterateWord(word: string): Promise<string> {
  const suggestions = await fetchSuggestions(word)
  return suggestions[0] || word
}

export function clearCache(): void {
  Object.keys(translitCache).forEach(k => delete translitCache[k])
}
