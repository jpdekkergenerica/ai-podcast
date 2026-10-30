/** Loading placeholder. variant="row" mimics a TransactionRow. Shimmer is stepped; static under Reduce Motion. */
export interface SkeletonProps {
  width?: number | string;
  height?: number;
  variant?: "block" | "row";
  style?: React.CSSProperties;
}
export function Skeleton(props: SkeletonProps): JSX.Element;
