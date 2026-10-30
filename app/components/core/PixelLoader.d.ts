/** Stepped 3-block loader for buttons, processing states and inline waits. */
export interface PixelLoaderProps {
  /** Block edge in px (4 default, 8 for full-screen). */
  size?: 4 | 8;
  color?: string;
  /** Accessible status label. Default "Đang xử lý". */
  label?: string;
}
export function PixelLoader(props: PixelLoaderProps): JSX.Element;
