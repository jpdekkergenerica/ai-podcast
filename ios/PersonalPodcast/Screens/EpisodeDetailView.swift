import SwiftUI

/// Scherm 7 · Afleveringsdetail: afspelen, samenvatting, behandelde periode en de gebruikte bronnen per onderwerp.
struct EpisodeDetailView: View {
    let podcast: Podcast
    let guid: String
    @Environment(AudioPlayer.self) private var player
    @State private var episode: Episode?
    @State private var error: String?

    var body: some View {
        Group {
            if let ep = episode { content(ep) }
            else if let error { ContentUnavailableView("Laden mislukt", systemImage: "wifi.slash", description: Text(error)) }
            else { ProgressView("Laden…") }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Theme.background)
        .navigationTitle("Aflevering")
        .navigationBarTitleDisplayMode(.inline)
        .task { await load() }
    }

    private func content(_ ep: Episode) -> some View {
        List {
            Section {
                VStack(alignment: .leading, spacing: 6) {
                    Text(ep.title).font(.title2.weight(.bold)).fixedSize(horizontal: false, vertical: true)
                    Text("\(Dutch.date(ep.published.isEmpty ? ep.date : ep.published)) · \(Dutch.minutes(ep.duration))").font(.footnote).foregroundStyle(Theme.secondary)
                }
            }.listRowBackground(Theme.card)

            if let url = URL(string: ep.audioUrl), !ep.audioUrl.isEmpty {
                Section { playerControls(ep, url: url) }.listRowBackground(Theme.card)
            }

            if !ep.summary.isEmpty { Section { Text(ep.summary) }.listRowBackground(Theme.card) }

            if !ep.periodStart.isEmpty {
                Section { Text("Behandelde nieuwsperiode: \(Dutch.date(ep.periodStart)) t/m \(Dutch.date(ep.periodEnd.isEmpty ? ep.published : ep.periodEnd))")
                    .font(.footnote).foregroundStyle(Theme.secondary) }.listRowBackground(Theme.card)
            }

            ForEach(ep.sources, id: \.topic) { group in
                Section(group.topic.isEmpty ? "Bronnen" : group.topic) {
                    ForEach(group.items, id: \.link) { item in
                        if let url = URL(string: item.link) {
                            Link(destination: url) {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(item.title).font(.body.weight(.medium)).foregroundStyle(Color.primary)
                                    Text(item.source).font(.footnote).foregroundStyle(Theme.secondary)
                                }
                            }
                        }
                    }
                }.listRowBackground(Theme.card)
            }
        }
        .scrollContentBackground(.hidden)
    }

    @ViewBuilder
    private func playerControls(_ ep: Episode, url: URL) -> some View {
        let active = player.currentGuid == ep.guid
        VStack(spacing: 12) {
            Slider(value: Binding(get: { active ? player.position : 0 }, set: { player.seek(to: $0) }),
                   in: 0...max(active && player.duration > 0 ? player.duration : Double(ep.duration), 1))
                .disabled(!active)
            HStack {
                Text(Dutch.clock(active ? player.position : 0)).monospacedDigit()
                Spacer()
                Text(Dutch.clock(active && player.duration > 0 ? player.duration : Double(ep.duration))).monospacedDigit()
            }.font(.caption).foregroundStyle(Theme.secondary)
            HStack(spacing: 36) {
                Button { player.skip(-15) } label: { Image(systemName: "gobackward.15").font(.title2) }.disabled(!active)
                Button {
                    if !active { player.load(guid: ep.guid, url: url, title: ep.title, show: podcast.title) }
                    player.toggle()
                } label: {
                    Group {
                        if active && player.isLoading && player.isPlaying { ProgressView() }
                        else { Image(systemName: active && player.isPlaying ? "pause.circle.fill" : "play.circle.fill").font(.system(size: 52)) }
                    }.frame(width: 56, height: 56)
                }
                Button { player.skip(30) } label: { Image(systemName: "goforward.30").font(.title2) }.disabled(!active)
            }
            .buttonStyle(.plain).foregroundStyle(Theme.brand)
        }
        .padding(.vertical, 4)
    }

    private func load() async {
        do { episode = try await APIClient.shared.episode(podcast.id, guid: guid) } catch { self.error = error.localizedDescription }
    }
}
