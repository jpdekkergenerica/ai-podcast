import SwiftUI

/// Scherm 8 · Account en meldingen: Apple-account, pushstatus en twee afzonderlijke meldingsvoorkeuren.
struct AccountView: View {
    @Environment(Session.self) private var session
    @State private var me: Me?
    @State private var push = PushManager.shared
    @State private var confirmDelete = false
    @State private var busy = false
    @State private var error: String?

    private var pushText: String {
        switch push.status {
        case .authorized, .provisional, .ephemeral: return me?.pushRegistered == true ? "Aan" : "Toegestaan, nog niet gekoppeld"
        case .denied: return "Geweigerd in Instellingen"
        default: return "Nog niet ingesteld"
        }
    }

    var body: some View {
        List {
            Section {
                HStack(spacing: 16) {
                    AvatarView(name: session.displayName, email: me?.email, size: 64)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(session.displayName ?? "Apple-account").font(.headline)
                        Text(me?.email ?? "Ingelogd met Apple").font(.subheadline).foregroundStyle(Theme.secondary)
                    }
                }
                .padding(.vertical, 4)
            }.listRowBackground(Theme.card)

            Section {
                LabeledContent("Pushmeldingen", value: pushText)
                Toggle("Nieuwe aflevering", isOn: Binding(get: { me?.notifyNew ?? true }, set: { v in Task { await set(newEpisode: v) } }))
                Toggle("Mislukte aflevering", isOn: Binding(get: { me?.notifyFailed ?? true }, set: { v in Task { await set(failed: v) } }))
                if push.status == .notDetermined || (push.status == .authorized && me?.pushRegistered == false) {
                    Button("Meldingen inschakelen") { Task { await enable() } }
                } else if push.status == .denied {
                    Button("Open Instellingen") { if let u = URL(string: UIApplication.openSettingsURLString) { UIApplication.shared.open(u) } }
                }
            } header: { Text("Meldingen") } footer: {
                Text("De status van elke podcast blijft altijd zichtbaar in de app, ook als je geen meldingen ontvangt.")
            }.listRowBackground(Theme.card)

            Section {
                Button("Uitloggen") { session.logout() }
                Button("Account verwijderen", role: .destructive) { confirmDelete = true }
                Link("Privacy", destination: Config.apiBase.appendingPathComponent("privacy"))
            }.listRowBackground(Theme.card)
        }
        .scrollContentBackground(.hidden)
        .background(Theme.background)
        .navigationTitle("Account")
        .task { await reload() }
        .confirmationDialog("Account verwijderen?", isPresented: $confirmDelete, titleVisibility: .visible) {
            Button("Verwijderen", role: .destructive) { Task { await delete() } }
            Button("Annuleren", role: .cancel) {}
        } message: { Text("Al je podcasts, afleveringen en feeds verdwijnen. Dit kun je niet terugdraaien.") }
        .errorAlert($error)
    }

    private func reload() async {
        await push.refresh()
        me = try? await APIClient.shared.me()
    }

    private func set(newEpisode: Bool? = nil, failed: Bool? = nil) async {
        if let newEpisode { me?.notifyNew = newEpisode }
        if let failed { me?.notifyFailed = failed }
        do { me = try await APIClient.shared.setNotifications(newEpisode: newEpisode, failed: failed) }
        catch { self.error = error.localizedDescription; me = try? await APIClient.shared.me() }
    }

    private func enable() async {
        await push.enable()
        await push.syncWithServer()
        me = try? await APIClient.shared.me()
    }

    private func delete() async {
        busy = true
        do { _ = try await APIClient.shared.deleteAccount(); session.logout() } catch { self.error = error.localizedDescription }
        busy = false
    }
}
