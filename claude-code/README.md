# Petabytes for Claude Code

Lets your Petabytes pets react to what Claude does. The pet on your Dock (the [Petabytes Mac app](https://github.com/Chelayel/petabytes)),
in VS Code and in IntelliJ gets curious when Claude reads files, excited when it edits code, crosses its
fingers when tests run and cheers or hides at the result, celebrates a push, and says "Done!" when Claude
finishes. The add-on tells the Mac app on 127.0.0.1, and leaves the latest event in `~/.petabytes/claude-code.json`
for the editors to read; nothing leaves your computer.

It can also show a small pixel-art pet above your prompt: `/pet on` turns it on and `/pet off` turns it off.
`/pet loopee` (or any of the 35 pets, by name or kind) chooses that one.

## Install

At the prompt of a Claude Code session:

```
/plugin install petabytes --marketplace Chelayel/petabytes
```

Answer `y` to add the marketplace, then pick a scope. From a shell: `claude plugin install petabytes --marketplace Chelayel/petabytes`.

For a pet to react, have one running: the [Mac app](https://github.com/Chelayel/petabytes/releases/latest) (with **React to Claude Code** on in its menu), or the Petabytes extension for [VS Code](https://marketplace.visualstudio.com/items?itemName=chelayel.petabytes) or [IntelliJ](https://plugins.jetbrains.com/plugin/35446-petabytes), 1.6.0 or later.

Part of [Petabytes](https://github.com/Chelayel/petabytes). MIT licensed. `tools/claude_sprites.py` redraws the pixel-art pets in `hooks/sprites.ts` from `web/pets.json`.
