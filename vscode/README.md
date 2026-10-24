# Petabytes

Small companions with a big appetite. A pet lives in a **Petabytes** panel in your Explorer and reacts to what you're doing. Pick a sea creature from the **Tide** set or a pet from the **Home** set: **Shelly** the sea turtle, **Bloop** the jellyfish, **Inky** the octopus, **Pinchy** the crab, **Puff** the pufferfish, **Blue** the whale, **Clem** the clownfish, **Sandy** the seahorse, **Finn** the shark, **Splash** the dolphin, **Angie** the angelfish, **Indigo** the blue tang, **Biscuit** the golden retriever, **Byte** the cat, **Clover** the bunny or **Nugget** the hamster.

![A pet swimming faster while you type, celebrating a fix, hiding from failed tests, eating and napping](https://raw.githubusercontent.com/Chelayel/petabytes/main/docs/demo.gif)

![All sixteen pets](https://raw.githubusercontent.com/Chelayel/petabytes/main/docs/pets.png)

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

**Feed it:** click the ♥ on the panel (or **Petabytes: Feed Pet**) and a `{ }`, `[ ]`, `( )`, `< >` or `;` sinks down for your pet to eat. Every 20th `{` you type drops a crumb too.

![Pets reacting to typing, fixed errors, a new error, failed tests, debugging and being left alone](https://raw.githubusercontent.com/Chelayel/petabytes/main/docs/moods.png)

## Choose, show or hide

- Command Palette → **Petabytes: Choose Pet**, **Feed Pet**, **Toggle Pet**, **Show Pet** or **Hide Pet**
- The buttons on the panel's title bar
- The settings below

## Settings

| Setting | Default | |
| --- | --- | --- |
| `petabytes.enabled` | `true` | Show the pet in the Explorer |
| `petabytes.pet` | `"turtle"` | `turtle`, `jellyfish`, `octopus`, `crab`, `pufferfish`, `whale`, `clownfish`, `seahorse`, `shark`, `dolphin`, `angelfish`, `tang`, `retriever`, `cat`, `bunny` or `hamster` |
| `petabytes.name` | `""` | Your pet's name; empty for its own (Shelly, Bloop, Inky, Pinchy, Puff, Blue, Clem, Sandy, Finn, Splash, Angie, Indigo, Biscuit, Byte, Clover or Nugget) |

Works with any theme. In [JetBrains IDEs](https://plugins.jetbrains.com/search?search=petabytes) the pet swims along the editor's right edge.

There's also [a Mac app](https://github.com/Chelayel/petabytes#on-your-mac) whose pet walks along your Dock and reacts to your Mac (the app in front, battery, Wi-Fi, screenshots). It's separate: it can't see your code, so keep this extension for that.

## License

MIT. Built by [Chelayel](https://www.chelayel.com). Source: [github.com/Chelayel/petabytes](https://github.com/Chelayel/petabytes).
