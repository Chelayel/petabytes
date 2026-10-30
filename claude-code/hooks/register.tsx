import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Mood, Scene } from '../types'
import { SPRITES } from './sprites'
import type { Sprite } from './sprites'

/**
 * Petabytes in Claude Code. It tells the Petabytes Mac app what Claude is doing, so the pet on your Dock reacts
 * at full size (the app listens on 127.0.0.1 only; with it closed, nothing happens). A small pixel-art pet can
 * also sit above the prompt: off unless /pet on.
 * It gets curious when Claude reads, excited when it edits, crosses its fingers for tests and cheers or hides
 * at the result, celebrates a push and a finished turn, and naps when nothing happens for a while.
 * /pet chooses the pet (remembered across sessions); /pet off and /pet on hide and show it.
 */

/** The same pets as the editors and the Mac app, as an emoji each (a terminal can't draw their art). */
type Pet = { name: string; kind: string; emoji: string }
const TURTLE: Pet = { name: 'Shelly', kind: 'sea turtle', emoji: '🐢' }
const PETS: Record<string, Pet> = {
  turtle: TURTLE,
  jellyfish: { name: 'Bloop', kind: 'jellyfish', emoji: '🪼' },
  octopus: { name: 'Inky', kind: 'octopus', emoji: '🐙' },
  crab: { name: 'Pinchy', kind: 'crab', emoji: '🦀' },
  pufferfish: { name: 'Puff', kind: 'pufferfish', emoji: '🐡' },
  whale: { name: 'Blue', kind: 'whale', emoji: '🐋' },
  clownfish: { name: 'Clem', kind: 'clownfish', emoji: '🐠' },
  seahorse: { name: 'Sandy', kind: 'seahorse', emoji: '🐚' },
  shark: { name: 'Finn', kind: 'shark', emoji: '🦈' },
  dolphin: { name: 'Splash', kind: 'dolphin', emoji: '🐬' },
  angelfish: { name: 'Angie', kind: 'angelfish', emoji: '🐟' },
  tang: { name: 'Indigo', kind: 'blue tang', emoji: '🐟' },
  retriever: { name: 'Biscuit', kind: 'golden retriever', emoji: '🐕' },
  spitz: { name: 'Loopee', kind: 'German Spitz', emoji: '🐩' },
  cat: { name: 'Byte', kind: 'cat', emoji: '🐈' },
  bunny: { name: 'Clover', kind: 'bunny', emoji: '🐇' },
  hamster: { name: 'Nugget', kind: 'hamster', emoji: '🐹' },
  burger: { name: 'Patty', kind: 'burger', emoji: '🍔' },
  sushi: { name: 'Nori', kind: 'sushi', emoji: '🍣' },
  pizza: { name: 'Pepe', kind: 'pizza', emoji: '🍕' },
  donut: { name: 'Sprinkles', kind: 'donut', emoji: '🍩' },
  taco: { name: 'Tuesday', kind: 'taco', emoji: '🌮' },
  slime: { name: 'Squish', kind: 'slime', emoji: '🟢' },
  ghost: { name: 'Boo', kind: 'ghost', emoji: '👻' },
  knight: { name: 'Sir Pix', kind: 'knight', emoji: '🛡️' },
  robot: { name: 'Bolt', kind: 'robot', emoji: '🤖' },
  laptop: { name: 'Lappy', kind: 'laptop', emoji: '💻' },
  controller: { name: 'Joy', kind: 'controller', emoji: '🎮' },
  mug: { name: 'Java', kind: 'coffee mug', emoji: '☕' },
  duck: { name: 'Quackers', kind: 'rubber duck', emoji: '🦆' },
  cactus: { name: 'Spike', kind: 'cactus', emoji: '🌵' },
  floppy: { name: 'Floppy', kind: 'floppy disk', emoji: '💾' },
  mouse: { name: 'Click', kind: 'mouse', emoji: '🖱️' },
  headphones: { name: 'Beats', kind: 'headphones', emoji: '🎧' },
  sticky: { name: 'Post', kind: 'sticky note', emoji: '📝' },
}

