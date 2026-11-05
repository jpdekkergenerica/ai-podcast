import SwiftUI
import AuthenticationServices

/// Scherm 1 · Aanmelden: video-achtergrond, korte uitleg en Doorgaan met Apple.
struct StartView: View {
    @Environment(Session.self) private var session
    @State private var busy = false
    @State private var error: String?

    var body: some View {
        ZStack {
            LoopingVideoBackground(resourceName: "yourownpod-bg", resourceExtension: "mp4")
                .ignoresSafeArea()

            LinearGradient(
                colors: [
                    .black.opacity(0.50),
                    .black.opacity(0.18),
                    .black.opacity(0.05),
                    .black.opacity(0.20),
                    .black.opacity(0.78),
                ],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()
            .allowsHitTesting(false)

            GeometryReader { geo in
                // Muziekbalk ~midden van het volle scherm (video is full-bleed).
                let fullH = geo.size.height + geo.safeAreaInsets.top + geo.safeAreaInsets.bottom
                let barTopInFull = fullH * 0.42
                let barBottomInFull = fullH * 0.58
                // Coordinaten in deze GeometryReader beginnen onder de safe area.
                let barTop = barTopInFull - geo.safeAreaInsets.top
                let barBottom = barBottomInFull - geo.safeAreaInsets.top
                let headerBottom: CGFloat = 56
                let titleY = (headerBottom + max(headerBottom + 8, barTop)) / 2

                VStack(alignment: .leading, spacing: 0) {
                    HStack(spacing: 10) {
                        Image(systemName: "mic.fill").font(.title3).foregroundStyle(.white)
                            .frame(width: 40, height: 40).background(Theme.brandFill, in: RoundedRectangle(cornerRadius: 10))
                        Text("yourownpod").font(.title3.weight(.semibold)).foregroundStyle(.white)
                    }

                    Spacer(minLength: 0)
                        .frame(height: max(0, titleY - headerBottom / 2 - 28))

                    Text("Jouw onderwerpen, jouw podcast")
                        .font(.largeTitle.weight(.bold))
                        .foregroundStyle(.white)
                        .fixedSize(horizontal: false, vertical: true)

                    Spacer(minLength: 0)
                        .frame(height: max(24, barTop - titleY - 28))

                    // Vrije band voor de muziekbalk.
                    Color.clear.frame(height: max(80, barBottom - barTop))

                    Text("Kies waar je nieuws over wilt horen. Wij maken en publiceren de afleveringen in je eigen feed. Luisteren kan in deze app of in Apple Podcasts.")
                        .foregroundStyle(.white.opacity(0.9))
                    if let error {
                        Text(error).font(.subheadline).foregroundStyle(Color(red: 1, green: 0.55, blue: 0.5)).padding(.top, 8)
                    }

                    Spacer(minLength: 16)

                    SignInWithAppleButton(.continue) { request in
                        request.requestedScopes = [.fullName, .email]
                    } onCompletion: { result in
                        handle(result)
                    }
                    .signInWithAppleButtonStyle(.white)
                    .frame(height: 52)
                    .disabled(busy)
                    if busy { ProgressView().tint(.white).frame(maxWidth: .infinity).padding(.top, 12) }
                }
                .padding(.horizontal, 24)
                .padding(.top, 8)
                .padding(.bottom, 8)
            }
        }
    }

    private func handle(_ result: Result<ASAuthorization, Error>) {
        switch result {
        case .failure(let failure):
            if (failure as? ASAuthorizationError)?.code != .canceled { error = "Inloggen met Apple mislukt. Probeer het opnieuw." }
        case .success(let auth):
            guard let credential = auth.credential as? ASAuthorizationAppleIDCredential,
                  let data = credential.identityToken, let token = String(data: data, encoding: .utf8) else {
                error = "Apple gaf geen inlogbewijs terug. Probeer het opnieuw."; return
            }
            Task {
                busy = true; error = nil
                do { let name = credential.fullName.flatMap { PersonNameComponentsFormatter().string(from: $0) }
                    try await session.signIn(appleToken: token, email: credential.email, name: name) }
                catch { self.error = error.localizedDescription }
                busy = false
            }
        }
    }
}
