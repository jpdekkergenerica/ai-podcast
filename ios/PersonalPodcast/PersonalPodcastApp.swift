import SwiftUI

@main
struct PersonalPodcastApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) private var delegate
    @State private var session = Session()
    @State private var player = AudioPlayer()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(session)
                .environment(player)
                .tint(Theme.brand)
        }
    }
}
