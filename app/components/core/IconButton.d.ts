/** Square icon-only button, min 44×44. Always pass an accessible label. */
export interface IconButtonProps {
  icon: string;
  /** Required accessible name (Vietnamese), e.g. "Quay lại". */
  label: string;
  variant?: "ghost" | "outline" | "filled";
  /** Edge in px, ≥44. Default 44. */
  size?: number;
  disabled?: boolean;
  loading?: boolean;
  /** Toggle on — renders inverted. */
  selected?: boolean;
  forceState?: "pressed" | "focused";
  onClick?: (e: React.MouseEvent) => void;
  style?: React.CSSProperties;
}
export function IconButton(props: IconButtonProps): JSX.Element;
