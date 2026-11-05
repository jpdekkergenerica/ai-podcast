import SwiftUI

/// Scherm 3 · Podcast aanmaken en bewerken: basis, onderwerpen en bronnen, duur/stem/stijl en planning.
struct PodcastFormView: View {
    let existing: Podcast?
    let onSaved: (Podcast) -> Void

    @Environment(\.dismiss) private var dismiss

    struct Entry: Identifiable { let id = UUID(); var text: String }
    struct DraftSource: Identifiable { let id = UUID(); let url: String; let name: String; let error: String? }
    enum CoverChoice { case keep, new(Data, UIImage), remove }

    @State private var title = ""
    @State private var topics = [Entry(text: "")]
    @State private var sources: [DraftSource] = []
    @State private var sourceDraft = ""
    @State private var sourceBusy = false
    @State private var duration = 10
    @State private var voice = VoiceRef(voiceId: "dLPO5AsXc3FZDbTh1IKa", name: "Standaardstem")
    @State private var style = "informeel"
    @State private var schedule = Schedule()
    @State private var time = Date()
    @State private var cover = CoverChoice.keep
    @State private var errors: [String: String] = [:]
    @State private var busy = false
    @State private var loaded = false

    private static let styles = [("zakelijk", "Zakelijk", "Helder, feitelijk en beknopt"),
                                 ("informeel", "Informeel", "Warm en rechtstreeks, alsof je een vriend bijpraat"),
                                 ("verhalend", "Verhalend", "Het nieuws als verhaal met een lijn")]

    private var editing: Bool { existing != nil }

    var body: some View {
        Form {
            Section("Basisgegevens") {
                TextField("Naam, bijvoorbeeld Mijn technieuws", text: $title)
                fieldError("title")
                NavigationLink {
                    CoverPickerView(current: existing?.coverUrl, hasCustom: existing?.hasCustomCover ?? false, choice: $cover)
                } label: {
                    HStack {
                        VStack(alignment: .leading, spacing: 2) {
                            Text("Omslag")
                            Text("Optioneel. Zonder eigen afbeelding gebruiken we een standaardomslag.").font(.footnote).foregroundStyle(Theme.secondary)
                        }
                        Spacer()
                        coverThumb
                    }
                }
            }

            Section {
                ForEach($topics) { $entry in
                    TextField("Bijvoorbeeld: nieuwe ontwikkelingen in AI-regelgeving", text: $entry.text, axis: .vertical)
                }
                .onDelete { if topics.count > 1 { topics.remove(atOffsets: $0) } }
                fieldError("topics")
                if topics.count < 12 {
                    Button { topics.append(Entry(text: "")) } label: { Label("Onderwerp toevoegen", systemImage: "plus") }
                }
            } header: { Text("Onderwerpen") } footer: { Text("Eén onderwerp per veld. Veeg naar links om er een te verwijderen.") }

            Section {
                ForEach(sources) { s in
                    VStack(alignment: .leading, spacing: 2) {
                        Text(s.name.isEmpty ? s.url : s.name).font(.body.weight(.medium))
                        Text(s.url).font(.footnote).foregroundStyle(Theme.secondary).lineLimit(1)
                        if let e = s.error { Text(e).font(.footnote).foregroundStyle(Theme.negative) }
                    }
                }
                .onDelete { sources.remove(atOffsets: $0) }
                HStack {
                    TextField("https://… (website of RSS)", text: $sourceDraft)
                        .keyboardType(.URL).textInputAutocapitalization(.never).autocorrectionDisabled()
                    if sourceBusy { ProgressView() } else {
                        Button("Voeg toe") { Task { await addSource() } }.disabled(sourceDraft.trimmingCharacters(in: .whitespaces).isEmpty)
                    }
                }
                fieldError("sources")
            } header: { Text("Eigen bronnen (optioneel)") } footer: { Text("De app zoekt zelf ook betrouwbare bronnen en combineert die met jouw bronnen.") }

            Section("Duur, stem en vertelstijl") {
                Picker("Duur", selection: $duration) { ForEach([5, 10, 15, 20], id: \.self) { Text("\($0) min").tag($0) } }
                    .pickerStyle(.segmented)
                fieldError("duration_minutes")
                NavigationLink { VoicePickerView(selection: $voice) } label: { LabeledContent("Stem", value: voice.name.isEmpty ? "Kies een stem" : voice.name) }
                fieldError("voice")
                Picker("Vertelstijl", selection: $style) { ForEach(Self.styles, id: \.0) { Text($0.1).tag($0.0) } }.pickerStyle(.segmented)
                Text(Self.styles.first { $0.0 == style }?.2 ?? "").font(.footnote).foregroundStyle(Theme.secondary)
                fieldError("style")
            }

            Section {
                Picker("Frequentie", selection: Binding(get: { schedule.preset }, set: { schedule.apply($0) })) {
                    ForEach(SchedulePreset.allCases) { Text($0.label).tag($0) }
                }
                if schedule.preset == .weekly {
                    Picker("Dag", selection: Binding(get: { schedule.days.first ?? 0 }, set: { schedule.apply(.weekly, weekday: $0) })) {
                        ForEach(0..<7, id: \.self) { Text(Dutch.dayName[$0].capitalized).tag($0) }
                    }
                }
                if schedule.preset == .every {
                    Stepper("Elke \(schedule.everyDays ?? 2) dagen", value: Binding(get: { schedule.everyDays ?? 2 }, set: { schedule.everyDays = $0 }), in: 2...30)
                }
                DatePicker("Klaar om", selection: $time, displayedComponents: .hourAndMinute)
                fieldError("schedule")
            } header: { Text("Planning") } footer: {
                Text("Tijdzone: \(TimeZone.current.identifier). De aflevering staat op dit tijdstip klaar; de voorbereiding begint iets eerder.")
            }

            Section {
                if let general = errors["form"] { Text(general).foregroundStyle(Theme.negative) }
                Button { Task { await submit() } } label: {
                    if busy { ProgressView().frame(maxWidth: .infinity) } else { Text(editing ? "Wijzigingen opslaan" : "Podcast aanmaken") }
                }
                .buttonStyle(PrimaryButtonStyle()).disabled(busy).listRowInsets(EdgeInsets()).listRowBackground(Color.clear)
            } footer: {
                Text(editing ? "Wijzigingen gelden voor nieuwe afleveringen en starten zelf geen extra aflevering."
                             : "Na het aanmaken maken we direct de eerste aflevering. Je hoeft niets te starten.")
            }
        }
        .scrollDismissesKeyboard(.interactively)
        .navigationTitle(editing ? "Podcast bewerken" : "Nieuwe podcast")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar { ToolbarItem(placement: .cancellationAction) { Button("Annuleer") { dismiss() } } }
        .onAppear(perform: populate)
    }

