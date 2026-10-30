/** Onboarding pager dots (square). */
export interface PageDotsProps {
  count?: number;
  index?: number;
  onChange?: (i: number) => void;
  style?: React.CSSProperties;
}
export function PageDots(props: PageDotsProps): JSX.Element;
