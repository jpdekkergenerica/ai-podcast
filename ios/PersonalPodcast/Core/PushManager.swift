import SwiftUI
import UIKit
import UserNotifications
import Observation

/// Pushmeldingen: toestemming vragen, het APNs-token ophalen en aan de server doorgeven.
@MainActor @Observable
final class PushManager {
    static let shared = PushManager()
    private let tokenKey = "apns.token"
    private(set) var status: UNAuthorizationStatus = .notDetermined
    private(set) var token: String?

    private init() { token = UserDefaults.standard.string(forKey: tokenKey) }

    func refresh() async {
        status = await UNUserNotificationCenter.current().notificationSettings().authorizationStatus
        if status == .authorized || status == .provisional { UIApplication.shared.registerForRemoteNotifications() }
    }

    func enable() async {
        _ = try? await UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge])
        await refresh()
    }

    func didRegister(token: String) {
        self.token = token
        UserDefaults.standard.set(token, forKey: tokenKey)
        Task { await syncWithServer() }
    }

    /// Koppelt dit toestel aan het ingelogde account (zodat meldingen hier aankomen).
    func syncWithServer() async {
        guard let token, APIClient.shared.token != nil else { return }
        _ = try? await APIClient.shared.registerDevice(token: token)
    }
}

final class AppDelegate: NSObject, UIApplicationDelegate {
    func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        let token = deviceToken.map { String(format: "%02x", $0) }.joined()
        Task { @MainActor in PushManager.shared.didRegister(token: token) }
    }

    func application(_ application: UIApplication, didFailToRegisterForRemoteNotificationsWithError error: Error) {}
}
