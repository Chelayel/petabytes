import AppKit
import ServiceManagement

/**
 Petabytes for Mac: a pet that walks along the top of your Dock and reacts to what your Mac is doing.
 Its icon is in the menu bar, or, after Move to Dock, the pet itself lives in its Dock icon (where it can be
 kept; clicking it feeds the pet). The menu is on that icon and on the pet, by right-click.
 */
final class AppDelegate: NSObject, NSApplicationDelegate, NSMenuDelegate {
    private var window: PetWindow!
    private var signals: Signals!
    private var statusItem: NSStatusItem!
    private let dockPet = DockPet()
    private let speech = DockSpeech()
    private let picker = PetPicker()

    private static let sizes: [(String, CGFloat)] = [("Small", 1.0), ("Medium", 1.3), ("Large", 1.7)]

    func applicationDidFinishLaunching(_ notification: Notification) {
        window = PetWindow()
        window.menuProvider = { [unowned self] in self.petMenu(withQuit: true) }
        window.zoom = CGFloat(UserDefaults.standard.object(forKey: "size") as? Double ?? 1.3)

        picker.onChoose = { [unowned self] id in self.choose(id) }
        picker.onRename = { [unowned self] in self.window.configure() }

        signals = Signals { [weak self] message in self?.send(message) }
        signals.start()

        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        statusItem.autosaveName = "Petabytes"
        statusItem.button?.image = NSImage(systemSymbolName: "pawprint.fill", accessibilityDescription: "Petabytes")
        let menu = NSMenu()
        menu.delegate = self
        statusItem.menu = menu
        applyDockIcon()
        // open -a Petabytes --args --choose-pet: start with the picker open.
        if CommandLine.arguments.contains("--choose-pet") { picker.show() }
        // A full menu bar (on a MacBook, whatever doesn't fit beside the notch) hides new items without a word.
        // Then the app shows its icon in the Dock too, so its menu can always be found.
        DispatchQueue.main.asyncAfter(deadline: .now() + 2) { [weak self] in
            guard let self, !Settings.showInDock, let button = self.statusItem.button,
                  button.window?.occlusionState.contains(.visible) != true else { return }
            NSApp.setActivationPolicy(.regular)
        }
    }

    /** Where the Mac's news goes: the pet on the Dock (its web page), or the one in the Dock icon. */
    private func send(_ message: [String: Any]) {
        if Settings.showInDock { dockPet.receive(message) } else { window.send(message) }
    }

