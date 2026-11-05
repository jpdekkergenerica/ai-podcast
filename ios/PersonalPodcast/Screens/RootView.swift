import SwiftUI

struct RootView: View {
    @Environment(Session.self) private var session

    var body: some View {
        Group {
            if session.booting {
                ProgressView("Laden…").frame(maxWidth: .infinity, maxHeight: .infinity).background(Theme.background)
            } else if session.isAuthed {
                MainTabs()
            } else {
                StartView()
            }
        }
        .task { await session.boot() }
    }
}

struct MainTabs: View {
    var body: some View {
        TabView {
            NavigationStack { PodcastListView() }
                .tabItem { Label("Podcasts", systemImage: "mic.fill") }
            NavigationStack { AccountView() }
                .tabItem { Label("Account", systemImage: "person.crop.circle") }
        }
    }
}

/// Foutmelding als alert.
extension View {
    func errorAlert(_ message: Binding<String?>) -> some View {
        alert("Er ging iets mis", isPresented: Binding(get: { message.wrappedValue != nil }, set: { if !$0 { message.wrappedValue = nil } })) {
            Button("OK", role: .cancel) {}
        } message: { Text(message.wrappedValue ?? "") }
    }
}
