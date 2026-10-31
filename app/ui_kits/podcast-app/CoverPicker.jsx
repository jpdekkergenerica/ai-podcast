import React, { useRef, useState } from "react";
import { Button } from "../../components/core/Button.jsx";
import { TopAppBar } from "../../components/navigation/TopAppBar.jsx";
import { Cover, FieldError, Muted, Page } from "./ui.jsx";

const SIDE = 1400; // Apple vraagt 1400–3000 px, vierkant

/** Leest een gekozen bestand, snijdt het midden uit tot een vierkant en geeft een JPEG als data-URL. */
export function squareJpeg(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      URL.revokeObjectURL(url);
      const side = Math.min(img.naturalWidth, img.naturalHeight);
      if (side < 600) return reject(new Error("De afbeelding is te klein (minimaal 600 bij 600 pixels)"));
      const canvas = document.createElement("canvas");
      canvas.width = canvas.height = SIDE;
      canvas.getContext("2d").drawImage(img, (img.naturalWidth - side) / 2, (img.naturalHeight - side) / 2, side, side, 0, 0, SIDE, SIDE);
      resolve(canvas.toDataURL("image/jpeg", 0.88));
    };
    img.onerror = () => { URL.revokeObjectURL(url); reject(new Error("Dit bestand is geen afbeelding die we kunnen gebruiken")); };
    img.src = url;
  });
}

/** Scherm 4 · Omslag kiezen: huidige of standaardomslag, kiezen of vervangen met voorbeeld, en verwijderen. */
export function CoverPicker({ current, hasCustom, onUse, onRemove, onBack }) {
  const input = useRef(null);
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const choose = async (e) => {
    const file = e.target.files && e.target.files[0];
    e.target.value = "";
    if (!file) return;
    setError("");
    try { setPreview(await squareJpeg(file)); } catch (err) { setError(err.message); }
  };
  const use = async () => {
    setBusy(true); setError("");
    try { await onUse(preview); } catch (err) { setError(err.message); setBusy(false); }
  };
  const remove = async () => {
    setBusy(true); setError("");
    try { await onRemove(); } catch (err) { setError(err.message); setBusy(false); }
  };

  return (
    <>
      <TopAppBar title="Omslag" onBack={onBack} />
      <Page>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
          <Cover url={preview || current} size={240} radius={16} />
          <Muted>{preview ? "Zo ziet je omslag eruit (vierkante uitsnede)" : hasCustom ? "Je eigen omslag" : "Standaardomslag met de naam van je podcast"}</Muted>
        </div>
        <input ref={input} type="file" accept="image/*" onChange={choose} style={{ display: "none" }} />
        <FieldError>{error}</FieldError>
        {preview && <Button fullWidth loading={busy} onClick={use}>Gebruik deze afbeelding</Button>}
        <Button fullWidth variant={preview ? "secondary" : "primary"} disabled={busy} onClick={() => input.current.click()}>
          {hasCustom || preview ? "Vervangen" : "Kiezen"}
        </Button>
        {(hasCustom || preview) && !busy && (
          <Button fullWidth variant="tertiary" onClick={preview ? () => setPreview(null) : remove}>
            {preview ? "Andere afbeelding" : "Eigen omslag verwijderen"}
          </Button>
        )}
        <Muted>Een omslag is optioneel. Zonder eigen afbeelding gebruiken we een standaardomslag.</Muted>
      </Page>
    </>
  );
}
