import SwiftUI
import UIKit

extension UIColor {
    convenience init(rgb: UInt32) {
        self.init(red: CGFloat((rgb >> 16) & 0xFF) / 255, green: CGFloat((rgb >> 8) & 0xFF) / 255, blue: CGFloat(rgb & 0xFF) / 255, alpha: 1)
    }
}

extension Color {
    init(light: UInt32, dark: UInt32) {
        self.init(UIColor { $0.userInterfaceStyle == .dark ? UIColor(rgb: dark) : UIColor(rgb: light) })
    }
}

/// Kleuren van de yourownpod-stijl (paars), met licht en donker.
enum Theme {
    static let brand = Color(light: 0x72188B, dark: 0xC58AD8)        // tekst en accenten
    static let brandFill = Color(light: 0x72188B, dark: 0x9748AD)    // knoppen
    static let brandSoft = Color(light: 0xF2E8F5, dark: 0x2A1A31)
    static let background = Color(light: 0xFBFBFB, dark: 0x0D0D12)
    static let card = Color(light: 0xFFFFFF, dark: 0x16161D)
    static let fill = Color(light: 0xEEEFF2, dark: 0x272835)
    static let secondary = Color(light: 0x666D80, dark: 0xA4ABB8)
    static let positive = Color(light: 0x2F7A3E, dark: 0x5FC474)
    static let positiveSoft = Color(light: 0xE5F2E8, dark: 0x1B2E20)
    static let negative = Color(light: 0xD12C2C, dark: 0xFF5A4F)
    static let negativeSoft = Color(light: 0xFBE6E6, dark: 0x3A1C1C)
    static let warning = Color(light: 0x8A6100, dark: 0xFFD60A)
    static let warningSoft = Color(light: 0xFFF4D6, dark: 0x3A3210)
}

struct PrimaryButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) private var enabled
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.headline)
            .frame(maxWidth: .infinity, minHeight: 50)
            .foregroundStyle(.white)
            .background(Theme.brandFill.opacity(enabled ? (configuration.isPressed ? 0.8 : 1) : 0.4), in: RoundedRectangle(cornerRadius: 14))
    }
}

struct SecondaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.headline)
            .frame(maxWidth: .infinity, minHeight: 50)
            .foregroundStyle(Theme.brand)
            .background(Theme.brandSoft.opacity(configuration.isPressed ? 0.7 : 1), in: RoundedRectangle(cornerRadius: 14))
    }
}

/// Omslag van een podcast; toont een grijs vlak zolang het laadt.
struct CoverImage: View {
    let url: String?
    var size: CGFloat = 64
    var radius: CGFloat = 12

    var body: some View {
        AsyncImage(url: url.flatMap(URL.init(string:))) { phase in
            switch phase {
            case .success(let image): image.resizable().scaledToFill()
            default: Theme.fill.overlay(Image(systemName: "mic.fill").foregroundStyle(Theme.secondary))
            }
        }
        .frame(width: size, height: size)
        .clipShape(RoundedRectangle(cornerRadius: radius))
    }
}

/// Statuslabel: Gepland · Bezig · Gepubliceerd · Mislukt · Gepauzeerd · Overgeslagen.
struct StatusPill: View {
    let status: PodStatus

    private var colors: (Color, Color) {
        switch status.code {
        case "published": return (Theme.positiveSoft, Theme.positive)
        case "failed": return (Theme.negativeSoft, Theme.negative)
        case "skipped": return (Theme.warningSoft, Theme.warning)
        case "paused": return (Theme.fill, Theme.secondary)
        default: return (Theme.brandSoft, Theme.brand)
        }
    }

    var body: some View {
        HStack(spacing: 6) {
            if status.code == "running" { ProgressView().controlSize(.mini) } else { Circle().frame(width: 6, height: 6) }
            Text(status.label).font(.caption.weight(.medium))
        }
        .padding(.horizontal, 8).frame(height: 24)
        .foregroundStyle(colors.1)
        .background(colors.0, in: Capsule())
    }
}
