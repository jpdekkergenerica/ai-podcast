import Foundation
import Observation

/// Inlogstatus van de app. Het token staat in de keychain; bij een 401 van de server word je uitgelogd.
@MainActor @Observable
final class Session {
    private(set) var token: String?
    private(set) var booting = true
    private(set) var devAuth = false
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

    func signIn(appleToken: String, email: String?) async throws {
        set(try await APIClient.shared.appleLogin(identityToken: appleToken, email: email).accessToken)
    }

    func signInDev() async throws { set(try await APIClient.shared.devLogin().accessToken) }

    func logout() {
        set(nil)
    }

    private func set(_ value: String?) {
        token = value
        APIClient.shared.token = value
        Keychain.write("access_token", value)
        if value != nil { Task { await PushManager.shared.syncWithServer() } }
    }
}
