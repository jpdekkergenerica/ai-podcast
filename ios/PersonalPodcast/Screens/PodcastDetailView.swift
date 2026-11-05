import SwiftUI

/// Scherm 6 · Podcastdetail: status, volgende publicatie, persoonlijke feed, instellingen en afleveringen.
struct PodcastDetailView: View {
    let id: String
    @Environment(\.dismiss) private var dismiss
    @Environment(\.openURL) private var openURL
    @State private var podcast: Podcast?
    @State private var episodes: [EpisodeSummary] = []
    @State private var error: String?
    @State private var confirm: Confirm?
    @State private var showForm = false
    @State private var copied = false

    enum Confirm: Identifiable { case delete, rotate; var id: Int { hashValue } }

    private static let styleLabel = ["zakelijk": "Zakelijk", "informeel": "Informeel", "verhalend": "Verhalend"]

    var body: some View {
        Group {
            if let p = podcast { content(p) }
            else if let error { ContentUnavailableView("Laden mislukt", systemImage: "wifi.slash", description: Text(error)) }
            else { ProgressView("Laden…") }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Theme.background)
        .navigationTitle(podcast?.title ?? "Podcast")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar { if podcast != nil { ToolbarItem(placement: .primaryAction) { Button("Bewerken") { showForm = true } } } }
        .task { await load() }
        .task(id: podcast?.status.code) {
            while podcast?.status.code == "running", !Task.isCancelled {
                try? await Task.sleep(for: .seconds(8))
                await load()
            }
        }
        .refreshable { await load() }
        .errorAlert($error)
    }

    private func content(_ p: Podcast) -> some View {
        List {
            Section {
                HStack(spacing: 16) {
                    CoverImage(url: p.coverUrl, size: 88, radius: 14)
                    VStack(alignment: .leading, spacing: 6) {
                        StatusPill(status: p.status)
                        Text(p.status.detail).font(.footnote).foregroundStyle(Theme.secondary)
                        if let next = p.nextRun { Text("Volgende aflevering: **\(next.local)**").font(.footnote) }
                    }
                }
            }.listRowBackground(Theme.card)

            Section("Luisteren") {
                if let feed = feedURL(p) {
                    Button { openURL(feed) } label: { Label("Volg in Apple Podcasts", systemImage: "headphones") }
                }
                Button { UIPasteboard.general.string = p.feedUrl; copied = true
                    Task { try? await Task.sleep(for: .seconds(2)); copied = false }
                } label: { Label(copied ? "Gekopieerd" : "Kopieer feedlink", systemImage: copied ? "checkmark" : "doc.on.doc") }
                Button { confirm = .rotate } label: { Label("Nieuwe feedlink maken", systemImage: "arrow.triangle.2.circlepath") }
                Text("Deel de feedlink met niemand: wie hem heeft, kan je afleveringen beluisteren. Afleveringen kun je ook in deze app afspelen.")
                    .font(.footnote).foregroundStyle(Theme.warning)
            }.listRowBackground(Theme.card)

            Section("Instellingen") {
                LabeledContent("Onderwerpen", value: p.topics.map(\.text).joined(separator: " · "))
                LabeledContent("Duur", value: "\(p.durationMinutes) min")
                LabeledContent("Stem", value: p.voice.name.isEmpty ? "Standaardstem" : p.voice.name)
                LabeledContent("Vertelstijl", value: Self.styleLabel[p.style] ?? p.style)
                LabeledContent("Planning", value: p.schedule.label)
                LabeledContent("Eigen bronnen", value: p.sources.isEmpty ? "Geen" : "\(p.sources.count)")
            }.listRowBackground(Theme.card)

            Section("Afleveringen") {
                if episodes.isEmpty {
                    Text(p.status.code == "running" ? "De eerste aflevering wordt gemaakt. Dit duurt een paar minuten." : "Er is nog geen aflevering gepubliceerd.")
                        .font(.footnote).foregroundStyle(Theme.secondary)
                }
                ForEach(episodes) { e in
                    NavigationLink { EpisodeDetailView(podcast: p, guid: e.guid) } label: {
                        VStack(alignment: .leading, spacing: 3) {
                            Text(e.title).font(.body).lineLimit(2)
                            Text("\(Dutch.date(e.published.isEmpty ? e.date : e.published)) · \(Dutch.minutes(e.duration))").font(.footnote).foregroundStyle(Theme.secondary)
                        }
                    }
                }
            }.listRowBackground(Theme.card)

            Section {
                if p.paused {
                    Button { Task { await act { try await APIClient.shared.resume(id) } } } label: { Label("Hervatten", systemImage: "play.fill") }
                } else {
                    Button { Task { await act { try await APIClient.shared.pause(id) } } } label: { Label("Pauzeren", systemImage: "pause.fill") }
                }
                Button(role: .destructive) { confirm = .delete } label: { Label("Podcast verwijderen", systemImage: "trash") }
            } footer: { Text("Bestaande afleveringen blijven bewaard totdat je de podcast verwijdert.") }
                .listRowBackground(Theme.card)
        }
        .scrollContentBackground(.hidden)
        .sheet(isPresented: $showForm) {
            NavigationStack { PodcastFormView(existing: p) { _ in showForm = false; Task { await load() } } }
        }
        .confirmationDialog(confirm == .delete ? "“\(p.title)” verwijderen?" : "Nieuwe feedlink maken?",
                            isPresented: Binding(get: { confirm != nil }, set: { if !$0 { confirm = nil } }), titleVisibility: .visible) {
            if confirm == .delete {
                Button("Verwijderen", role: .destructive) { Task { await remove() } }
            } else {
                Button("Nieuwe link maken") { Task { await act { try await APIClient.shared.rotateFeedToken(id) } } }
            }
            Button("Annuleren", role: .cancel) {}
        } message: {
            Text(confirm == .delete ? "De podcast, alle afleveringen en de feed verdwijnen. Dit kun je niet terugdraaien."
                                    : "De oude link stopt direct met werken. Voeg de nieuwe link opnieuw toe in Apple Podcasts.")
        }
    }

    /// podcast://… opent Apple Podcasts met een vraag om deze feed te volgen.
    private func feedURL(_ p: Podcast) -> URL? {
        guard var parts = URLComponents(string: p.feedUrl) else { return nil }
        parts.scheme = "podcast"
        return parts.url
    }

    private func load() async {
        do {
            async let pod = APIClient.shared.podcast(id)
            async let eps = APIClient.shared.episodes(id)
            podcast = try await pod; episodes = try await eps
        } catch { if podcast == nil { self.error = error.localizedDescription } }
    }

    private func act(_ work: () async throws -> Podcast) async {
        do { podcast = try await work() } catch { self.error = error.localizedDescription }
    }

    private func remove() async {
        do { _ = try await APIClient.shared.deletePodcast(id); dismiss() } catch { self.error = error.localizedDescription }
    }
}
