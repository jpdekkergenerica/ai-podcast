import SwiftUI
import AVFoundation

/// Scherm 5 · Stem kiezen: de stemmen van ElevenLabs met zoeken en een kort luistervoorbeeld.
struct VoicePickerView: View {
    @Binding var selection: VoiceRef
    @Environment(\.dismiss) private var dismiss
    @State private var voices: [Voice]?
    @State private var error: String?
    @State private var query = ""
    @State private var playing: String?
    @State private var player: AVPlayer?

    private var shown: [Voice] {
        let q = query.trimmingCharacters(in: .whitespaces).lowercased()
        return (voices ?? []).filter { q.isEmpty || "\($0.name) \($0.description)".lowercased().contains(q) }
    }

    var body: some View {
        List {
            if voices == nil && error == nil { HStack { ProgressView(); Text("Stemmen laden…").foregroundStyle(Theme.secondary) } }
            if let error { Text("\(error) Je huidige keuze (\(selection.name.isEmpty ? "standaardstem" : selection.name)) blijft behouden.").foregroundStyle(Theme.negative) }
            ForEach(shown) { v in
                HStack {
                    Button { selection = VoiceRef(voiceId: v.voiceId, name: v.name); stop(); dismiss() } label: {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(v.name).font(.body.weight(.medium)).foregroundStyle(Color.primary)
                            if !v.description.isEmpty { Text(v.description).font(.footnote).foregroundStyle(Theme.secondary).lineLimit(2) }
                        }
                    }
                    Spacer()
                    if selection.voiceId == v.voiceId { Image(systemName: "checkmark").foregroundStyle(Theme.brand) }
                    if let url = URL(string: v.previewUrl), !v.previewUrl.isEmpty {
                        Button { toggle(v, url) } label: { Image(systemName: playing == v.voiceId ? "stop.circle.fill" : "play.circle").font(.title2) }
                            .buttonStyle(.borderless).accessibilityLabel("Luister naar \(v.name)")
                    }
                }
            }
            if let voices, !voices.isEmpty, shown.isEmpty { Text("Geen stem gevonden voor “\(query)”.").foregroundStyle(Theme.secondary) }
        }
        .searchable(text: $query, prompt: "Zoek op naam")
        .navigationTitle("Stem kiezen")
        .navigationBarTitleDisplayMode(.inline)
        .task { await load() }
        .onDisappear(perform: stop)
    }

    private func load() async {
        do { voices = try await APIClient.shared.voices() } catch { voices = []; self.error = error.localizedDescription }
    }

    private func toggle(_ v: Voice, _ url: URL) {
        if playing == v.voiceId { stop(); return }
        stop()
        try? AVAudioSession.sharedInstance().setCategory(.playback)
        player = AVPlayer(url: url)
        player?.play()
        playing = v.voiceId
        NotificationCenter.default.addObserver(forName: .AVPlayerItemDidPlayToEndTime, object: player?.currentItem, queue: .main) { _ in playing = nil }
    }

    private func stop() { player?.pause(); player = nil; playing = nil }
}
