/** Transient feedback above the tab bar. 4s default; with action 6s. */
export interface ToastProps {
  message: string;
  action?: string;
  onAction?: () => void;
  icon?: string;
  variant?: "default" | "error";
  style?: React.CSSProperties;
}
export function Toast(props: ToastProps): JSX.Element;
