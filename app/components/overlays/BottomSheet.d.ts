/** Bottom sheet with scrim, 32×4 block grabber, title + close. Fills its positioned parent. */
export interface BottomSheetProps {
  open?: boolean;
  title?: string;
  onClose?: () => void;
  children?: React.ReactNode;
  /** Sticky actions area. */
  footer?: React.ReactNode;
  /** Render without scrim/positioning (docs, stacked previews). */
  inline?: boolean;
  style?: React.CSSProperties;
}
export function BottomSheet(props: BottomSheetProps): JSX.Element | null;
