export function getSpeechRecognition(): SpeechRecognition | null {
  // @ts-ignore
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SR) return null
  // @ts-ignore
  return new SR()
}


