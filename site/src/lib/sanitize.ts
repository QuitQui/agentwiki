import sanitizeHtml from 'sanitize-html'

const ALLOWED: sanitizeHtml.IOptions = {
  allowedTags: sanitizeHtml.defaults.allowedTags.concat([
    'h1', 'h2', 'h3', 'h4', 'details', 'summary', 'mark', 'del', 'ins',
    'table', 'thead', 'tbody', 'tr', 'th', 'td', 'caption',
    'pre', 'code', 'kbd', 'samp',
  ]),
  allowedAttributes: {
    ...sanitizeHtml.defaults.allowedAttributes,
    '*': ['class', 'id', 'style'],
    a: ['href', 'name', 'target', 'rel'],
    code: ['class'],
  },
  allowedStyles: {
    '*': {
      // Allow only safe style properties
      color: [/.*/],
      background: [/.*/],
      'background-color': [/.*/],
      'font-size': [/.*/],
      'font-weight': [/.*/],
      'text-align': [/.*/],
      'border-left': [/.*/],
      padding: [/.*/],
      margin: [/.*/],
      'border-radius': [/.*/],
    },
  },
  disallowedTagsMode: 'discard',
}

export function sanitize(html: string): string {
  return sanitizeHtml(html, ALLOWED)
}
