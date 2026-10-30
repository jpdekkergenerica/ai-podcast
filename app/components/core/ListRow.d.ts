/** Generic row for settings, menus and navigation lists. */
export interface ListRowProps {
  icon?: string;
  label: React.ReactNode;
  description?: string;
  value?: React.ReactNode;
  /** Replaces the chevron, e.g. <Switch/>. */
  trailing?: React.ReactNode;
  chevron?: boolean;
  onClick?: () => void;
  /** Shows PRO code chip. */
  pro?: boolean;
  /** Destructive row (Xoá tài khoản): bold + filled icon. */
  danger?: boolean;
  divider?: boolean;
  style?: React.CSSProperties;
}
export function ListRow(props: ListRowProps): JSX.Element;
