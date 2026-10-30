/** 1-bit pixel-art illustration slot for empty states & onboarding. Render with image-rendering: pixelated at integer scale. */
export interface IllustrationProps {
  /** PNG/SVG, 1-bit, drawn on a 64×64 or 32×32 grid. */
  src?: string;
  alt?: string;
  /** Integer multiple of the art grid (64 → 128, 192). */
  size?: number;
  /** Placeholder caption. */
  label?: string;
  style?: React.CSSProperties;
}
export function Illustration(props: IllustrationProps): JSX.Element;