const LINES = {
  hello: ['Hi! I\'m {name}.', 'Hello! Let\'s build something.', '{name}, reporting for duty!'],
  late: ['It\'s late. I\'ll keep you company.', 'Night shift, huh?'],
  prompt: ['On it!', 'Ooh, a new task.', 'Let\'s go!', 'I\'m listening.', 'Good one.'],
  read: ['Reading up...', 'Looking around...', 'What\'s in here?', 'Research time.'],
  edit: ['Ooh, new code.', 'Look at it go!', 'Typing away!', 'Fresh code, coming up.'],
  test: ['Fingers crossed!', 'Testing, testing...', 'Come on, green!'],
  testOk: ['All green!', 'Tests passed!', 'Woohoo, it works!'],
  testFail: ['Oof, tests failed.', 'Red. We\'ll get it.', '*hides* Not green...'],
  push: ['Ship it!', 'Off it goes!', 'Pushed! Bon voyage, commits.'],
  commit: ['Committed! Nice.', 'Saved to the history books.'],
  install: ['Downloading the internet...', 'So many packages.'],
  danger: ['*hides* Careful with that!', 'Are you sure about that one?'],
  failed: ['Hmm, that didn\'t work.', 'Exit code says no.', 'Uh oh.'],
  web: ['Researching!', 'To the internet!'],
  agent: ['Calling in a friend!', 'Teamwork!'],
  done: ['Done! Nice work.', 'All done!', 'Ta-da!', 'That was fun.'],
  wake: ['Oh! I\'m up.', 'Back to work?', 'Mm, what did I miss?'],
  sleep: ['zzz...'],
  pet: ['*happy noises*', 'Hehe!', 'I like you too!'],
} as const

type LineKey = keyof typeof LINES

const MOOD_MARK: Record<Mood, string> = { calm: '', happy: '✨', excited: '⚡', curious: '❓', worried: '💦', hiding: '' }
const SHADES = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

/** A run of terminal cells drawn the same way: a half-block character with its colors. */
type Run = { text: string; color?: string; backgroundColor?: string }

/** The sprite as terminal rows: two pixel rows to a cell (▀ over ▄), runs of the same colors merged. */
function cells(sprite: Sprite, mirrored: boolean): Run[][] {
  const rows = sprite.rows.map(r => (mirrored ? [...r].reverse().join('') : r))
  const shade = (k: string | undefined) => (k && k !== '.' ? sprite.palette[SHADES.indexOf(k)] : undefined)
  const lines: Run[][] = []
  for (let y = 0; y < rows.length; y += 2) {
    const runs: Run[] = []
    const top = rows[y] ?? '', bottom = rows[y + 1] ?? ''
    for (let x = 0; x < top.length; x++) {
      const up = shade(top[x]), down = shade(bottom[x])
      const run: Run = up && down ? { text: '▀', color: up, backgroundColor: down }
        : up ? { text: '▀', color: up } : down ? { text: '▄', color: down } : { text: ' ' }
      const last = runs[runs.length - 1]
      if (last && last.color === run.color && last.backgroundColor === run.backgroundColor && last.text[0] === run.text) last.text += run.text
      else runs.push(run)
    }
    lines.push(runs)
  }
  return lines
}
const SLEEP_AFTER = 3 * 60 * 1000

const calm: Scene = { mood: 'calm', moodUntil: 0, line: '', lineUntil: 0, sleeping: false }
const scene = atom({ plugin: 'petabytes', key: 'scene' } as const, calm, { shape: 'scene-3' })
const petId = atom({ plugin: 'petabytes', key: 'pet' } as const, 'turtle')
/** The pet above the prompt is off unless asked for: the Mac app's pet is the main one. */
const hidden = atom({ plugin: 'petabytes', key: 'hidden' } as const, true)

/** Where the Petabytes Mac app listens for what Claude is doing (ClaudeCodeLink in the app). */
const MAC_APP = 'http://127.0.0.1:47365/'

/**
 Tells the Mac or Windows app, and leaves the news in ~/.petabytes/claude-code.json for the pets in VS Code and IntelliJ,
 which watch that file. Each pet decides whether it reacts (cooldowns, chance) and says what. Never fails.
 */
async function tell($: EngineInterface, key: string) {
  try {
    // Windows keeps the home folder in USERPROFILE.
    const home = (await $.env.get('HOME')) ?? (await $.env.get('USERPROFILE'))
    if (home) await $.fs.write(`${home}/.petabytes/claude-code.json`, JSON.stringify({ key, at: Date.now() }))
  } catch {
    // Nowhere to write: the IDE pets just don't hear about it.
  }
  try {
    await $.http.fetch(MAC_APP, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ type: 'react', key }) })
  } catch {
    // The app isn't running, or isn't listening: the pet just doesn't hear about it.
  }
}

