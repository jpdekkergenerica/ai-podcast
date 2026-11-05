import SwiftUI
import PhotosUI

/// Scherm 4 · Omslag kiezen: huidige of standaardomslag, kiezen of vervangen met voorbeeld, en verwijderen.
struct CoverPickerView: View {
    let current: String?
    let hasCustom: Bool
    @Binding var choice: PodcastFormView.CoverChoice
    @State private var item: PhotosPickerItem?
    @State private var error: String?

    private var hasOwn: Bool {
        switch choice {
        case .new: return true
        case .remove: return false
        case .keep: return hasCustom
        }
    }

    var body: some View {
        VStack(spacing: 16) {
            preview.frame(width: 240, height: 240)
            Text(caption).font(.footnote).foregroundStyle(Theme.secondary)
            if let error { Text(error).font(.footnote).foregroundStyle(Theme.negative) }
            PhotosPicker(selection: $item, matching: .images) {
                Text(hasOwn ? "Vervangen" : "Kiezen").font(.headline).frame(maxWidth: .infinity, minHeight: 50)
                    .foregroundStyle(.white).background(Theme.brandFill, in: RoundedRectangle(cornerRadius: 14))
            }
            if hasOwn { Button("Eigen omslag verwijderen", role: .destructive) { choice = .remove } }
            Text("Een omslag is optioneel. Zonder eigen afbeelding gebruiken we een standaardomslag.").font(.footnote).foregroundStyle(Theme.secondary).multilineTextAlignment(.center)
            Spacer()
        }
        .padding(24)
        .background(Theme.background)
        .navigationTitle("Omslag")
        .navigationBarTitleDisplayMode(.inline)
        .onChange(of: item) { _, new in Task { await load(new) } }
    }

    @ViewBuilder private var preview: some View {
        switch choice {
        case .new(_, let image): Image(uiImage: image).resizable().scaledToFill().clipShape(RoundedRectangle(cornerRadius: 16))
        case .remove: CoverImage(url: nil, size: 240, radius: 16)
        case .keep: CoverImage(url: current, size: 240, radius: 16)
        }
    }

    private var caption: String {
        switch choice {
        case .new: return "Zo ziet je omslag eruit (vierkante uitsnede). Het wordt opgeslagen met de podcast."
        case .remove: return "Het standaardomslag wordt gebruikt zodra je opslaat."
        case .keep: return hasCustom ? "Je eigen omslag" : "Standaardomslag met de naam van je podcast"
        }
    }

    private func load(_ item: PhotosPickerItem?) async {
        guard let item else { return }
        error = nil
        do {
            guard let data = try await item.loadTransferable(type: Data.self), let image = UIImage(data: data) else {
                error = "Dit bestand is geen afbeelding die we kunnen gebruiken"; return
            }
            let pixels = min(image.size.width, image.size.height) * image.scale
            guard pixels >= 600 else { error = "De afbeelding is te klein (minimaal 600 bij 600 pixels)"; return }
            let side: CGFloat = 1400   // Apple vraagt 1400–3000 px, vierkant
            let format = UIGraphicsImageRendererFormat(); format.scale = 1
            let squared = UIGraphicsImageRenderer(size: CGSize(width: side, height: side), format: format).image { _ in
                let ratio = max(side / image.size.width, side / image.size.height)
                let w = image.size.width * ratio, h = image.size.height * ratio
                image.draw(in: CGRect(x: (side - w) / 2, y: (side - h) / 2, width: w, height: h))
            }
            guard let jpeg = squared.jpegData(compressionQuality: 0.88) else { error = "De afbeelding kon niet worden verwerkt"; return }
            choice = .new(jpeg, squared)
        } catch { self.error = "De afbeelding kon niet worden geladen" }
    }
}
