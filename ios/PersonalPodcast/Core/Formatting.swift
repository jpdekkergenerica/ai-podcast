import Foundation

enum Dutch {
    static let dayShort = ["Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"]
    static let dayName = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]

    static func parse(_ iso: String) -> Date? {
        let full = ISO8601DateFormatter()
        full.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        let plain = ISO8601DateFormatter()
        let dateOnly = ISO8601DateFormatter()
        dateOnly.formatOptions = [.withFullDate]
        return full.date(from: iso) ?? plain.date(from: iso) ?? dateOnly.date(from: iso)
    }

    /// "donderdag 5 november"
    static func date(_ iso: String) -> String {
        guard let d = parse(iso) else { return "" }
        let f = DateFormatter()
        f.locale = Locale(identifier: "nl_NL")
        f.dateFormat = "EEEE d MMMM"
        return f.string(from: d)
    }

    static func minutes(_ seconds: Int) -> String { "\(max(1, Int((Double(seconds) / 60).rounded()))) min" }

    static func clock(_ seconds: Double) -> String {
        guard seconds.isFinite, seconds >= 0 else { return "0:00" }
        let s = Int(seconds)
        return String(format: "%d:%02d", s / 60, s % 60)
    }
}

enum SchedulePreset: String, CaseIterable, Identifiable {
    case daily, weekdays, weekly, every
    var id: String { rawValue }
    var label: String {
        switch self {
        case .daily: return "Dagelijks"
        case .weekdays: return "Werkdagen"
        case .weekly: return "Wekelijks"
        case .every: return "Elke … dagen"
        }
    }
}

extension Schedule {
    var preset: SchedulePreset {
        if everyDays != nil { return .every }
        if days.count == 7 { return .daily }
        if days.count == 5 && days.allSatisfy({ $0 < 5 }) { return .weekdays }
        if days.count == 1 { return .weekly }
        return .daily
    }

    mutating func apply(_ preset: SchedulePreset, weekday: Int? = nil) {
        switch preset {
        case .daily: days = Array(0...6); everyDays = nil
        case .weekdays: days = Array(0...4); everyDays = nil
        case .weekly: days = [weekday ?? (days.count == 1 ? days[0] : 0)]; everyDays = nil
        case .every: days = Array(0...6); everyDays = everyDays ?? 2
        }
    }

    var label: String {
        if let everyDays { return "Elke \(everyDays) dagen om \(time)" }
        switch preset {
        case .daily: return "Dagelijks om \(time)"
        case .weekdays: return "Werkdagen om \(time)"
        case .weekly: return "Elke \(Dutch.dayName[days[0]]) om \(time)"
        case .every: return "Om \(time)"
        }
    }
}
