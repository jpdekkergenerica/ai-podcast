export type IconName =
  | "buildings" | "users" | "download" | "link" | "shield" | "building" | "external-link" | "trophy" | "mood-sad" | "gift" | "upload" | "mail" | "archive" | "shopping-bag" | "store" | "sort" | "sync" | "copy" | "cloud-upload" | "repeat" | "bookmark" | "mood-happy" | "hourglass" | "chart" | "flag" | "menu" | "inbox" | "cart" | "label" | "toggle-right" | "speed-fast" | "bitcoin" | "device-phone" | "calendar-month" | "mood-neutral" | "lightbulb" | "dollar" | "script-text" | "logout" | "analytics" | "card-stack" | "notes" | "map" | "human" | "toggle-left"
  | "coffee" | "shopping-bag" | "home" | "car" | "gamepad" | "heart" | "book-open" | "reciept" | "coin"
  | "arrows-horizontal" | "bullseye-arrow" | "more-horizontal" | "mic" | "camera" | "plus" | "minus" | "close"
  | "arrow-left" | "arrow-right" | "chevron-right" | "chevron-left" | "chevron-down" | "chevron-up" | "search"
  | "calendar" | "check" | "alert" | "warning-box" | "trash" | "edit" | "notification" | "paperclip" | "image"
  | "calculator" | "wallet" | "dashboard" | "list" | "chart-bar" | "user" | "sliders" | "lock" | "info-box"
  | "cellular-signal-off" | "reload" | "zap" | "message" | "eye" | "eye-closed" | "more-vertical" | "loader"
  | "sun" | "moon" | "credit-card" | "trending-up" | "trending-down" | "clock";

/** Pixel icon (pixelarticons, 24×24, 2px pixel strokes). Outline by default; filled = inverted tile for active/selected. */
export interface IconProps {
  name: IconName;
  /** 24 (default) or 48 — integer multiples only to stay pixel-honest. Default 24. */
  size?: 24 | 48 | 16;
  /** Active/selected state: glyph knocked out of a solid tile. */
  filled?: boolean;
  color?: string;
  /** Accessible label; omit for decorative icons. */
  title?: string;
  style?: React.CSSProperties;
}
export function Icon(props: IconProps): JSX.Element;
