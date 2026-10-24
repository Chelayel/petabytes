import AppKit
import SwiftUI

/**
 The Choose a Pet window: the pets as cards, a tab per set, and the pet's name. Choosing a card switches pets
 straight away; the window stays open so you can look around.
 */
final class PetPicker {
    private var window: NSWindow?
    /** A pet was chosen (its id). */
    var onChoose: (String) -> Void = { _ in }
    /** The name was changed; Settings.name has it. */
    var onRename: () -> Void = {}

    func show() {
        if window == nil {
            let view = PickerView(onChoose: { [weak self] in self?.onChoose($0) }, onRename: { [weak self] in self?.onRename() })
            let window = NSWindow(contentViewController: NSHostingController(rootView: view))
            window.title = "Choose a Pet"
            window.styleMask = [.titled, .closable]
            window.isReleasedWhenClosed = false
            window.center()
            self.window = window
        }
        NSApp.activate(ignoringOtherApps: true)
        window?.makeKeyAndOrderFront(nil)
    }
}

private struct PickerView: View {
    let onChoose: (String) -> Void
    let onRename: () -> Void

    private static let sets = [("tide", "Tide"), ("home", "Home"), ("snacks", "Snacks"), ("games", "Games")]
    /** Every pet's picture, drawn once. */
    private static let pictures: [String: NSImage] = Dictionary(uniqueKeysWithValues: Catalog.shared.order.map {
        ($0, PetArt.load($0).image(size: NSSize(width: 150, height: 100)))
    })

    @State private var selected = Settings.pet
    @State private var set = Catalog.shared.pets[Settings.pet]?.set ?? "tide"
    @State private var name = Settings.name

    var body: some View {
        VStack(spacing: 16) {
            Picker("Set", selection: $set) {
                ForEach(Self.sets, id: \.0) { Text($0.1).tag($0.0) }
            }
            .pickerStyle(.segmented)
            .labelsHidden()

            ScrollView {
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 140), spacing: 12)], spacing: 12) {
                    ForEach(Catalog.shared.order.filter { Catalog.shared.pets[$0]?.set == set }, id: \.self, content: card)
                }
                .padding(2)
            }

            HStack {
                Text("Name")
                TextField(Catalog.shared.pets[selected]?.name ?? "", text: $name)
                    .textFieldStyle(.roundedBorder)
                    .onSubmit(rename)
                Button("Done") {
                    rename()
                    NSApp.keyWindow?.close()
                }
                .keyboardShortcut(.defaultAction)
            }
            Text("Leave the name empty for the pet's own.")
                .font(.caption)
                .foregroundStyle(.secondary)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(20)
        .frame(width: 660, height: 560)
    }

    private func card(_ id: String) -> some View {
        let pet = Catalog.shared.pets[id]
        let chosen = id == selected
        return Button {
            selected = id
            name = ""
            onChoose(id)
        } label: {
            VStack(spacing: 4) {
                if let picture = Self.pictures[id] {
                    Image(nsImage: picture).resizable().scaledToFit().frame(height: 72)
                }
                Text(pet?.name ?? id).font(.headline)
                Text(pet?.label ?? "").font(.caption).foregroundStyle(.secondary)
            }
            .padding(10)
            .frame(maxWidth: .infinity)
            .contentShape(Rectangle())
            .background(RoundedRectangle(cornerRadius: 12).fill(chosen ? Color.accentColor.opacity(0.18) : Color.primary.opacity(0.05)))
            .overlay(RoundedRectangle(cornerRadius: 12).stroke(chosen ? Color.accentColor : .clear, lineWidth: 2))
        }
        .buttonStyle(.plain)
        .accessibilityLabel("\(pet?.name ?? id) the \(pet?.label?.lowercased() ?? id)")
    }

    private func rename() {
        Settings.name = name.trimmingCharacters(in: .whitespaces)
        onRename()
    }
}
