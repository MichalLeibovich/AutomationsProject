import { atom } from 'jotai';
import type { TestRun } from '@/types/run.types';

export interface DayPanelEntry {
  kind: 'day';
  date: string;
}

export interface RunPanelEntry {
  kind: 'run';
  run: TestRun;
}

export type PanelEntry = DayPanelEntry | RunPanelEntry;

/**
 * A navigation stack, not nested overlays. Opening a run from a day pushes
 * onto the stack and the panel content slides sideways; it never stacks a
 * second modal on top of the first.
 */
export const panelStackAtom = atom<PanelEntry[]>([]);

export const panelTopAtom = atom<PanelEntry | null>((get) => {
  const stack = get(panelStackAtom);
  return stack.length > 0 ? (stack[stack.length - 1] ?? null) : null;
});

export const panelDepthAtom = atom((get) => get(panelStackAtom).length);

export const panelCanGoBackAtom = atom((get) => get(panelStackAtom).length > 1);

export const openDayPanelAtom = atom(null, (_get, set, date: string) => {
  set(panelStackAtom, [{ kind: 'day', date }]);
});

export const openRunPanelAtom = atom(null, (_get, set, run: TestRun) => {
  set(panelStackAtom, [{ kind: 'run', run }]);
});

export const pushRunPanelAtom = atom(null, (get, set, run: TestRun) => {
  set(panelStackAtom, [...get(panelStackAtom), { kind: 'run', run }]);
});

export const panelBackAtom = atom(null, (get, set) => {
  set(panelStackAtom, get(panelStackAtom).slice(0, -1));
});

export const closePanelAtom = atom(null, (_get, set) => {
  set(panelStackAtom, []);
});
