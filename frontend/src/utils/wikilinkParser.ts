/**
 * Utilitário de parsing de Wikilinks na sintaxe [[Nome do Artigo]] ou [[Nome do Artigo|Texto de Exibição]].
 */

export interface TextSegment {
  type: 'text'
  content: string
}

export interface WikilinkSegment {
  type: 'wikilink'
  raw: string
  targetTitle: string
  displayText: string
}

export type ParsedSegment = TextSegment | WikilinkSegment

const WIKILINK_REGEX = /\[\[([^\]\|]+)(?:\|([^\]]+))?\]\]/g

export function parseWikilinks(text: string): ParsedSegment[] {
  if (!text) return []

  const segments: ParsedSegment[] = []
  let lastIndex = 0
  let match: RegExpExecArray | null

  // Reset regex index
  WIKILINK_REGEX.lastIndex = 0

  while ((match = WIKILINK_REGEX.exec(text)) !== null) {
    const matchIndex = match.index

    // Adiciona o texto puro antes do match
    if (matchIndex > lastIndex) {
      segments.push({
        type: 'text',
        content: text.slice(lastIndex, matchIndex),
      })
    }

    const targetTitle = match[1] ? match[1].trim() : ''
    const displayText = match[2] ? match[2].trim() : targetTitle

    segments.push({
      type: 'wikilink',
      raw: match[0],
      targetTitle,
      displayText,
    })

    lastIndex = WIKILINK_REGEX.lastIndex
  }

  // Adiciona qualquer texto restante após o último match
  if (lastIndex < text.length) {
    segments.push({
      type: 'text',
      content: text.slice(lastIndex),
    })
  }

  return segments
}
