/** Empty state — the one place besides balances where Geist Pixel headlines appear inside content. */
export interface EmptyStateProps {
  title: string;
  children?: React.ReactNode;
  action?: string;
  onAction?: () => void;
  illustration?: string;
  illustrationLabel?: string;
  /** No illustration (inside cards/lists). */
  compact?: boolean;
  style?: React.CSSProperties;
}
export function EmptyState(props: EmptyStateProps): JSX.Element;
