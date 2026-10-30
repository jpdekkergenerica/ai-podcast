/** Floating action button — 56×56 black square; the main "add" entry. Max one per screen. */
export interface FABProps {
  icon?: string;
  /** Accessible name / extended label. Default "Thêm giao dịch". */
  label?: string;
  /** Show label beside icon. */
  extended?: boolean;
  disabled?: boolean;
  forceState?: "pressed" | "focused";
  onClick?: (e: React.MouseEvent) => void;
  style?: React.CSSProperties;
}
export function FAB(props: FABProps): JSX.Element;
