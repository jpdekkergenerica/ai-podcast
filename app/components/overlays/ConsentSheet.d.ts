/** Permission / data-consent sheet for AI processing, microphone or camera. */
export interface ConsentSheetProps {
  open?: boolean;
  kind?: "ai" | "mic" | "camera";
  onAccept?: (c: { processing: boolean; improve: boolean }) => void;
  onDecline?: () => void;
  inline?: boolean;
}
export function ConsentSheet(props: ConsentSheetProps): JSX.Element | null;
