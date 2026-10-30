export type CategoryKey = "food" | "shopping" | "housing" | "transport" | "entertainment" | "health" | "education" | "bills" | "income" | "transfer" | "savings" | "other";
export const CATEGORIES: Record<CategoryKey, { label: string; icon: string }>;
/** Square bordered tile with a category's pixel glyph; used in rows, pickers, confirmation cards. */
export interface CategoryIconProps {
  category?: CategoryKey;
  /** Inverted (filled) tile. */
  selected?: boolean;
  /** Tile edge in px; multiple of 4. Default 40. */
  size?: number;
  style?: React.CSSProperties;
}
export function CategoryIcon(props: CategoryIconProps): JSX.Element;
