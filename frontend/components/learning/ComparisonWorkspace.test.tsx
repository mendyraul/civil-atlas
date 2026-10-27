import { act, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import type { AtlasCamera } from '../../types/atlas';

type MapProps = {
  cameraCommand: AtlasCamera;
  onCameraChange: (camera: AtlasCamera, origin?: 'interaction' | 'command') => void;
};
const maps = vi.hoisted(() => new Map<string, MapProps>());
vi.mock('../map/AtlasMap', () => ({ AtlasMap: (props: MapProps) => {
  // The rendered wrappers provide stable identities independently of rerenders.
  return <div ref={(element) => {
    if (element) maps.set(element.closest('section')!.getAttribute('aria-label')!.split(' ')[0], props);
  }} aria-label="Mock map" />;
} }));
vi.mock('../atlas/hooks/useAtlasData', () => ({ useAtlasData: (year: number) => ({
  world: { year, civilizations: [], nodes: [], routes: [], layers: [], relationships: [], eras: [], events: [] },
  status: 'demo', sources: [],
}) }));
import { ComparisonWorkspace } from './ComparisonWorkspace';

beforeEach(() => { history.replaceState(null, '', '/compare'); maps.clear(); });

it('observes follower commands without feeding stale positions back into linked cameras', async () => {
  render(<ComparisonWorkspace />);
  await waitFor(() => expect(maps.size).toBe(2));
  const view = (zoom: number): AtlasCamera => ({ center: [30, 30], zoom, bearing: 0, pitch: 0 });
  act(() => { maps.get('Left')!.onCameraChange(view(2.8), 'interaction'); });
  act(() => { maps.get('Left')!.onCameraChange(view(3.8), 'interaction'); });
  act(() => { maps.get('Right')!.onCameraChange(view(2.8), 'command'); });
  expect(maps.get('Left')!.cameraCommand.zoom).toBe(3.8);
  expect(maps.get('Right')!.cameraCommand.zoom).toBe(3.8);
  expect(screen.getByLabelText('Right camera')).toHaveTextContent('zoom 2.80');
  act(() => { maps.get('Right')!.onCameraChange(view(3.8), 'command'); });
  expect(screen.getByLabelText('Right camera')).toHaveTextContent('zoom 3.80');
  act(() => { maps.get('Right')!.onCameraChange(view(4.8), 'interaction'); });
  expect(maps.get('Left')!.cameraCommand.zoom).toBe(4.8);
  expect(maps.get('Right')!.cameraCommand.zoom).toBe(4.8);
  expect(screen.getByLabelText('Left year')).toHaveValue(117);
  expect(screen.getByLabelText('Right year')).toHaveValue(123);
});
