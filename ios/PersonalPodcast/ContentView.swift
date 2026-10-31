import SwiftUI
import WebKit
import AuthenticationServices

/// Host voor de Monsey-config-UI. Luisteren gebeurt in Apple Podcasts; deze app is alleen configuratie.
struct ContentView: View {
    private var startURL: URL {
        if let raw = Bundle.main.object(forInfoDictionaryKey: "PODCAST_WEB_URL") as? String,
           let url = URL(string: raw), !raw.isEmpty {
            return url
        }
        return URL(string: "http://127.0.0.1:8766/ui_kits/podcast-app/mobile.html")!
    }

    var body: some View {
        WebView(url: startURL)
            .ignoresSafeArea()
    }
}

struct WebView: UIViewRepresentable {
    let url: URL

    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        config.allowsInlineMediaPlayback = true
        config.userContentController.add(context.coordinator, name: "appleSignIn")
        config.userContentController.add(context.coordinator, name: "push")
        let view = WKWebView(frame: .zero, configuration: config)
        context.coordinator.webView = view
        view.scrollView.contentInsetAdjustmentBehavior = .never
        view.navigationDelegate = context.coordinator
        view.uiDelegate = context.coordinator
        view.load(URLRequest(url: url, cachePolicy: .reloadIgnoringLocalCacheData))
        return view
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}

    func makeCoordinator() -> Coordinator { Coordinator() }

    /// Brug tussen de webpagina en Sign in with Apple: JS stuurt "appleSignIn", het resultaat gaat terug via `__appleSignInResult`.
    final class Coordinator: NSObject, WKNavigationDelegate, WKUIDelegate, WKScriptMessageHandler,
                             ASAuthorizationControllerDelegate, ASAuthorizationControllerPresentationContextProviding {
        weak var webView: WKWebView?

        func userContentController(_ controller: WKUserContentController, didReceive message: WKScriptMessage) {
            if message.name == "push" {
                let action = (message.body as? [String: Any])?["action"] as? String ?? "status"
                PushBridge.shared.handle(action: action) { payload in self.send(payload, to: "__pushResult") }
                return
            }
            guard message.name == "appleSignIn" else { return }
            let request = ASAuthorizationAppleIDProvider().createRequest()
            request.requestedScopes = [.email]
            let auth = ASAuthorizationController(authorizationRequests: [request])
            auth.delegate = self
            auth.presentationContextProvider = self
            auth.performRequests()
        }

        func presentationAnchor(for controller: ASAuthorizationController) -> ASPresentationAnchor {
            webView?.window ?? ASPresentationAnchor()
        }

        func authorizationController(controller: ASAuthorizationController,
                                     didCompleteWithAuthorization authorization: ASAuthorization) {
            guard let credential = authorization.credential as? ASAuthorizationAppleIDCredential,
                  let data = credential.identityToken,
                  let token = String(data: data, encoding: .utf8) else {
                send(["error": "Apple gaf geen token terug"])
                return
            }
            var payload: [String: Any] = ["identityToken": token]
            if let email = credential.email { payload["email"] = email }
            send(payload)
        }

        func authorizationController(controller: ASAuthorizationController, didCompleteWithError error: Error) {
            let cancelled = (error as? ASAuthorizationError)?.code == .canceled
            send(["error": cancelled ? "Inloggen geannuleerd" : "Inloggen met Apple mislukt: \(error.localizedDescription)"])
        }

        private func send(_ payload: [String: Any], to callback: String = "__appleSignInResult") {
            guard let json = try? JSONSerialization.data(withJSONObject: payload),
                  let text = String(data: json, encoding: .utf8) else { return }
            DispatchQueue.main.async {
                self.webView?.evaluateJavaScript("window.\(callback)(\(text))")
            }
        }

        /// Links naar bronnen (window.open of een link naar een andere site) openen in Safari, niet in deze WebView.
        func webView(_ webView: WKWebView, createWebViewWith configuration: WKWebViewConfiguration,
                     for navigationAction: WKNavigationAction, windowFeatures: WKWindowFeatures) -> WKWebView? {
            if let url = navigationAction.request.url, ["http", "https"].contains(url.scheme?.lowercased() ?? "") {
                UIApplication.shared.open(url)
            }
            return nil
        }

        func webView(_ webView: WKWebView,
                     decidePolicyFor navigationAction: WKNavigationAction,
                     decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
            if let url = navigationAction.request.url,
               let scheme = url.scheme?.lowercased(),
               scheme == "podcasts" || scheme == "itms-podcasts" {
                UIApplication.shared.open(url)
                decisionHandler(.cancel)
                return
            }
            if navigationAction.navigationType == .linkActivated, let url = navigationAction.request.url,
               ["http", "https"].contains(url.scheme?.lowercased() ?? ""), url.host != webView.url?.host {
                UIApplication.shared.open(url)
                decisionHandler(.cancel)
                return
            }
            decisionHandler(.allow)
        }
    }
}
