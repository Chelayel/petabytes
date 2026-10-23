# Tide Pets

A sea creature lives in a **Tide Pets** panel in your Explorer and reacts to what you're doing. Pick one: **Shelly** the sea turtle, **Bloop** the jellyfish, **Inky** the octopus, **Pinchy** the crab, **Puff** the pufferfish, **Blue** the whale, **Clem** the clownfish, **Sandy** the seahorse or **Finn** the shark.

![The nine pets](https://raw.githubusercontent.com/Chelayel/tide-pets/main/docs/pets.png)

- **Typing:** swims faster
- **Saving:** does a happy loop and blows bubbles
- **New errors in the open file:** looks worried, and hides when several appear at once (Inky inks, Puff puffs up)
- **All errors fixed:** celebrates
- **Tasks:** cheers when one passes, hides when one fails
- **Debugging:** brings out a magnifying glass
- **Switching files:** looks around
- **Away for 3 minutes:** naps
- **Running the app, builds, tests:** "It's alive!", "Compiling, hold on.", "Fingers crossed!"
- **The terminal:** notices when you open it, and reacts to `git push`, installs, tests and risky commands like `rm -rf`
- **Copilot:** notices AI edits and big blocks of code appearing at once
- **Commits and branches:** celebrates a commit, notices a new branch
- **Late nights, mornings, long sessions:** says so, and suggests a stretch
- **Clicked / double-clicked:** does a spin / shows hearts

**Feed it:** click the ♥ on the panel (or **Tide Pets: Feed Pet**) and a `{ }`, `[ ]`, `( )`, `< >` or `;` sinks down for your pet to eat. Every 20th `{` you type drops a crumb too.

![Pets reacting to typing, fixed errors, a new error, failed tests, debugging and being left alone](https://raw.githubusercontent.com/Chelayel/tide-pets/main/docs/moods.png)

## Choose, show or hide

- Command Palette → **Tide Pets: Choose Pet**, **Feed Pet**, **Toggle Pet**, **Show Pet** or **Hide Pet**
- The buttons on the panel's title bar
- The settings below

## Settings

| Setting | Default | |
| --- | --- | --- |
| `tidePets.enabled` | `true` | Show the pet in the Explorer |
| `tidePets.pet` | `"turtle"` | `turtle`, `jellyfish`, `octopus`, `crab`, `pufferfish`, `whale`, `clownfish`, `seahorse` or `shark` |
| `tidePets.name` | `""` | Your pet's name; empty for its own (Shelly, Bloop, Inky, Pinchy, Puff, Blue, Clem, Sandy or Finn) |

Made to go with the [Midnight Tide](https://marketplace.visualstudio.com/items?itemName=Chelayel.midnight-tide-vscode) theme, and works with any theme. In [JetBrains IDEs](https://plugins.jetbrains.com/search?search=tide%20pets) the pet floats along the bottom of the editor.

## License

MIT. Built by [Chelayel](https://www.chelayel.com). Source: [github.com/Chelayel/tide-pets](https://github.com/Chelayel/tide-pets).
