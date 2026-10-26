# Petabytes for Claude Code

Lets your Petabytes pet react to what Claude does. With the [Petabytes Mac app](https://github.com/Chelayel/petabytes)
running, the pet on your Dock gets curious when Claude reads files, excited when it edits code, crosses its
fingers when tests run and cheers or hides at the result, celebrates a push, and says "Done!" when Claude
finishes. The add-on talks to the app on 127.0.0.1 only; with the app closed, nothing happens.

It can also show a small pixel-art pet above your prompt: `/pet on` turns it on and `/pet off` turns it off.
`/pet loopee` (or any of the 35 pets, by name or kind) chooses that one.

## Install

At the prompt of a Claude Code session:

```
/plugin install petabytes --marketplace Chelayel/petabytes
```

Answer `y` to add the marketplace, then pick a scope. From a shell: `claude plugin install petabytes --marketplace Chelayel/petabytes`.

For the full-size pet, also install the [Petabytes Mac app](https://github.com/Chelayel/petabytes/releases/latest) and leave **React to Claude Code** on in its menu.

Part of [Petabytes](https://github.com/Chelayel/petabytes). MIT licensed. `tools/claude_sprites.py` redraws the pixel-art pets in `hooks/sprites.ts` from `web/pets.json`.
