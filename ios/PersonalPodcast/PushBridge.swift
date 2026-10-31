import UIKit
import UserNotifications

/// Pushmeldingen voor de webpagina: `status` leest de toestemming, `register` vraagt toestemming en haalt het APNs-token op.
/// Antwoorden komen terug via `window.__pushResult({status, token?, error?})`.
final class PushBridge {
    static let shared = PushBridge()
    private let tokenKey = "apns.token"
    private var waiting: [(String?, String?) -> Void] = []

    private var savedToken: String? { UserDefaults.standard.string(forKey: tokenKey) }

    func handle(action: String, reply: @escaping ([String: Any]) -> Void) {
        let center = UNUserNotificationCenter.current()
        switch action {
        case "register":
            center.requestAuthorization(options: [.alert, .sound, .badge]) { granted, _ in
                guard granted else { return reply(["status": "denied"]) }
                self.waiting.append { token, error in
                    var payload: [String: Any] = ["status": "authorized"]
                    if let token { payload["token"] = token }
                    if let error { payload["error"] = error }
                    reply(payload)
                }
                DispatchQueue.main.async { UIApplication.shared.registerForRemoteNotifications() }
                // Zonder token (bijvoorbeeld in de simulator zonder signing) antwoorden we na een korte wachttijd.
                DispatchQueue.main.asyncAfter(deadline: .now() + 5) { self.flush(token: nil, error: "Geen token ontvangen") }
            }
        default:
            center.getNotificationSettings { settings in
                let status: String
                switch settings.authorizationStatus {
                case .authorized, .provisional, .ephemeral: status = "authorized"
                case .denied: status = "denied"
                default: status = "notDetermined"
                }
                var payload: [String: Any] = ["status": status]
                if status == "authorized", let token = self.savedToken { payload["token"] = token }
                reply(payload)
            }
        }
    }

    func didRegister(token: String) {
        UserDefaults.standard.set(token, forKey: tokenKey)
        flush(token: token, error: nil)
    }

    func didFail(_ message: String) { flush(token: nil, error: message) }

    private func flush(token: String?, error: String?) {
        let callbacks = waiting
        waiting.removeAll()
        callbacks.forEach { $0(token, error) }
    }
}