    @ViewBuilder private var coverThumb: some View {
        switch cover {
        case .new(_, let image): Image(uiImage: image).resizable().scaledToFill().frame(width: 48, height: 48).clipShape(RoundedRectangle(cornerRadius: 8))
        case .remove: CoverImage(url: nil, size: 48, radius: 8)
        case .keep: CoverImage(url: existing?.coverUrl, size: 48, radius: 8)
        }
    }

    @ViewBuilder private func fieldError(_ key: String) -> some View {
        if let text = errors[key] { Text(text).font(.footnote).foregroundStyle(Theme.negative) }
    }

    private func populate() {
        guard !loaded else { return }
        loaded = true
        time = Self.date(from: schedule.time)
        guard let p = existing else { return }
        title = p.title
        topics = p.topics.isEmpty ? [Entry(text: "")] : p.topics.map { Entry(text: $0.text) }
        sources = p.sources.map { DraftSource(url: $0.url, name: $0.name, error: $0.error) }
        duration = p.durationMinutes
        if !p.voice.voiceId.isEmpty { voice = p.voice }
        style = p.style
        schedule = p.schedule
        time = Self.date(from: p.schedule.time)
    }

    private static func date(from clock: String) -> Date {
        let parts = clock.split(separator: ":").compactMap { Int($0) }
        return Calendar.current.date(bySettingHour: parts.first ?? 7, minute: parts.count > 1 ? parts[1] : 0, second: 0, of: Date()) ?? Date()
    }

    private func addSource() async {
        let url = sourceDraft.trimmingCharacters(in: .whitespaces)
        guard !url.isEmpty else { return }
        if sources.contains(where: { $0.url == url }) { sourceDraft = ""; return }
        sourceBusy = true
        do {
            let info = try await APIClient.shared.checkSource(url)
            sources.append(DraftSource(url: info.error == nil ? info.url : url, name: info.name, error: info.error))
        } catch {
            sources.append(DraftSource(url: url, name: "", error: error.localizedDescription))
        }
        sourceDraft = ""; sourceBusy = false
    }

    private func submit() async {
        let clean = topics.map { $0.text.trimmingCharacters(in: .whitespacesAndNewlines) }.filter { !$0.isEmpty }
        var local: [String: String] = [:]
        if title.trimmingCharacters(in: .whitespaces).isEmpty { local["title"] = "Geef je podcast een naam" }
        if clean.isEmpty { local["topics"] = "Voeg minstens één onderwerp toe" }
        guard local.isEmpty else { errors = local; return }
        busy = true; errors = [:]
        var plan = schedule
        let parts = Calendar.current.dateComponents([.hour, .minute], from: time)
        plan.time = String(format: "%02d:%02d", parts.hour ?? 7, parts.minute ?? 0)
        plan.timezone = TimeZone.current.identifier
        plan.enabled = true
        let body = PodcastBody(title: title.trimmingCharacters(in: .whitespaces), topics: clean, sources: sources.map(\.url), durationMinutes: duration,
                               voiceId: voice.voiceId, voiceName: voice.name, style: style, schedule: plan)
        do {
            var saved = try await (editing ? APIClient.shared.updatePodcast(existing!.id, body) : APIClient.shared.createPodcast(body))
            do {
                switch cover {
                case .new(let data, _): saved = try await APIClient.shared.setCover(saved.id, jpeg: data)
                case .remove where editing: saved = try await APIClient.shared.deleteCover(saved.id)
                default: break
                }
            } catch { /* een mislukte omslag blokkeert de podcast niet */ }
            onSaved(saved)
        } catch let error as APIError {
            errors = error.fields.isEmpty ? ["form": error.message] : error.fields
            busy = false
        } catch {
            errors = ["form": error.localizedDescription]; busy = false
        }
    }
}
