/** 2–4 mutually exclusive options (period switcher: Tuần / Tháng / Năm). */
export interface SegmentedControlProps {
  options: Array<string | { value: string; label: string }>;
  value?: string;
  onChange?: (value: string) => void;
  /** sm 32 · md 40. */
  size?: "sm" | "md";
  disabled?: boolean;
  style?: React.CSSProperties;
}
export function SegmentedControl(props: SegmentedControlProps): JSX.Element;
