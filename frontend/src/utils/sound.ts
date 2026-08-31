/**
 * A short alert tone for a scheduled-automation failure, synthesised with the
 * Web Audio API rather than shipped as an audio file — nothing to load, and
 * nothing that can 404.
 *
 * Deliberately independent of the desktop Notification permission: a viewer
 * who has not granted (or has denied) that permission still hears this, since
 * it needs none of its own.
 */

let sharedContext: AudioContext | null = null;

const getContext = (): AudioContext | null => {
  const Ctor = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!Ctor) return null;
  sharedContext ??= new Ctor();
  return sharedContext;
};

/** One short tone at `frequency`, starting `delay` seconds from now. */
const scheduleTone = (
  context: AudioContext,
  frequency: number,
  startDelay: number,
  duration: number,
): void => {
  const oscillator = context.createOscillator();
  const gain = context.createGain();

  oscillator.type = 'sine';
  oscillator.frequency.value = frequency;
  oscillator.connect(gain);
  gain.connect(context.destination);

  const startAt = context.currentTime + startDelay;
  const endAt = startAt + duration;

  // A short fade in/out avoids the audible click a hard on/off produces.
  gain.gain.setValueAtTime(0, startAt);
  gain.gain.linearRampToValueAtTime(0.2, startAt + 0.02);
  gain.gain.linearRampToValueAtTime(0, endAt);

  oscillator.start(startAt);
  oscillator.stop(endAt);
};

/**
 * Play a short two-tone alert, the way a monitoring dashboard signals a fresh
 * failure. Silently does nothing if the Web Audio API is unavailable, or if
 * the browser has not yet let audio play in this tab (autoplay policies
 * require a prior user gesture somewhere on the page — normal navigation
 * within the app satisfies that after the first click).
 */
export function playFailureAlert(): void {
  const context = getContext();
  if (!context) return;

  if (context.state === 'suspended') {
    void context.resume().catch(() => undefined);
  }

  scheduleTone(context, 880, 0, 0.15);
  scheduleTone(context, 660, 0.18, 0.22);
}
