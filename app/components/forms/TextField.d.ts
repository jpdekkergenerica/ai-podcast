/** Labeled single-line input. Error state: 2px border + alert icon + message (never color). */
export interface TextFieldProps {
  label?: string;
  value?: string;
  defaultValue?: string;
  onChange?: (v: string) => void;
  placeholder?: string;
  helper?: string;
  error?: string;
  disabled?: boolean;
  /** Leading icon name. */
  icon?: string;
  trailing?: React.ReactNode;
  forceState?: "focused";
  type?: string;
  inputMode?: "text" | "numeric" | "decimal" | "search";
  style?: React.CSSProperties;
}
export function TextField(props: TextFieldProps): JSX.Element;
