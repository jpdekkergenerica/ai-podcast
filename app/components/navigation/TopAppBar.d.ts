/** Top app bar. "large" puts the screen title in Geist Pixel (display-m) — one per screen. */
export interface TopAppBarProps {
  title?: string;
  variant?: "small" | "large";
  leading?: React.ReactNode;
  onBack?: () => void;
  onClose?: () => void;
  /** Trailing IconButtons. */
  actions?: React.ReactNode;
  subtitle?: string;
  divider?: boolean;
  style?: React.CSSProperties;
}
export function TopAppBar(props: TopAppBarProps): JSX.Element;