const pick = <T,>(list: readonly [T, ...T[]]): T => list[Math.floor(Math.random() * list.length)] ?? list[0]

/** What a shell command is, for the pet's reaction to it (or nothing worth reacting to). */
function kindOf(command: string): 'test' | 'push' | 'commit' | 'install' | 'danger' | undefined {
  if (/\brm\s+-[a-z]*r[a-z]*f|\bgit\s+push\b.*--force|\bgit\s+reset\s+--hard\b/i.test(command)) return 'danger'
  if (/\bgit\s+push\b/i.test(command)) return 'push'
  if (/\bgit\s+commit\b/i.test(command)) return 'commit'
  if (/\b(npm|pnpm|yarn|bun)\s+(i|install|add|ci)\b|\bpip3?\s+install\b|\bbrew\s+install\b/i.test(command)) return 'install'
  if (/\b(test|jest|vitest|pytest|mocha)\b|gradlew?\s+.*\btest\b|\bgo\s+test\b|\bcargo\s+test\b/i.test(command)) return 'test'
  return undefined
}

/** When something last happened, for napping, and when the pet last talked about routine work. */
let lastActive = 0
let lastChatter = 0

/** Sets a mood and maybe a line; any reaction also wakes the pet. */
async function react($: EngineInterface, mood: Mood, key?: LineKey, ms = 2600) {
  const now = await $.clock.now()
  const wasAsleep = (await read($, scene)).sleeping
  lastActive = now
  const pet = PETS[await read($, petId)] ?? TURTLE
  const text = key ? pick(LINES[key]).replace('{name}', pet.name) : ''
  await update($, scene, s => ({
    ...s,
    sleeping: false,
    mood,
    moodUntil: now + ms,
    line: wasAsleep && !text ? pick(LINES.wake) : text || s.line,
    lineUntil: text || wasAsleep ? now + ms : s.lineUntil,
  }))
}

/** Reading and editing happen a lot: talk about them now and then, not every time. */
async function chatty($: EngineInterface) {
  const now = await $.clock.now()
  if (now - lastChatter < 25_000) return false
  lastChatter = now
  return true
}

/**
 * The pet keeps still: every couple of seconds it only lets a reaction or a line run out, and naps after a quiet
 * while. Nothing is written (so nothing redraws) unless one of those actually changed.
 */
