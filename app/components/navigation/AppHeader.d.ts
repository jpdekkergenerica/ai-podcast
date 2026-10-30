/** Header for the 4 root tabs. Title is the screen's one Geist Pixel moment (display-s). */
export interface AppHeaderProps {
  title: string;
  name?: string;
  onAvatar?: () => void;
  onNotifications?: () => void;
  unread?: number;
  actions?: React.ReactNode;
  style?: React.CSSProperties;
}
export function AppHeader(props: AppHeaderProps): JSX.Element;
