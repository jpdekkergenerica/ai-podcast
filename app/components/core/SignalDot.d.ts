/** Hardware-style indicator light. Paper: flat 6px square. LED: same square with 4px glow. */
export interface SignalDotProps {
  tone?: "positive" | "negative" | "warning" | "info";
  /** Stepped blink for pending states (processing, upcoming charge). */
  pending?: boolean;
  size?: number;
  label?: string;
  style?: React.CSSProperties;
}
export function SignalDot(props: SignalDotProps): JSX.Element;
