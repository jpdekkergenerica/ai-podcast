import SwiftUI
import AuthenticationServices

/// Scherm 1 · Aanmelden: korte uitleg en Doorgaan met Apple.
struct StartView: View {
    @Environment(Session.self) private var session
    @State private var busy = false
    @State private var error: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 24) {
            HStack(spacing: 10) {
                Image(systemName: "mic.fill").font(.title3).foregroundStyle(.white)
                    .frame(width: 40, height: 40).background(Theme.brandFill, in: RoundedRectangle(cornerRadius: 10))
                Text("yourownpod").font(.title3.weight(.semibold))
            }
            Spacer()
            VStack(alignment: .leading, spacing: 10) {
                Text("Jouw onderwerpen, jouw podcast").font(.largeTitle.weight(.bold)).fixedSize(horizontal: false, vertical: true)
                Text("Kies waar je nieuws over wilt horen. Wij maken en publiceren de afleveringen in je eigen feed. Luisteren kan in deze app of in Apple Podcasts.")
                    .foregroundStyle(Theme.secondary)
                if let error { Text(error).font(.subheadline).foregroundStyle(Theme.negative).padding(.top, 4) }
            }
            Spacer()
            VStack(spacing: 12) {
                SignInWithAppleButton(.continue) { request in
                    request.requestedScopes = [.fullName, .email]
                } onCompletion: { result in
                    handle(result)
                }
                .signInWithAppleButtonStyle(.black)
                .frame(height: 52)
                .disabled(busy)
                if session.devAuth {
                    Button("Ontwikkel-login") { Task { await devLogin() } }
                        .buttonStyle(SecondaryButtonStyle()).disabled(busy)
                }
            }
            if busy { ProgressView().frame(maxWidth: .infinity) }
        }
        .padding(24)
        .background(Theme.background)
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

    private func devLogin() async {
        busy = true; error = nil
        do { try await session.signInDev() } catch { self.error = error.localizedDescription }
        busy = false
    }
}
