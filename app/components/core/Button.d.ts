/**
 * Text button. primary = black fill (one per view), secondary = 1px outline, tertiary = underlined text,
 * destructive = black fill + mandatory warning icon + explicit verb ("Xoá ví").
 * @startingPoint section="Core" subtitle="Buttons in every variant and state" viewport="700x520"
 */
export interface ButtonProps {
  variant?: "primary" | "secondary" | "tertiary" | "destructive";
  /** sm 36 · md 48 · lg 56 (visual height; hit area ≥44). Default md. */
  size?: "sm" | "md" | "lg";
  children?: React.ReactNode;
  /** Leading icon name. Destructive defaults to "warning-box". */
  icon?: string;
  iconRight?: string;
  disabled?: boolean;
  /** Replaces label with PixelLoader and blocks input. */
  loading?: boolean;
  fullWidth?: boolean;
  /** Docs only — force a visual state. */
  forceState?: "pressed" | "focused";
  onClick?: (e: React.MouseEvent) => void;
  type?: "button" | "submit";
  style?: React.CSSProperties;
}
export function Button(props: ButtonProps): JSX.Element;
