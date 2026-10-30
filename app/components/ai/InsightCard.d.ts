/** AI insight: one observation + one action. Max one visible on Home. */
export interface InsightCardProps {
  title: string;
  children?: React.ReactNode;
  icon?: string;
  /** Badge signal: info (neutral insight, default) · warning (early warning) · negative (problem) · positive (good news). */
  tone?: "info" | "warning" | "negative" | "positive";
  action?: string;
  onAction?: () => void;
  /** Optional mini chart / BudgetBar. */
  visual?: React.ReactNode;
  onDismiss?: () => void;
  style?: React.CSSProperties;
}
export function InsightCard(props: InsightCardProps): JSX.Element;
