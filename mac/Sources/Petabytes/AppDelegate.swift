import AppKit
import ServiceManagement

/**
 Petabytes for Mac: a pet that swims along the top of your Dock and reacts to what your Mac is doing.
 It lives in the menu bar rather than the Dock; its menu is there and on the pet, by right-click.
 */
final class AppDelegate: NSObject, NSApplicationDelegate, NSMenuDelegate {
    private var window: PetWindow!
    private var signals: Signals!
    private var statusItem: NSStatusItem!

    private static let sizes: [(String, CGFloat)] = [("Small", 1.0), ("Medium", 1.3), ("Large", 1.7)]

    func applicationDidFinishLaunching(_ notification: Notification) {
        window = PetWindow()
        window.menuProvider = { [unowned self] in self.petMenu() }
        window.zoom = CGFloat(UserDefaults.standard.object(forKey: "size") as? Double ?? 1.3)
        if Settings.visible { window.orderFrontRegardless() }

        signals = Signals { [weak self] message in self?.window.send(message) }
        signals.start()

        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        statusItem.autosaveName = "Petabytes"
        statusItem.button?.image = NSImage(systemSymbolName: "pawprint.fill", accessibilityDescription: "Petabytes")
        let menu = NSMenu()
        menu.delegate = self
        statusItem.menu = menu
    }

    // ---- Menus -------------------------------------------------------------

    /** The menu-bar menu is rebuilt each time it opens, so its checkmarks are current. */
    func menuNeedsUpdate(_ menu: NSMenu) {
        menu.items = petMenu().items.map { item in
            item.menu?.removeItem(item)
            return item
        }
    }

    /** The same menu in the menu bar and on the pet. */
    private func petMenu() -> NSMenu {
        let menu = NSMenu()
        menu.addItem(item("Feed \(petName())", #selector(feed)))

        let choose = NSMenu()
        let catalog = Catalog.shared
        for id in catalog.order {
            guard let pet = catalog.pets[id] else { continue }
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
        let dock = item("Swim Along the Dock", #selector(swimAlongDock))
        dock.state = Settings.place == .dock ? .on : .off
        menu.addItem(dock)
        let float = item("Float Freely", #selector(floatFreely))
        float.state = Settings.place == .float ? .on : .off
        menu.addItem(float)

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
        menu.addItem(item(Settings.visible ? "Hide Pet" : "Show Pet", #selector(toggleVisible)))

        menu.addItem(.separator())
        let login = item("Open at Login", #selector(toggleLogin))
        login.state = SMAppService.mainApp.status == .enabled ? .on : .off
        menu.addItem(login)
        menu.addItem(item("Quit Petabytes", #selector(NSApplication.terminate(_:)), key: "q"))
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
        window.send(["type": "feed", "key": "feed"])
    }

    @objc private func choosePet(_ sender: NSMenuItem) {
        guard let id = sender.representedObject as? String else { return }
        Settings.pet = id
        Settings.name = ""
        window.configure()
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
        if visible { window.orderFrontRegardless() } else { window.orderOut(nil) }
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
