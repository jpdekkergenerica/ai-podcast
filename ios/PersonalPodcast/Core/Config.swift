import Foundation

enum Config {
    /// Basisadres van de server (project.yml: API_BASE_URL).
    static var apiBase: URL {
        // Voor testen: start de app met `-API_BASE_URL_OVERRIDE http://127.0.0.1:8000` om een andere server te gebruiken.
        if let override = UserDefaults.standard.string(forKey: "API_BASE_URL_OVERRIDE"), let url = URL(string: override) { return url }
        let raw = Bundle.main.object(forInfoDictionaryKey: "API_BASE_URL") as? String ?? ""
        return URL(string: raw.isEmpty ? "https://www.yourownpod.com" : raw)!
    }
}
