/** Offline indicator with count of unsynced transactions. */
export interface OfflineBannerProps {
  pending?: number;
  style?: React.CSSProperties;
}
export function OfflineBanner(props: OfflineBannerProps): JSX.Element;
