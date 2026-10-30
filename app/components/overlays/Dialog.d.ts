/** Confirmation dialog. Destructive: verb label naming the object ("Xoá ví"), never "OK". */
export interface DialogProps {
  open?: boolean;
  title: string;
  children?: React.ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm?: () => void;
  onCancel?: () => void;
  destructive?: boolean;
  inline?: boolean;
  loading?: boolean;
}
export function Dialog(props: DialogProps): JSX.Element | null;
