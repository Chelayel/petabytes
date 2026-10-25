<img src="docs/logo/logo.svg" width="72" alt="Petabytes logo: a little critter between curly braces">

# Petabytes

Small companions with a big appetite. They keep you company while you code, in VS Code, JetBrains IDEs and on your Mac, and react to what you're doing. Pick one:

- **Tide**, sea creatures that swim: **Shelly** the sea turtle, **Bloop** the jellyfish, **Inky** the octopus, **Pinchy** the crab, **Puff** the pufferfish, **Blue** the whale, **Clem** the clownfish, **Sandy** the seahorse, **Finn** the shark, **Splash** the dolphin, **Angie** the angelfish or **Indigo** the blue tang.
- **Home**, pets that walk: **Biscuit** the golden retriever, **Byte** the cat, **Clover** the bunny or **Nugget** the hamster.
- **Snacks**, food with feet: **Patty** the burger, **Nori** the sushi, **Pepe** the pizza, **Sprinkles** the donut or **Tuesday** the taco.
- **Games**, original pixel-art characters: **Squish** the slime, **Boo** the ghost, **Sir Pix** the knight or **Bolt** the robot. They say "+1 coin!" when you save, "LEVEL UP!" when you fix every error and "GAME OVER" when tests fail.
- **Gadgets**, the things on your desk: **Lappy** the laptop, **Joy** the controller, **Java** the coffee mug, **Quackers** the rubber duck (who helps when you debug), **Spike** the cactus, **Floppy** the floppy disk, **Click** the mouse, **Beats** the headphones or **Post** the sticky note.

![Shelly swimming faster while you type, worrying about an error and celebrating the fix; Byte the cat hiding from failed tests; Patty the burger eating a curly brace; Sir Pix the knight napping and waking up](docs/demo.gif)

![All thirty-four pets](docs/pets.png)

## Which one do I need?

There are three, and they don't depend on each other:

