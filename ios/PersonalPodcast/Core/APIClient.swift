import Foundation

struct APIError: LocalizedError {
    var message: String
    var fields: [String: String] = [:]
    var status = 0
    var errorDescription: String? { message }
}

private struct AnyEncodable: Encodable {
    let value: Encodable
    func encode(to encoder: Encoder) throws { try value.encode(to: encoder) }
}

/// Spreekt de FastAPI-server aan. Het token komt uit de Session; een 401 meldt de Session dat er opnieuw ingelogd moet worden.
final class APIClient: @unchecked Sendable {
    static let shared = APIClient()
    var token: String?
    var onUnauthorized: (() -> Void)?

    private let decoder: JSONDecoder = {
        let d = JSONDecoder(); d.keyDecodingStrategy = .convertFromSnakeCase; return d
    }()
    private let encoder: JSONEncoder = {
        let e = JSONEncoder(); e.keyEncodingStrategy = .convertToSnakeCase; return e
    }()
    private let session: URLSession = {
        let c = URLSessionConfiguration.default
        c.timeoutIntervalForRequest = 60
        return URLSession(configuration: c)
    }()

    private func call<T: Decodable>(_ method: String, _ path: String, body: Encodable? = nil) async throws -> T {
        var request = URLRequest(url: URL(string: path, relativeTo: Config.apiBase)!)
        request.httpMethod = method
        if let body {
            request.httpBody = try encoder.encode(AnyEncodable(value: body))
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        }
        if let token { request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization") }
        let (data, response): (Data, URLResponse)
        do { (data, response) = try await session.data(for: request) }
        catch let error as URLError {
            let text = error.code == .notConnectedToInternet || error.code == .networkConnectionLost
                ? "Geen internetverbinding. Controleer je verbinding en probeer het opnieuw."
                : "De server is niet bereikbaar. Probeer het zo opnieuw."
            throw APIError(message: text)
        }
        let status = (response as? HTTPURLResponse)?.statusCode ?? 0
        guard (200..<300).contains(status) else {
            if status == 401, token != nil { onUnauthorized?() }
            throw Self.error(status: status, data: data)
        }
        do { return try decoder.decode(T.self, from: data) }
        catch { throw APIError(message: "Onverwacht antwoord van de server.", status: status) }
    }

    private static func error(status: Int, data: Data) -> APIError {
        if let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any], let detail = object["detail"] {
            if let text = detail as? String { return APIError(message: text, status: status) }
            if let dict = detail as? [String: Any] {
                return APIError(message: dict["message"] as? String ?? "Er ging iets mis.",
                                fields: dict["fields"] as? [String: String] ?? [:], status: status)
            }
            return APIError(message: "Controleer de ingevulde gegevens.", status: status)
        }
        return APIError(message: status >= 500 ? "De server is tijdelijk niet beschikbaar. Probeer het zo opnieuw." : "Er ging iets mis.", status: status)
    }

    // MARK: eindpunten

    func health() async throws -> Health { try await call("GET", "/health") }
    func devLogin() async throws -> TokenResponse {
        try await call("POST", "/auth/dev", body: ["apple_sub": "dev-user-ios", "email": "dev@example.com"])
    }
    func appleLogin(identityToken: String, email: String?) async throws -> TokenResponse {
        var body = ["identity_token": identityToken]
        if let email { body["email"] = email }
        return try await call("POST", "/auth/apple", body: body)
    }
    func me() async throws -> Me { try await call("GET", "/me") }
    func setNotifications(newEpisode: Bool? = nil, failed: Bool? = nil) async throws -> Me {
        var body: [String: Bool] = [:]
        if let newEpisode { body["notify_new"] = newEpisode }
        if let failed { body["notify_failed"] = failed }
        return try await call("PATCH", "/me/notifications", body: body)
    }
    func registerDevice(token: String) async throws -> Me { try await call("POST", "/me/devices", body: ["token": token]) }
    func deleteAccount() async throws -> Message { try await call("DELETE", "/me/account") }

    func podcasts() async throws -> [Podcast] { try await call("GET", "/me/podcasts") }
    func podcast(_ id: String) async throws -> Podcast { try await call("GET", "/me/podcasts/\(id)") }
    func createPodcast(_ body: PodcastBody) async throws -> Podcast { try await call("POST", "/me/podcasts", body: body) }
    func updatePodcast(_ id: String, _ body: PodcastBody) async throws -> Podcast { try await call("PATCH", "/me/podcasts/\(id)", body: body) }
    func deletePodcast(_ id: String) async throws -> Message { try await call("DELETE", "/me/podcasts/\(id)") }
    func pause(_ id: String) async throws -> Podcast { try await call("POST", "/me/podcasts/\(id)/pause", body: [String: String]()) }
    func resume(_ id: String) async throws -> Podcast { try await call("POST", "/me/podcasts/\(id)/resume", body: [String: String]()) }
    func rotateFeedToken(_ id: String) async throws -> Podcast { try await call("POST", "/me/podcasts/\(id)/rotate-feed-token", body: [String: String]()) }
    func setCover(_ id: String, jpeg: Data) async throws -> Podcast {
        try await call("POST", "/me/podcasts/\(id)/cover", body: ["image": "data:image/jpeg;base64," + jpeg.base64EncodedString()])
    }
    func deleteCover(_ id: String) async throws -> Podcast { try await call("DELETE", "/me/podcasts/\(id)/cover") }
    func episodes(_ id: String) async throws -> [EpisodeSummary] { try await call("GET", "/me/podcasts/\(id)/episodes") }
    func episode(_ id: String, guid: String) async throws -> Episode {
        let safe = guid.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? guid
        return try await call("GET", "/me/podcasts/\(id)/episodes/\(safe)")
    }
    func voices() async throws -> [Voice] { try await call("GET", "/me/voices") }
    func checkSource(_ url: String) async throws -> SourceCheck { try await call("POST", "/me/sources/check", body: ["url": url]) }
}
