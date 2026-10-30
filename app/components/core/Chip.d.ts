/**
 * Filter/choice chip, 32px tall with 4px radius (the system's only rounded element). variant="code" is the 20px currency-code chip.
 */
export interface ChipProps {
  children?: React.ReactNode;
  /** Selected → inverted fill. */
  selected?: boolean;
  disabled?: boolean;
  icon?: string;
  /** Shows a trailing ✕ that calls this. */
  onRemove?: () => void;
  variant?: "filter" | "code";
  onClick?: (e: React.MouseEvent) => void;
  forceState?: "pressed" | "focused";
  style?: React.CSSProperties;
}
export function Chip(props: ChipProps): JSX.Element;