- **In your editor**, to react to your code (saves, errors, tests, runs, debugging, commits): install the plugin in each IDE you use, the [VS Code extension](https://marketplace.visualstudio.com/items?itemName=chelayel.petabytes) or the [JetBrains plugin](https://plugins.jetbrains.com/search?search=petabytes). The pet lives inside that IDE.
- **On your Mac desktop**, to react to your Mac (the app in front, typing, battery, Wi-Fi, downloads, screenshots): [the Mac app](#on-your-mac). It walks along your Dock, but it can't see your code; for that, add the editor plugin too.

## In your editor

| You | Your pet |
| --- | --- |
| Type | Swims faster |
| Save | Does a happy loop and blows bubbles |
| Add errors to the open file | Looks worried; hides when several appear at once (Inky inks, Puff puffs up) |
| Fix all the errors | Celebrates |
| Run a task or run configuration | Cheers when it passes, hides when it fails |
| Run the app | Spins: "It's alive!" |
| Debug | Brings out a magnifying glass |
| Open your AI assistant, or a big block of code appears at once | "Did an AI write that? I won't tell." |
| Open the terminal; run `git push`, tests, installs, `rm -rf` (VS Code) | "Command line time!", "Ship it!", "Fingers crossed!", hides |
| Commit, switch branches | Celebrates, or notices the new branch |
| Undo several times in a row | "Rewinding time?" |
| Switch files | Looks around |
| Code late at night, early in the morning, or for hours | "It's late. The tide's out.", "Stretch break?" (Home pets say it their own way) |
| Step away for 3 minutes | Naps |
| Click it / double-click it | Does a spin / shows hearts |

**Feed it.** Use **Feed Pet** (the ♥ on the VS Code panel, or right-click the pet in IntelliJ) and a snack sinks down: `{ }`, `[ ]`, `( )`, `< >` or `;`. Your pet swims over and eats it. Every 20th `{` you type drops a crumb too, and a pet that hasn't eaten in an hour asks for one.

![Pets reacting to typing, fixed errors, a new error, failed tests, debugging and being left alone](docs/moods.png)

In IntelliJ IDEA, the pet swims up and down a strip at the editor's right edge, beside the scrollbar and out of the way of your code (or along the bottom edge, if you prefer):

![Patty the burger at the right edge of the editor in IntelliJ IDEA, saying "All clear!"](docs/intellij-right-edge.png)

In VS Code, the pet lives in a **Petabytes** panel in the Explorer:

![Pepe the pizza in the Petabytes panel in VS Code, eating a curly brace](docs/vscode-panel.png)

| Editor | Folder | Where the pet lives | Choose, show or hide |
| --- | --- | --- | --- |
| VS Code | [`vscode/`](vscode/) | A **Petabytes** panel in the Explorer (VS Code doesn't let extensions draw over the editor) | **Petabytes: Choose Pet** / **Toggle Pet**, or the `petabytes.*` settings |
| JetBrains (2024.2+) | [`intellij/`](intellij/) | Swimming up and down the editor's right edge, or along its bottom edge. Drag it to move it; it fades and lets clicks through when your cursor is right beside it | Right-click the pet or **Tools → Petabytes**; position, size and name in **Settings → Tools → Petabytes** |
| Mac (macOS 13+) | [`mac/`](mac/) | Standing on top of the Dock, or floating wherever you drag it; or, after **Move to Dock**, inside its own Dock icon | Right-click the pet, or the paw in the menu bar (the Dock icon, once moved there) |

## On your Mac

Download `Petabytes-<version>.dmg` from the [latest release](https://github.com/Chelayel/petabytes/releases/latest) and drag Petabytes to Applications. It isn't notarized yet, so the first time, right-click it and choose **Open**.

The pet walks along the top of your Dock, out of the way: clicks go through everywhere except on the pet itself. Drag it off the Dock to float it anywhere. **Move to Dock** puts it inside its own Dock icon instead, where you can keep it: it stays animated, a little bubble shows how it feels (z, !, ♥, ?) or that it's talking, and clicking the icon feeds it.

![Bolt the robot standing on top of the Dock](docs/mac-walking.png) ![Inky the octopus living inside its own Dock icon](docs/mac-dock.png)

**Choose Pet…** opens a picker, a tab per set:

![The Choose a Pet window, showing the Games set](docs/mac-picker.png)
 It steps aside while an app is full screen (**Hide in Full Screen**, on by default).

It reacts to your Mac, and none of it asks for a permission:

| Your Mac | Your pet |
| --- | --- |
| You type, step away, come back, unlock | Gets excited, naps, wakes up, "Welcome back!" |
| You switch to a terminal, an editor, an AI app, a browser, chat, mail, a design or notes app, a calendar, a game, a video player, Docker, a database client, the simulator, Activity Monitor, a password manager... | "Command line time!", "Code time!", "Just one tab, right?", "Inbox zero?", "Careful with that DROP TABLE.", "*covers eyes*"... |
| Zoom, Teams or FaceTime | "A call? I'll be quiet." and hides |
| Battery low, plugged in | "Battery's low. Got a charger?", "Ahh, power." |
| Wi-Fi drops, comes back | Hides, then "We're back online!" |
| A download finishes, you take a screenshot, you copy something | "Download done!", "Cheese!", "Copy-paste? I saw nothing." |
| The Mac heats up, switches to dark mode | "It's getting hot in here.", "Lights out!" |

It only ever learns *that* a key was pressed, never which, and *that* the clipboard changed, never what's on it. It draws at 20 frames a second (fewer while it sleeps, almost none while the screen is locked).

## How it's built

Every pet is described once, in [`web/pets.json`](web/pets.json) (generated by [`tools/pets.py`](tools/pets.py)): shapes in a 120x80 box, grouped so each mood can pose a group, with parts that paddle, pulse or sway, and each pet's lines. Two small renderers draw it:

- **VS Code** ([`web/pet.html`](web/pet.html), hosted by [`vscode/extension.js`](vscode/extension.js)): SVG in a webview; the extension posts what you're doing.
- **JetBrains** ([`intellij/`](intellij/)): native Java2D in a layer over the editor (`pet/PetArt.kt`, `PetBrain.kt`, `PetPainter.kt`), fed by IDE listeners in `PetService.kt`.
- **Mac** ([`mac/`](mac/)): the same `web/pet.html` in a see-through, click-through panel (`PetWindow.swift`), fed by what the Mac reports in `Signals.swift`.

Adding a pet means adding it to `tools/pets.py`; every renderer picks it up (VS Code also lists it in `vscode/package.json` and `extension.js`). `./gradlew renderPreview` in `intellij/` draws every pet in every mood with the JetBrains painter, headlessly:

![Every pet in every mood, drawn by the JetBrains painter](docs/intellij-moods.png)

`python3 tools/gallery.py` redraws this README's pictures of the pets and their moods from `web/pet.html`, in headless Chrome.

Run locally:

```
python3 tools/pets.py > web/pets.json          # after changing the art
cd vscode && npx @vscode/vsce package           # petabytes-<version>.vsix
cd intellij && ./gradlew runIde                 # an IDE sandbox with the plugin
mac/build.sh && open mac/build/Petabytes.app    # the Mac app, and mac/build/Petabytes-<version>.dmg
```

## Support

Petabytes is free. If it makes you smile while you code, you can [buy me a coffee](https://buymeacoffee.com/chelayel) ☕

## License

MIT. Built by [Chelayel](https://www.chelayel.com).
