import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
vi.mock('../../../lib/atlas', async () => ({ ...await vi.importActual('../../../lib/atlas'), DEMO_MODE: false, HAS_REMOTE_API: true, API_BASE_URL: 'https://atlas.test' }));
import { useAtlasData, emptyWorld } from './useAtlasData';
const response = (data: unknown) => ({ ok: true, json: async () => data });
describe('historical data loading', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn(async (url: string) => response(url.includes('/world/') ? emptyWorld(Number(url.split('/').pop())) : [])));
  });
  afterEach(() => vi.unstubAllGlobals());
  it('loads the deep-linked year and retains the last snapshot with its actual year while another year loads, then reuses the cache', async () => {
    const { result, rerender } = renderHook(({ year }) => useAtlasData(year, true), { initialProps: { year: 700 } });
    await waitFor(() => expect(result.current.status).toBe('live'));
    expect(fetch).toHaveBeenCalledWith('https://atlas.test/api/v1/world/700', expect.anything());
    rerender({ year: 117 });
    expect(result.current.status).toBe('loading');
    expect(result.current.world).toEqual(emptyWorld(700));
    await waitFor(() => expect(result.current.status).toBe('live'));
    const count = vi.mocked(fetch).mock.calls.length;
    rerender({ year: 700 });
    await waitFor(() => expect(result.current.status).toBe('live'));
    expect(vi.mocked(fetch).mock.calls.length).toBe(count);
  });
  it('cancels obsolete requests and ignores late responses even if the transport ignores abort', async () => {
    let finish: (value: unknown) => void = () => {};
    vi.stubGlobal('fetch', vi.fn((url: string) => url.endsWith('/world/117') ? new Promise((resolve) => { finish = resolve; }) : Promise.resolve(response(url.includes('/world/') ? emptyWorld(700) : []))));
    const { result, rerender } = renderHook(({ year }) => useAtlasData(year, true), { initialProps: { year: 117 } });
    await waitFor(() => expect(fetch).toHaveBeenCalledWith('https://atlas.test/api/v1/world/117', expect.anything()));
    const signal = vi.mocked(fetch).mock.calls.find(([url]) => String(url).endsWith('/world/117'))![1]!.signal!;
    rerender({ year: 700 });
    expect(signal.aborted).toBe(true);
    await waitFor(() => expect(result.current.status).toBe('live'));
    await act(async () => { finish(response(emptyWorld(117))); });
    expect(result.current.world.year).toBe(700);
  });
  it('clears the retained snapshot when the new date fails, and clears genuinely empty dates', async () => {
    const previous = { ...emptyWorld(117), layers: [{ id: 'published-boundary' }] };
    vi.stubGlobal('fetch', vi.fn(async (url: string) => url.endsWith('/world/117') ? response(previous) : url.endsWith('/world/700') ? { ok: false } : response(url.includes('/world/') ? emptyWorld(1500) : [])));
    const { result, rerender } = renderHook(({ year }) => useAtlasData(year, true), { initialProps: { year: 117 } });
    await waitFor(() => expect(result.current.status).toBe('live'));
    rerender({ year: 700 });
    expect(result.current.world.year).toBe(117);
    await waitFor(() => expect(result.current.status).toBe('unavailable'));
    expect(result.current.world).toEqual(emptyWorld(700));
    rerender({ year: 1500 });
    await waitFor(() => expect(result.current.status).toBe('live'));
    expect(result.current.world).toEqual(emptyWorld(1500));
  });
  it('shows failure without demo fallback and supports retry', async () => {
    vi.stubGlobal('fetch', vi.fn(async (url: string) => url.includes('/world/') ? { ok: false } : response([])));
    const { result } = renderHook(() => useAtlasData(117, true));
    await waitFor(() => expect(result.current.status).toBe('unavailable'));
    expect(result.current.world.civilizations).toEqual([]);
    vi.stubGlobal('fetch', vi.fn(async (url: string) => response(url.includes('/world/') ? emptyWorld(117) : [])));
    act(() => result.current.reload());
    await waitFor(() => expect(result.current.status).toBe('live'));
  });
});
