/** Search input (transactions). Accepts free text and amounts ("45k"). */
export interface SearchFieldProps {
  value?: string;
  onChange?: (v: string) => void;
  placeholder?: string;
  /** Shows trailing "Huỷ". */
  onCancel?: () => void;
  style?: React.CSSProperties;
}
export function SearchField(props: SearchFieldProps): JSX.Element;
