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

    private static let sizes: [(String, CGFloat)] = [("Small", 1.0), ("Medium", 1.3), ("Large", 1.7)]
    private static let sets = ["tide": "Tide", "home": "Home", "snacks": "Snacks", "games": "Games"]

    func applicationDidFinishLaunching(_ notification: Notification) {
        window = PetWindow()
        window.menuProvider = { [unowned self] in self.petMenu(withQuit: true) }
        window.zoom = CGFloat(UserDefaults.standard.object(forKey: "size") as? Double ?? 1.3)

        signals = Signals { [weak self] message in self?.send(message) }
        signals.start()

        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        statusItem.autosaveName = "Petabytes"
        statusItem.button?.image = NSImage(systemSymbolName: "pawprint.fill", accessibilityDescription: "Petabytes")
        let menu = NSMenu()
        menu.delegate = self
        statusItem.menu = menu
        applyDockIcon()
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
            dockPet.start()
        } else {
            dockPet.stop()
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

        let choose = NSMenu()
        let catalog = Catalog.shared
        var lastSet: String?
        for id in catalog.order {
            guard let pet = catalog.pets[id] else { continue }
            if pet.set != lastSet, let set = pet.set {
                if lastSet != nil { choose.addItem(.separator()) }
                choose.addItem(Self.header(Self.sets[set] ?? set.capitalized))
                lastSet = set
            }
            let entry = item("\(pet.name) the \((pet.label ?? id).lowercased())", #selector(choosePet(_:)))
            entry.representedObject = id
            entry.state = id == Settings.pet ? .on : .off
            choose.addItem(entry)
        }
        let chooseItem = NSMenuItem(title: "Choose Pet", action: nil, keyEquivalent: "")
        chooseItem.submenu = choose
        menu.addItem(chooseItem)
        menu.addItem(item("Rename…", #selector(rename)))

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
        let fullScreen = item("Hide in Full Screen", #selector(toggleHideInFullScreen))
        fullScreen.state = Settings.hideInFullScreen ? .on : .off
        menu.addItem(fullScreen)
        let login = item("Open at Login", #selector(toggleLogin))
        login.state = SMAppService.mainApp.status == .enabled ? .on : .off
        menu.addItem(login)
        if withQuit { menu.addItem(item("Quit Petabytes", #selector(NSApplication.terminate(_:)), key: "q")) }
        return menu
    }

    private static func header(_ title: String) -> NSMenuItem {
        if #available(macOS 14, *) { return .sectionHeader(title: title) }
        let item = NSMenuItem(title: title, action: nil, keyEquivalent: "")
        item.isEnabled = false
        return item
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

    @objc private func choosePet(_ sender: NSMenuItem) {
        guard let id = sender.representedObject as? String else { return }
        Settings.pet = id
        Settings.name = ""
        window.configure()
        dockPet.choose(id)
    }

    @objc private func rename() {
        let alert = NSAlert()
        alert.messageText = "Rename \(petName())"
        alert.informativeText = "Leave it empty for the pet's own name."
        let field = NSTextField(frame: NSRect(x: 0, y: 0, width: 240, height: 24))
        field.stringValue = Settings.name
        alert.accessoryView = field
        alert.addButton(withTitle: "Rename")
        alert.addButton(withTitle: "Cancel")
        alert.window.initialFirstResponder = field
        NSApp.activate(ignoringOtherApps: true)
        guard alert.runModal() == .alertFirstButtonReturn else { return }
        Settings.name = field.stringValue.trimmingCharacters(in: .whitespaces)
        window.configure()
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
