import { useCallback, useLayoutEffect, useRef, useState } from 'react';
import { ButtonBase } from '@mui/material';
import type { ReactNode } from 'react';
import { useStyles } from './SegmentedControlStyles';

export interface SegmentedOption<T extends string> {
  value: T;
  label: string;
  icon?: ReactNode;
}

export interface SegmentedControlProps<T extends string> {
  options: SegmentedOption<T>[];
  value: T;
  onChange: (value: T) => void;
  small?: boolean;
  ariaLabel?: string;
  testId?: string;
}

/** Where the sliding highlight should sit, in pixels from the track's start. */
interface ThumbGeometry {
  left: number;
  width: number;
}

/**
 * A row of mutually exclusive options with a sliding highlight.
 *
 * Replaces a row of independent toggle buttons: a segmented control makes the
 * active selection unambiguous and cannot silently deselect itself.
 *
 * The highlight is positioned by **measuring the active option** rather than
 * assuming every option is the same width. Options are sized by their label, and
 * Hebrew labels differ in length — dividing the track into equal shares put the
 * first option right and every later one progressively further off, sometimes not
 * covering the label at all. Measured geometry is also direction-agnostic, since
 * `getBoundingClientRect` reports physical pixels either way.
 */
export const SegmentedControl = <T extends string>({
  options,
  value,
  onChange,
  small = false,
  ariaLabel,
  testId,
}: SegmentedControlProps<T>) => {
  const { classes, cx } = useStyles({ small });

  const trackRef = useRef<HTMLDivElement | null>(null);
  const optionRefs = useRef(new Map<T, HTMLButtonElement>());
  const [thumb, setThumb] = useState<ThumbGeometry | null>(null);

  // False for the very first placement, so the highlight appears where it
  // belongs instead of sliding in from the edge on mount.
  const hasPlaced = useRef(false);

  const measure = useCallback(() => {
    const track = trackRef.current;
    const active = optionRefs.current.get(value);
    if (!track || !active) return;

    const trackBox = track.getBoundingClientRect();
    const activeBox = active.getBoundingClientRect();

    setThumb((previous) => {
      if (previous !== null) hasPlaced.current = true;
      return { left: activeBox.left - trackBox.left, width: activeBox.width };
    });
  }, [value]);

  // Layout effect rather than effect: measuring after paint would show the
  // highlight in its old position for a frame.
  useLayoutEffect(() => {
    measure();
  }, [measure, options.length]);

  // Labels can reflow after a webfont loads or the container resizes, which
  // would leave the highlight stranded where the old layout put it.
  useLayoutEffect(() => {
    if (typeof ResizeObserver === 'undefined') return;

    const observer = new ResizeObserver(measure);
    if (trackRef.current) observer.observe(trackRef.current);
    optionRefs.current.forEach((node) => observer.observe(node));

    return () => observer.disconnect();
  }, [measure, options.length]);

  return (
    <div
      ref={trackRef}
      className={classes.root}
      role="tablist"
      aria-label={ariaLabel}
      data-testid={testId}
    >
      {/* Hidden until measured, so it never flashes at the wrong place. */}
      {thumb && (
        <span
          className={classes.thumb}
          aria-hidden="true"
          // `right: auto` is required, not decorative: the RTL plugin turns the
          // class's horizontal rules into `right`, and left + right + width
          // together over-constrain the box, at which point RTL discards `left`.
          style={{
            left: thumb.left,
            width: thumb.width,
            right: 'auto',
            // Inline, because the RTL plugin rewrites `left` to `right` inside a
            // transition list as readily as in a declaration — leaving the
            // highlight animating a property nothing ever sets.
            transition: hasPlaced.current
              ? 'left .34s cubic-bezier(.22,.61,.36,1), width .34s cubic-bezier(.22,.61,.36,1)'
              : 'none',
          }}
        />
      )}

      {options.map((option) => {
        const isActive = option.value === value;

        return (
          <ButtonBase
            key={option.value}
            ref={(node) => {
              if (node) optionRefs.current.set(option.value, node);
              else optionRefs.current.delete(option.value);
            }}
            role="tab"
            aria-selected={isActive}
            className={cx(classes.option, isActive && classes.optionActive)}
            onClick={() => onChange(option.value)}
          >
            {option.icon && <span className={classes.optionIcon}>{option.icon}</span>}
            {option.label}
          </ButtonBase>
        );
      })}
    </div>
  );
};
