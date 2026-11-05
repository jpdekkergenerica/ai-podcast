import SwiftUI

/// Scherm 2 · Mijn podcasts: omslag, naam, duur, planning, volgende publicatie en status per podcast.
struct PodcastListView: View {
    @State private var podcasts: [Podcast]?
    @State private var error: String?
    @State private var showForm = false
    @State private var toDelete: Podcast?
    @State private var path: [String] = []

    private var anyRunning: Bool { podcasts?.contains { $0.status.code == "running" } ?? false }

    var body: some View {
        Group {
            if let podcasts {
                if podcasts.isEmpty { empty } else { list(podcasts) }
            } else if let error {
                ContentUnavailableView("Laden mislukt", systemImage: "wifi.slash", description: Text(error))
            } else {
                ProgressView("Laden…")
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Theme.background)
        .navigationTitle("Mijn podcasts")
        .toolbar { ToolbarItem(placement: .primaryAction) { Button { showForm = true } label: { Image(systemName: "plus") }.accessibilityLabel("Podcast toevoegen") } }
        .sheet(isPresented: $showForm) {
            NavigationStack { PodcastFormView(existing: nil) { saved in showForm = false; Task { await load() }; path.append(saved.id) } }
        }
        .navigationDestination(for: String.self) { id in PodcastDetailView(id: id) }
        .task { await load() }
        .task(id: anyRunning) {
            // zolang er een aflevering wordt gemaakt, ververst de lijst zichzelf
            while anyRunning, !Task.isCancelled {
                try? await Task.sleep(for: .seconds(8))
                await load()
            }
        }
        .refreshable { await load() }
        .confirmationDialog(toDelete.map { "“\($0.title)” verwijderen?" } ?? "", isPresented: Binding(get: { toDelete != nil }, set: { if !$0 { toDelete = nil } }), titleVisibility: .visible) {
            Button("Verwijderen", role: .destructive) { if let p = toDelete { Task { await delete(p) } } }
            Button("Annuleren", role: .cancel) {}
        } message: { Text("De podcast, alle afleveringen en de feed verdwijnen. Dit kun je niet terugdraaien.") }
    }

    private var empty: some View {
        ContentUnavailableView {
            Label("Nog geen podcasts", systemImage: "mic")
        } description: {
            Text("Kies je onderwerpen en wij maken en publiceren de afleveringen. Luisteren kan in deze app en in Apple Podcasts.")
        } actions: {
            Button("Podcast toevoegen") { showForm = true }.buttonStyle(.borderedProminent).tint(Theme.brandFill)
        }
    }

    private func list(_ items: [Podcast]) -> some View {
        List {
            ForEach(items) { p in
                NavigationLink(value: p.id) { row(p) }
                    .listRowBackground(Theme.card)
                    .swipeActions { Button("Verwijderen", role: .destructive) { toDelete = p } }
            }
        }
        .scrollContentBackground(.hidden)
    }

    private func row(_ p: Podcast) -> some View {
        HStack(spacing: 12) {
            CoverImage(url: p.coverUrl, size: 64)
            VStack(alignment: .leading, spacing: 4) {
                Text(p.title).font(.headline).lineLimit(1)
                Text("\(p.durationMinutes) min · \(p.schedule.label)").font(.footnote).foregroundStyle(Theme.secondary).lineLimit(1)
                Text(p.nextRun.map { "Volgende: \($0.local)" } ?? (p.paused ? "Gepauzeerd" : "")).font(.footnote).foregroundStyle(Theme.secondary).lineLimit(1)
                StatusPill(status: p.status)
            }
        }
        .padding(.vertical, 4)
    }

    private func load() async {
        do { podcasts = try await APIClient.shared.podcasts(); error = nil }
        catch { if podcasts == nil { self.error = error.localizedDescription } }
    }

    private func delete(_ p: Podcast) async {
        do { _ = try await APIClient.shared.deletePodcast(p.id); toDelete = nil; await load() }
        catch { self.error = error.localizedDescription }
    }
}
