import React, { useState } from "react";
import { TopAppBar } from "../../components/navigation/TopAppBar.jsx";
import { ListRow } from "../../components/core/ListRow.jsx";
import { Button } from "../../components/core/Button.jsx";
import { TextField } from "../../components/forms/TextField.jsx";
import { EmptyState } from "../../components/feedback/EmptyState.jsx";
export function Topics({ show, onBack, onSave, onTest }) {
  const [topics, setTopics] = useState(() => (show.topics || []).map((t) => ({ ...t })));
  const [edit, setEdit] = useState(null); // index or "new"
  const [draft, setDraft] = useState({ name: "", description: "", keywords: "", feeds: "" });
  const [busy, setBusy] = useState(false);
  const [testOut, setTestOut] = useState(null);
  const [error, setError] = useState("");

  const openNew = () => {
    setDraft({ name: "", description: "", keywords: "", feeds: "" });
    setEdit("new");
    setTestOut(null);
    setError("");
  };

  const openEdit = (i) => {
    const t = topics[i];
    setDraft({
      name: t.name,
      description: t.description || "",
      keywords: (t.keywords || []).join(", "),
      feeds: (t.feeds || []).join("\n"),
    });
    setEdit(i);
    setTestOut(null);
    setError("");
  };

  const toTopic = () => ({
    name: draft.name.trim(),
    description: draft.description.trim(),
    keywords: draft.keywords.split(",").map((k) => k.trim()).filter(Boolean),
    feeds: draft.feeds.split("\n").map((f) => f.trim()).filter(Boolean),
    sort_order: typeof edit === "number" ? edit : topics.length,
  });

  const saveDraft = async () => {
    const t = toTopic();
    if (!t.name || !t.feeds.length) {
      setError("Naam en minstens één feed zijn verplicht");
      return;
    }
    const next = [...topics];
    if (edit === "new") next.push(t);
    else next[edit] = { ...next[edit], ...t };
    setBusy(true); setError("");
    try {
      await onSave(next);
      setTopics(next);
      setEdit(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    if (edit === "new") { setEdit(null); return; }
    const next = topics.filter((_, i) => i !== edit);
    setBusy(true);
    try {
      await onSave(next);
      setTopics(next);
      setEdit(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const runTest = async () => {
    setBusy(true); setTestOut(null);
    try {
      const rows = await onTest(toTopic());
      setTestOut(rows);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  if (edit != null) {
    return (
      <>
        <TopAppBar title={edit === "new" ? "Nieuw onderwerp" : "Onderwerp"} onBack={() => setEdit(null)} />
        <div style={{ flex: 1, overflowY: "auto", padding: 16, display: "flex", flexDirection: "column", gap: 12 }}>
          <TextField label="Naam" value={draft.name} onChange={(v) => setDraft({ ...draft, name: v })} />
          <TextField label="Beschrijving" value={draft.description} onChange={(v) => setDraft({ ...draft, description: v })} />
          <TextField label="Trefwoorden" value={draft.keywords} onChange={(v) => setDraft({ ...draft, keywords: v })}
            helper="Komma-gescheiden, regex mag (bijv. \\bAI\\b)" />
          <TextField label="RSS-feeds" value={draft.feeds} onChange={(v) => setDraft({ ...draft, feeds: v })}
            helper="Eén URL per regel" />
          {error && <span style={{ font: "var(--type-body-small)", color: "var(--negative-text)" }}>{error}</span>}
          {testOut && (
            <div style={{ border: "var(--border-1) solid var(--border-default)", padding: 12, display: "flex", flexDirection: "column", gap: 8 }}>
              {testOut.map((r) => (
                <div key={r.url} style={{ font: "var(--type-body-small)" }}>
                  <div style={{ fontWeight: 600 }}>{r.url.replace(/^https?:\/\//, "").slice(0, 48)}</div>
                  {r.error ? <span style={{ color: "var(--negative-text)" }}>{r.error}</span>
                    : <span style={{ color: "var(--text-secondary)" }}>{r.matches} treffers · {r.recent} recent</span>}
                  {(r.samples || []).map((s) => <div key={s} style={{ color: "var(--text-tertiary)" }}>· {s}</div>)}
                </div>
              ))}
            </div>
          )}
          <Button fullWidth variant="secondary" loading={busy} onClick={runTest}>Test feeds</Button>
          <Button fullWidth loading={busy} onClick={saveDraft}>Opslaan</Button>
          {edit !== "new" && <Button fullWidth variant="destructive" loading={busy} onClick={remove}>Onderwerp verwijderen</Button>}
        </div>
      </>
    );
  }

  return (
    <>
      <TopAppBar title="Onderwerpen" onBack={onBack} actions={<Button size="sm" variant="tertiary" onClick={openNew}>Toevoegen</Button>} />
      <div style={{ flex: 1, overflowY: "auto" }}>
        {!topics.length ? (
          <div style={{ padding: 24 }}>
            <EmptyState title="Nog geen onderwerpen" action="Eerste onderwerp" onAction={openNew}>
              Jij bedenkt ze. Wij halen er elke ochtend het nieuws bij.
            </EmptyState>
          </div>
        ) : topics.map((t, i) => (
          <ListRow key={t.id || t.name + i} icon="flag" label={t.name}
            description={`${(t.feeds || []).length} feeds · ${(t.keywords || []).length} trefwoorden`}
            onClick={() => openEdit(i)} divider={i > 0} />
        ))}
      </div>
      <div style={{ padding: 16 }}>
        <Button fullWidth icon="plus" onClick={openNew}>Onderwerp toevoegen</Button>
      </div>
    </>
  );
}
