import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
vi.mock('../../lib/atlas', async () => { const actual = await vi.importActual<typeof import('../../lib/atlas')>('../../lib/atlas'); return { ...actual, DEMO_MODE: true, HAS_REMOTE_API: false }; });
const mapProps = vi.hoisted(() => vi.fn());
vi.mock('../map/AtlasMap', () => ({ AtlasMap: (props: unknown) => { mapProps(props); return <div aria-label="map loaded" />; } }));
import { AtlasClient } from './AtlasClient';

describe('AtlasClient', () => {
  beforeEach(() => { history.replaceState(null, '', '/atlas'); mapProps.mockClear(); });
  it('hydrates year and selection while panels start closed', async () => {
    history.replaceState(null, '', '/atlas?y=117&sel=roman-empire');
    render(<AtlasClient />);
    expect((await screen.findAllByText('117 CE')).length).toBeGreaterThan(0);
    expect(screen.queryByRole('region', { name: 'Selection and evidence' })).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: /Selection & evidence/ }));
    expect(screen.getByRole('heading', { name: 'Roman Empire' })).toBeVisible();
  });
  it('opens filters, resets them, and restores focus on Escape', async () => {
    render(<AtlasClient />); const user = userEvent.setup();
    const trigger = screen.getByRole('button', { name: /Layers & research/ });
    await user.click(trigger);
    await user.click(screen.getByRole('button', { name: /^reviewed/i }));
    await user.click(screen.getByRole('button', { name: /reset/i }));
    await user.keyboard('{Escape}');
    expect(trigger).toHaveFocus();
    expect(trigger).toHaveAttribute('aria-expanded', 'false');
  });
  it('restores camera orientation and hidden boundary choices', async () => {
    history.replaceState(null, '', '/atlas?y=117&lng=100&lat=35&z=3&bearing=25&pitch=30&hiddenBoundaries=roman-campaign');
    render(<AtlasClient />);
    await waitFor(() => expect(mapProps).toHaveBeenCalled());
    const props = mapProps.mock.lastCall![0];
    expect(props.cameraCommand).toEqual({ center: [100, 35], zoom: 3, bearing: 25, pitch: 30 });
    expect(window.location.search).toContain('hiddenBoundaries=roman-campaign');
  });
  it('toggles the modern reference independently and preserves it in the URL', async () => {
    render(<AtlasClient />);
    await userEvent.click(screen.getByRole('button', { name: /Layers & research/ }));
    expect(mapProps.mock.lastCall![0].showModernBorders).toBe(true);
    await userEvent.click(screen.getByRole('button', { name: /^Present-day borders/ }));
    expect(mapProps.mock.lastCall![0].showModernBorders).toBe(false);
    expect(window.location.search).toContain('modernBorders=false');
  });
  it('applies chapter camera commands and removes chapter URL state when leaving guided mode', async () => {
    render(<AtlasClient />); const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: 'Guided lesson' }));
    await user.click(screen.getByRole('button', { name: /2\. Corridors/ }));
    await waitFor(() => expect(mapProps.mock.lastCall![0].cameraCommand.center).toEqual([105, 35]));
    expect(window.location.search).toContain('y=123');
    await user.click(screen.getByRole('button', { name: 'Free exploration' }));
    expect(window.location.search).not.toContain('chapter=');
  });
});
