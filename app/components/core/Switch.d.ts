/** Square on/off toggle for settings. Pair with ListRow. */
export interface SwitchProps {
  checked?: boolean;
  onChange?: (v: boolean) => void;
  disabled?: boolean;
  label?: string;
  style?: React.CSSProperties;
}
export function Switch(props: SwitchProps): JSX.Element;
