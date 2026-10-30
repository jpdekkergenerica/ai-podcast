export function evalExpr(expr: string): number;
/** Big pixel amount readout for manual entry; pairs with Keypad. */
export interface AmountFieldProps {
  /** Raw digits/operators, e.g. "45000+20000". Operators: + − × ÷ */
  expression?: string;
  kind?: "income" | "expense" | "transfer";
  currency?: string;
  focused?: boolean;
  error?: string;
  label?: string;
  style?: React.CSSProperties;
}
export function AmountField(props: AmountFieldProps): JSX.Element;
