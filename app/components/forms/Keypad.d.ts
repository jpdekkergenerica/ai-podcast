export function applyKey(expression: string, key: string): string;
/** Numeric + calculator keypad for AmountField. Keys: 0–9, 000, + − × ÷, =, C, back, done. */
export interface KeypadProps {
  onKey?: (key: string) => void;
  style?: React.CSSProperties;
}
export function Keypad(props: KeypadProps): JSX.Element;