    // ---- Dock icon ---------------------------------------------------------

    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        if !Settings.showInDock && !Settings.visible { setVisible(true) }
        feed()
        return false
    }

    func applicationDockMenu(_ sender: NSApplication) -> NSMenu? {
        petMenu(withQuit: false) // the Dock adds its own Quit
    }

    /**
     In the menu bar, the pet walks along the Dock (or floats), drawn by web/pet.html. Moved to the Dock, it lives
     inside its own Dock icon instead, drawn natively; its window and web page are put away meanwhile.
     */
    private func applyDockIcon() {
        let inDock = Settings.showInDock
        NSApp.setActivationPolicy(inDock ? .regular : .accessory)
        statusItem.isVisible = !inDock
        window.wanted = !inDock && Settings.visible
        if inDock {
            window.orderOut(nil)
            dockPet.onSay = { [weak self] line in self?.speech.say(line) }
            dockPet.start()
        } else {
            dockPet.stop()
            speech.hide()
            if Settings.visible { window.orderFrontRegardless() }
        }
    }

    // ---- Menus -------------------------------------------------------------

    /** The menu-bar menu is rebuilt each time it opens, so its checkmarks are current. */
    func menuNeedsUpdate(_ menu: NSMenu) {
        menu.items = petMenu(withQuit: true).items.map { item in
            item.menu?.removeItem(item)
            return item
        }
    }

    /** The same menu in the menu bar, on the pet and on the Dock icon. */
    private func petMenu(withQuit: Bool) -> NSMenu {
        let menu = NSMenu()
        menu.addItem(item("Feed \(petName())", #selector(feed)))

        menu.addItem(item("Choose Pet…", #selector(showPicker)))

        menu.addItem(.separator())
        if !Settings.showInDock {
            let dock = item("Swim Along the Dock", #selector(swimAlongDock))
            dock.state = Settings.place == .dock ? .on : .off
            menu.addItem(dock)
            let float = item("Float Freely", #selector(floatFreely))
            float.state = Settings.place == .float ? .on : .off
            menu.addItem(float)
        }

        let sizes = NSMenu()
        for (index, (title, zoom)) in Self.sizes.enumerated() {
            let entry = item(title, #selector(chooseSize(_:)))
            entry.tag = index
            entry.state = abs(window.zoom - zoom) < 0.01 ? .on : .off
            sizes.addItem(entry)
        }
        let sizeItem = NSMenuItem(title: "Size", action: nil, keyEquivalent: "")
        sizeItem.submenu = sizes
        menu.addItem(sizeItem)
        if !Settings.showInDock { menu.addItem(item(Settings.visible ? "Hide Pet" : "Show Pet", #selector(toggleVisible))) }

        menu.addItem(.separator())
        menu.addItem(item(Settings.showInDock ? "Move to Menu Bar" : "Move to Dock", #selector(toggleShowInDock)))
        if Settings.showInDock {
            let talk = item("Talk Above the Dock Icon", #selector(toggleTalkInDock))
            talk.state = Settings.talkInDock && DockSpeech.allowed ? .on : .off
            menu.addItem(talk)
        }
        let fullScreen = item("Hide in Full Screen", #selector(toggleHideInFullScreen))
        fullScreen.state = Settings.hideInFullScreen ? .on : .off
        menu.addItem(fullScreen)
        let login = item("Open at Login", #selector(toggleLogin))
        login.state = SMAppService.mainApp.status == .enabled ? .on : .off
        menu.addItem(login)
        menu.addItem(.separator())
        menu.addItem(item("Buy Me a Coffee…", #selector(buyCoffee)))
        if withQuit { menu.addItem(item("Quit Petabytes", #selector(NSApplication.terminate(_:)), key: "q")) }
        return menu
    }

    private func item(_ title: String, _ action: Selector, key: String = "") -> NSMenuItem {
        let item = NSMenuItem(title: title, action: action, keyEquivalent: key)
        item.target = action == #selector(NSApplication.terminate(_:)) ? NSApp : self
        return item
    }

    private func petName() -> String {
        Settings.name.isEmpty ? Catalog.shared.pets[Settings.pet]?.name ?? "Pet" : Settings.name
    }

    // ---- Actions -----------------------------------------------------------

    @objc private func feed() {
        send(["type": "feed", "key": "feed"])
    }

    @objc private func showPicker() { picker.show() }

    @objc private func buyCoffee() {
        NSWorkspace.shared.open(URL(string: "https://buymeacoffee.com/chelayel")!)
    }

    private func choose(_ id: String) {
        Settings.pet = id
        Settings.name = ""
        window.configure()
        dockPet.choose(id)
    }

    @objc private func swimAlongDock() { move(to: .dock) }
    @objc private func floatFreely() { move(to: .float) }

    private func move(to place: Place) {
        Settings.place = place
        window.place()
    }

    @objc private func chooseSize(_ sender: NSMenuItem) {
        let zoom = Self.sizes[sender.tag].1
        UserDefaults.standard.set(Double(zoom), forKey: "size")
        window.zoom = zoom
    }

    @objc private func toggleVisible() { setVisible(!Settings.visible) }

    private func setVisible(_ visible: Bool) {
        Settings.visible = visible
        window.wanted = visible && !Settings.showInDock
        if visible || Settings.showInDock { window.orderFrontRegardless() } else { window.orderOut(nil) }
    }

    @objc private func toggleShowInDock() {
        Settings.showInDock.toggle()
        applyDockIcon()
        if Settings.showInDock && Settings.talkInDock && !DockSpeech.allowed && !Settings.askedForAccessibility {
            askForAccessibility()
        }
    }

    @objc private func toggleTalkInDock() {
        if Settings.talkInDock && DockSpeech.allowed {
            Settings.talkInDock = false
            speech.hide()
        } else {
            Settings.talkInDock = true
            if !DockSpeech.allowed { askForAccessibility() }
        }
    }

    /** Says why, then lets macOS ask: its prompt leads to Privacy & Security, where Petabytes gets switched on. */
    private func askForAccessibility() {
        Settings.askedForAccessibility = true
        let alert = NSAlert()
        alert.messageText = "Let your pet talk above its Dock icon?"
        alert.informativeText = "To put a speech bubble above its icon, Petabytes needs to know where the icon is in the Dock, and macOS only tells apps that through the Accessibility permission. Petabytes uses it for nothing else.\n\nIn System Settings, switch on Petabytes under Privacy & Security → Accessibility. Until then, your pet still shows how it feels in the corner of its icon."
        alert.addButton(withTitle: "Continue")
        alert.addButton(withTitle: "Not Now")
        NSApp.activate(ignoringOtherApps: true)
        guard alert.runModal() == .alertFirstButtonReturn else { return }
        DockSpeech.requestAccess()
    }

    @objc private func toggleHideInFullScreen() {
        Settings.hideInFullScreen.toggle()
        window.checkFullScreen()
    }

    @objc private func toggleLogin() {
        let service = SMAppService.mainApp
        do {
            if service.status == .enabled { try service.unregister() } else { try service.register() }
        } catch {
            let alert = NSAlert()
            alert.messageText = "Couldn't change Open at Login"
            alert.informativeText = "Move Petabytes to your Applications folder and try again. (\(error.localizedDescription))"
            NSApp.activate(ignoringOtherApps: true)
            alert.runModal()
        }
    }
}
