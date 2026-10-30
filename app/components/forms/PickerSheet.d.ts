/** Wallet or category picker inside a BottomSheet. */
export interface PickerSheetProps {
  type?: "category" | "wallet";
  open?: boolean;
  value?: string;
  wallets?: Array<{ id?: string; name: string; balance?: number; currency?: string; icon?: string }>;
  onSelect?: (id: string) => void;
  onClose?: () => void;
  /** Render in-flow (docs). */
  inline?: boolean;
  title?: string;
}
export function PickerSheet(props: PickerSheetProps): JSX.Element;
