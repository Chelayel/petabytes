# Tide Pets

Shelly the sea turtle keeps you company while you code, in VS Code and JetBrains IDEs, and reacts to what you're doing:

| You | Shelly |
| --- | --- |
| Type | Swims faster |
| Save | Does a happy loop and blows bubbles |
| Add errors to the open file | Looks worried; hides in her shell when several appear at once |
| Fix all the errors | Celebrates |
| Run a task or run configuration | Cheers when it passes, hides when it fails |
| Debug | Brings out a magnifying glass |
| Switch files | Looks around |
| Step away for 3 minutes | Naps on the sand |
| Click her | Does a spin |

Made to go with the [Midnight Tide](https://github.com/Chelayel/Midnight-Tide) theme, and works with any theme.

| Editor | Folder | Where Shelly lives | Turn on or off |
| --- | --- | --- | --- |
| VS Code | [`vscode/`](vscode/) | A **Tide Pets** panel in the Explorer | **Tide Pets: Toggle Pet** in the Command Palette, or the `tidePets.enabled` setting |
| JetBrains (2024.2+) | [`intellij/`](intellij/) | A **Tide Pets** tool window | **Tools → Show Tide Pet** |

Rename her with the `tidePets.name` setting in VS Code.

## How it's built

The pet is one page, [`web/pet.html`](web/pet.html): an SVG turtle, CSS animations and a small script. Each IDE shows it in a web view and sends it events:

- **VS Code** ([`vscode/extension.js`](vscode/extension.js)): a webview view; events arrive with `postMessage`. The page is copied into `vscode/media/` when the extension is packaged.
- **JetBrains** ([`intellij/`](intellij/)): a JCEF browser in a tool window; events arrive with `window.tidePets.receive(...)`. The page is copied into the plugin's resources at build.

Run locally:

```
cd vscode && npx @vscode/vsce package           # tide-pets-<version>.vsix
cd intellij && ./gradlew runIde                 # an IDE sandbox with the plugin
```

## Publishing

A tag publishes both at the tag's version:

```
git tag v0.1.0 && git push origin v0.1.0
```

[`release.yml`](.github/workflows/release.yml) builds and verifies the JetBrains plugin and the VS Code extension, attaches both to a GitHub release, and uploads each to its marketplace only when that marketplace doesn't already have the version, so re-running a tag is safe. A push to `main` that touches either IDE or the page builds them as a check and publishes nothing. Bump `pluginVersion` in `intellij/gradle.properties` and `version` in `vscode/package.json` alongside the tag.

The JetBrains Marketplace only accepts updates through its API: upload the first version by hand at https://plugins.jetbrains.com/plugin/add, using the zip from the release. The VS Code Marketplace creates the extension on its first automated upload.

Store tokens are repository secrets (`gh secret set NAME`, value on standard input):

| Secret | For |
| --- | --- |
| `JETBRAINS_MARKETPLACE_TOKEN` | JetBrains Marketplace, a token from https://plugins.jetbrains.com/author/me/tokens |
| `VSCE_PAT` | VS Code Marketplace, an Azure DevOps PAT with *Marketplace: Manage* on all accessible organizations (retired by Microsoft on 2026-12-01) |
| `AZURE_CLIENT_ID`, `AZURE_TENANT_ID` | VS Code Marketplace through a managed identity instead of the PAT; its federated credential must trust this repository's `marketplace-publish` environment |
| `OVSX_PAT` | Open VSX, optional |

A missing token skips that store with a warning.

## License

MIT. Built by [Chelayel](https://www.chelayel.com).
