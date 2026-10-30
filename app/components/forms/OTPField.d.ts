/** One-time-code entry (6 digits, Geist Pixel digits at 24px). */
export interface OTPFieldProps {
  value?: string;
  length?: number;
  onChange?: (v: string) => void;
  error?: string;
  autoFocus?: boolean;
  style?: React.CSSProperties;
}
export function OTPField(props: OTPFieldProps): JSX.Element;
