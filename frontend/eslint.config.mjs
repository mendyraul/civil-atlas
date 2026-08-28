import { globalIgnores } from 'eslint/config';
import nextVitals from 'eslint-config-next/core-web-vitals';

const config = [
  ...nextVitals,
  globalIgnores(['.next/**', 'coverage/**', 'playwright-report/**']),
  {
    // The map keeps synchronous refs for event handlers registered once, and
    // the atlas effects synchronize external URL/browser state by design.
    rules: {
      'react-hooks/refs': 'off',
      'react-hooks/set-state-in-effect': 'off',
    },
  },
];

export default config;
