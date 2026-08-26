import { render, screen, waitFor } from '@testing-library/react'; import userEvent from '@testing-library/user-event'; import { beforeEach, describe, expect, it, vi } from 'vitest';
vi.mock('../map/AtlasMap',()=>({AtlasMap:()=> <div aria-label="map loaded"/>})); import { AtlasClient } from './AtlasClient';
describe('AtlasClient',()=>{beforeEach(()=>history.replaceState(null,'','/atlas'));
it('hydrates year and entity selection from the URL',async()=>{history.replaceState(null,'','/atlas?y=-44&sel=roman-empire'); render(<AtlasClient/>); expect(await screen.findByText('44 BCE')).toBeInTheDocument(); expect(screen.getAllByText(/Roman Empire/).length).toBeGreaterThan(0);});
it('filters features and can reset filters',async()=>{render(<AtlasClient/>); const user=userEvent.setup(); const filter=screen.getByRole('button',{name:/reviewed/i}); await user.click(filter); expect(screen.getByText(/filter/i)).toBeInTheDocument();});
it('loads the lazy map',async()=>{render(<AtlasClient/>); await waitFor(()=>expect(screen.getByLabelText('map loaded')).toBeInTheDocument());});});
