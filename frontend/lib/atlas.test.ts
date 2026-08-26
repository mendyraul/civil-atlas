import { describe, expect, it } from 'vitest';
import { filterWorldByYear, formatYear, getFeatureById, isActiveAtYear } from './atlas';
import { world117 } from '../data/world117';
describe('atlas temporal queries', () => {
  it('includes closed interval boundaries and BCE years', () => { expect(isActiveAtYear({startYear:-500,endYear:-100}, -500)).toBe(true); expect(formatYear(-44)).toBe('44 BCE'); });
  it('filters every temporal collection', () => { const result=filterWorldByYear(world117, 117); expect(result.year).toBe(117); expect([...result.civilizations,...result.nodes,...result.routes].every(x=>x.startYear<=117&&x.endYear>=117)).toBe(true); });
  it('resolves deep-linked entities', () => expect(getFeatureById(world117, 'roman-empire')?.label).toMatch(/Roman/));
});
