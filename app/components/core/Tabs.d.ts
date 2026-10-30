/** Underlined text tabs for in-page sections (Chi tiêu / Thu nhập / Chuyển khoản). */
export interface TabsProps {
  tabs: Array<string | { value: string; label: string; count?: number }>;
  value?: string;
  onChange?: (value: string) => void;
  style?: React.CSSProperties;
}
export function Tabs(props: TabsProps): JSX.Element;
