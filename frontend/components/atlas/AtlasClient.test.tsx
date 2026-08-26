import { render, screen, waitFor } from '@testing-library/react'; import userEvent from '@testing-library/user-event'; import { beforeEach, describe, expect, it, vi } from 'vitest';
vi.mock('../../lib/atlas', async () => { const actual = await vi.importActual<typeof import('../../lib/atlas')>('../../lib/atlas'); return { ...actual, DEMO_MODE: true, HAS_REMOTE_API: false }; });
vi.mock('../map/AtlasMap',()=>({AtlasMap:()=> <div aria-label="map loaded"/>})); import { AtlasClient } from './AtlasClient';
describe('AtlasClient',()=>{beforeEach(()=>history.replaceState(null,'','/atlas'));
it('hydrates year and entity selection from the URL',async()=>{history.replaceState(null,'','/atlas?y=-44&sel=roman-empire'); render(<AtlasClient/>); expect((await screen.findAllByText('44 BCE')).length).toBeGreaterThan(0); await waitFor(()=>expect(screen.getAllByText(/Roman Empire/).length).toBeGreaterThan(0));});
it('filters features and can reset filters',async()=>{render(<AtlasClient/>); const user=userEvent.setup(); const filter=screen.getByRole('button',{name:/reviewed/i}); await user.click(filter); expect(screen.getByText('Filtered from map')).toBeInTheDocument();});
it('loads the lazy map',async()=>{render(<AtlasClient/>); await waitFor(()=>expect(screen.getByLabelText('map loaded')).toBeInTheDocument());});});
