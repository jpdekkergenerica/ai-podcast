/** Square avatar (initials on black, or grayscale photo). Tap target padded to 44. */
export interface AvatarProps {
  name?: string;
  src?: string;
  /** 24 · 32 · 40 · 64 */
  size?: number;
  onClick?: () => void;
  label?: string;
  style?: React.CSSProperties;
}
export function Avatar(props: AvatarProps): JSX.Element;
