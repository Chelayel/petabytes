/** What the pet is doing right now, as the band above the prompt draws it. */
export type Scene = {
  mood: Mood
  /** Clock time (ms) the mood lasts until; then it's calm again. */
  moodUntil: number
  line: string
  /** Clock time (ms) the line shows until. */
  lineUntil: number
  sleeping: boolean
}

export type Mood = 'calm' | 'happy' | 'excited' | 'curious' | 'worried' | 'hiding'


declare module 'claude-code' {
  interface PluginState {
    petabytes: { scene: Shaped<Scene>; pet: string; hidden: boolean }
  }
}
