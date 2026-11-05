import Foundation
import Observation

/// Inlogstatus van de app. Het token staat in de keychain; bij een 401 van de server word je uitgelogd.
@MainActor @Observable
final class Session {
    private(set) var token: String?
    private(set) var booting = true
    private(set) var devAuth = false
    /// Naam uit Sign in with Apple. Apple geeft die alleen de eerste keer; daarom bewaren we hem op dit toestel.
    private(set) var displayName: String? = UserDefaults.standard.string(forKey: "profile.name")
    var isAuthed: Bool { token != nil }

    init() {
        token = Keychain.read("access_token")
        APIClient.shared.token = token
        APIClient.shared.onUnauthorized = { [weak self] in Task { @MainActor in self?.logout() } }
    }

    func boot() async {
        if token != nil {
            do { _ = try await APIClient.shared.me() }
            catch let error as APIError where error.status == 401 { logout() }
            catch { /* offline: je blijft ingelogd */ }
        }
        if let health = try? await APIClient.shared.health() { devAuth = health.devAuth }
        booting = false
        await PushManager.shared.refresh()
    }

    func signIn(appleToken: String, email: String?, name: String?) async throws {
        set(try await APIClient.shared.appleLogin(identityToken: appleToken, email: email).accessToken)
        if let name, !name.isEmpty { saveName(name) }
    }

    func signInDev() async throws {
        set(try await APIClient.shared.devLogin().accessToken)
        saveName("Ontwikkelaar")
    }

    func logout() {
        set(nil)
        saveName(nil)
    }

    private func saveName(_ name: String?) {
        displayName = name
        UserDefaults.standard.set(name, forKey: "profile.name")
    }

    private func set(_ value: String?) {
        token = value
        APIClient.shared.token = value
        Keychain.write("access_token", value)
        if value != nil { Task { await PushManager.shared.syncWithServer() } }
    }
}
