/** Section/screen error. Thick border + icon + text — never red. */
export interface ErrorStateProps {
  title?: string;
  children?: React.ReactNode;
  action?: string;
  onAction?: () => void;
  style?: React.CSSProperties;
}
export function ErrorState(props: ErrorStateProps): JSX.Element;
