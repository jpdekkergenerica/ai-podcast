# iOS-host (TestFlight)

Dunne SwiftUI-shell met `WKWebView` die de Monsey-config-UI laadt. Geen native speler.

## Setup

```bash
# Genereer Xcode-project (eenmalig)
brew install xcodegen   # indien nodig
cd ios && xcodegen generate
open PersonalPodcast.xcodeproj
```

Zet in het scheme / Info `PODCAST_WEB_URL` op je gedeployde UI, bijvoorbeeld:

`https://api.example.com/app/ui_kits/podcast-app/mobile.html`

Lokaal: start de API (`python -m api.main`) en gebruik  
`http://127.0.0.1:8000/app/ui_kits/podcast-app/mobile.html`  
(simulator) of je Mac-LAN-IP op een device.

## Sign in with Apple

Productie: zet `AUTH_DEV_MODE=0`, `APPLE_CLIENT_ID` (Services ID / App ID) op de API, en vervang de dev-login in `Start.jsx` door AuthenticationServices → `POST /auth/apple`.
