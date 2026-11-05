import Foundation

struct VoiceRef: Codable, Hashable {
    var voiceId: String
    var name: String
}

struct Topic: Decodable, Hashable, Identifiable {
    let id: String
    let text: String
}

struct SourceItem: Decodable, Hashable, Identifiable {
    let id: String
    let url: String
    let kind: String
    let name: String
    let error: String?
}

struct NextRun: Decodable, Hashable {
    let local: String
    let timezone: String
}

struct PodStatus: Decodable, Hashable {
    let code: String   // scheduled | running | published | failed | paused | skipped
    let label: String
    let detail: String
}

/// Planning van een podcast. `days`: 0 = maandag … 6 = zondag; `everyDays` is een eigen interval.
struct Schedule: Codable, Hashable {
    var enabled = true
    var days = [0, 1, 2, 3, 4, 5, 6]
    var everyDays: Int?
    var time = "07:00"
    var timezone = TimeZone.current.identifier

    enum CodingKeys: String, CodingKey { case enabled, days, everyDays, time, timezone }

    init() {}

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        enabled = try c.decodeIfPresent(Bool.self, forKey: .enabled) ?? true
        days = try c.decodeIfPresent([Int].self, forKey: .days) ?? [0, 1, 2, 3, 4, 5, 6]
        everyDays = try c.decodeIfPresent(Int.self, forKey: .everyDays)
        time = try c.decodeIfPresent(String.self, forKey: .time) ?? "07:00"
        timezone = try c.decodeIfPresent(String.self, forKey: .timezone) ?? TimeZone.current.identifier
    }

    func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(enabled, forKey: .enabled)
        try c.encode(days, forKey: .days)
        if let everyDays { try c.encode(everyDays, forKey: .everyDays) } else { try c.encodeNil(forKey: .everyDays) }
        try c.encode(time, forKey: .time)
        try c.encode(timezone, forKey: .timezone)
    }
}

struct Podcast: Decodable, Identifiable, Hashable {
    let id: String
    let title: String
    let coverUrl: String
    let hasCustomCover: Bool
    let topics: [Topic]
    let sources: [SourceItem]
    let durationMinutes: Int
    let voice: VoiceRef
    let style: String
    let schedule: Schedule
    let nextRun: NextRun?
    let status: PodStatus
    let paused: Bool
    let feedUrl: String
    let episodeCount: Int
}

struct EpisodeSummary: Decodable, Identifiable, Hashable {
    let guid: String
    let date: String
    let published: String
    let title: String
    let duration: Int
    let audioUrl: String
    var id: String { guid }
}

struct SourceLink: Decodable, Hashable {
    let title: String
    let link: String
    let source: String
}

struct SourceGroup: Decodable, Hashable {
    let topic: String
    let items: [SourceLink]
}

struct Episode: Decodable, Identifiable, Hashable {
    let guid: String
    let date: String
    let published: String
    let title: String
    let duration: Int
    let audioUrl: String
    let summary: String
    let periodStart: String
    let periodEnd: String
    let sources: [SourceGroup]
    var id: String { guid }
}

struct Voice: Decodable, Identifiable, Hashable {
    let voiceId: String
    let name: String
    let description: String
    let previewUrl: String
    var id: String { voiceId }
}

struct SourceCheck: Decodable {
    let url: String
    let kind: String
    let name: String
    let error: String?
}

struct Me: Decodable {
    let email: String?
    var notifyNew: Bool
    var notifyFailed: Bool
    let pushRegistered: Bool
    let pushAvailable: Bool
}

struct TokenResponse: Decodable { let accessToken: String }
struct Health: Decodable { let ok: Bool; let devAuth: Bool }
struct Message: Decodable { let message: String }

/// Lichaam voor aanmaken en bijwerken van een podcast.
struct PodcastBody: Encodable {
    var title: String
    var topics: [String]
    var sources: [String]
    var durationMinutes: Int
    var voiceId: String
    var voiceName: String
    var style: String
    var schedule: Schedule
}
