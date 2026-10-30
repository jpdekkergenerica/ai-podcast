export const DEFAULT_TABS: Array<{ value: string; label: string; icon: string }>;
/** Bottom tab bar — 4 tabs (Tổng quan · Phân tích · Kế hoạch · Tài sản) with optional centre ⊕ Ghi cell (inverted, same height). */
export interface TabBarProps {
  tabs?: Array<{ value: string; label: string; icon: string }>;
  value?: string;
  onChange?: (v: string) => void;
  /** Present → renders the centre inverted ⊕ cell (global capture). */
  onCenter?: () => void;
  centerLabel?: string;
  centerPressed?: boolean;
  style?: React.CSSProperties;
}
export function TabBar(props: TabBarProps): JSX.Element;
