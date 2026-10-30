/** Calendar month grid (Monday-first) with "Hôm nay / Hôm qua" shortcuts. Place inside a BottomSheet. */
export interface DatePickerProps {
  value?: Date;
  /** Reference "today". */
  today?: Date;
  onChange?: (d: Date) => void;
  /** Default false — future dates disabled for spending. */
  allowFuture?: boolean;
  style?: React.CSSProperties;
}
export function DatePicker(props: DatePickerProps): JSX.Element;