async function step($: EngineInterface) {
  const now = await $.clock.now()
  if (await read($, hidden)) return
  const s = await read($, scene)
  const asleep = s.sleeping || now - lastActive > SLEEP_AFTER
  const fellAsleep = asleep && !s.sleeping
  const mood: Mood = now > s.moodUntil ? 'calm' : s.mood
  const line = fellAsleep ? pick(LINES.sleep) : now > s.lineUntil && !asleep ? '' : s.line
  if (asleep === s.sleeping && mood === s.mood && line === s.line) return
  await update($, scene, current => ({
    ...current,
    sleeping: asleep,
    mood,
    line,
    lineUntil: fellAsleep ? Number.MAX_SAFE_INTEGER : current.lineUntil,
  }))
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'pet', description: 'Choose your Petabytes pet (/pet loopee), or /pet off, /pet on' })
    const saved = await $.store.get('pet')
    if (typeof saved === 'string' && PETS[saved]) await update($, petId, () => saved)
    const terminal = await $.store.get('terminal')
    await update($, hidden, () => terminal !== true)
    const hour = new Date(await $.clock.now()).getHours()
    await react($, 'happy', hour >= 23 || hour < 5 ? 'late' : 'hello', 3500)

    $.clock.every(2000, () => step($))

    return next(e)
  })

  on('command.run', { command: 'pet' }, async ($, e) => {
    const wanted = e.args.trim().toLowerCase()
    if (wanted === 'off' || wanted === 'on') {
      await update($, hidden, () => wanted === 'off')
      await $.store.set('terminal', wanted === 'on')
      return { text: wanted === 'off'
        ? 'The pet above the prompt is off. The Petabytes Mac app\'s pet still reacts to Claude.'
        : 'The pet is above the prompt too. /pet off hides it.' }
    }
    if (!wanted) {
      const current = PETS[await read($, petId)] ?? TURTLE
      const all = Object.values(PETS).map(p => `${p.emoji} ${p.name}`).join('  ')
      return { text: `The pet on your Mac (the Petabytes app) reacts to Claude; choose it in the app's menu. Here, /pet on shows a small one above the prompt too, now ${current.emoji} ${current.name} the ${current.kind}; choose it with /pet <name>:\n${all}` }
    }
    const found = Object.entries(PETS).find(([id, p]) => id === wanted || p.name.toLowerCase() === wanted || p.kind.toLowerCase() === wanted)
    if (!found) return { text: `No pet called "${e.args.trim()}". Try /pet to see them all.` }
    await update($, petId, () => found[0])
    await $.store.set('pet', found[0])
    await update($, hidden, () => false)
    await $.store.set('terminal', true)
    await react($, 'happy', 'hello', 3000)
    return { text: `Say hi to ${found[1].emoji} ${found[1].name} the ${found[1].kind}!` }
  })

  // A pet's failure never gets in the way: each of these lets the event through if the pet's part throws.
  on('prompt.submit', async ($, e, next) => {
    void tell($, 'claudeStart')
    await react($, 'curious', 'prompt', 1800)
    return next(e)
  }).catch(($, e, next) => next(e))

  on('tool.call', async ($, e, next) => {
    switch (e.tool) {
      case 'Read':
        void tell($, 'claudeRead')
        await react($, 'curious', (await chatty($)) ? 'read' : undefined, 1200)
        return next(e)
      case 'Edit':
      case 'Write':
      case 'NotebookEdit':
        void tell($, 'claudeEdit')
        await react($, 'excited', (await chatty($)) ? 'edit' : undefined, 2000)
        return next(e)
      case 'WebFetch':
      case 'WebSearch':
        void tell($, 'claudeWeb')
        await react($, 'curious', (await chatty($)) ? 'web' : undefined, 1500)
        return next(e)
      case 'Agent':
        void tell($, 'claudeAgent')
        await react($, 'excited', 'agent', 2000)
        return next(e)
      case 'Bash': {
        const kind = kindOf(e.command)
        if (kind === 'danger' || kind === 'test' || kind === 'install') void tell($, kind)
        if (kind === 'danger') await react($, 'hiding', 'danger', 2500)
        else if (kind === 'test') await react($, 'excited', 'test', 60_000)
        else if (kind === 'install') await react($, 'excited', 'install', 3000)
        const ran = await next(e)
        const failed = ran.deny === undefined && ran.isError === true
        if (kind === 'test') void tell($, failed ? 'claudeTestsFailed' : 'claudeTestsOk')
        else if (failed) void tell($, 'commandFail')
        else if (kind === 'push') void tell($, 'gitPush')
        else if (kind === 'commit') void tell($, 'commit')
        if (kind === 'test') await react($, failed ? 'hiding' : 'happy', failed ? 'testFail' : 'testOk', 3000)
        else if (failed) await react($, 'worried', 'failed', 2500)
        else if (kind === 'push') await react($, 'happy', 'push', 3000)
        else if (kind === 'commit') await react($, 'happy', 'commit', 2600)
        return ran
      }
      default:
        await react($, 'calm')
        return next(e)
    }
  }).catch(($, e, next) => next(e))

  on('turn.complete', async ($, e, next) => {
    void tell($, 'claudeDone')
    await react($, 'happy', 'done', 3000)
    return next(e)
  }).catch(($, e, next) => next(e))

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.props.hasSurvey || (await read($, hidden))) return next(e)
    const { Box, Text } = $.ui.resolve(e)
    const s = await read($, scene)
    const id = await read($, petId)
    const pet = PETS[id] ?? TURTLE
    const sprite = SPRITES[id] ?? SPRITES.turtle
    if (!sprite) return next(e)
    const faded = s.sleeping || s.mood === 'hiding'
    const mark = s.sleeping ? '💤' : s.mood === 'hiding' ? '🙈' : MOOD_MARK[s.mood]
    const lines = cells(sprite, false)

    return (
      <Box flexDirection="row">
        <Box flexDirection="column">
          {lines.map((runs, row) => (
            <Box key={`row-${row}`} flexDirection="row">
              {runs.map((run, n) => (
                <Text key={`${row}-${n}`} color={run.color} backgroundColor={run.backgroundColor} dimColor={faded}>{run.text}</Text>
              ))}
            </Box>
          ))}
        </Box>
        <Box flexDirection="column" justifyContent="center" paddingLeft={2}>
          {mark ? <Text>{mark}</Text> : null}
          {s.line ? <Text color="cyan">{`"${s.line}"`}</Text> : <Text dimColor>{pet.name}</Text>}
        </Box>
      </Box>
    )
  })
}
