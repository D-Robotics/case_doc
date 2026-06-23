import raw from './doc-scope-matrix.json';

export const VERSION_PRODUCT_MATRIX = raw.VERSION_PRODUCT_MATRIX;
export const PRODUCT_VERSION_MATRIX = raw.PRODUCT_VERSION_MATRIX;
const configuredProducts = Array.isArray(raw.PRODUCTS) ? raw.PRODUCTS : [];
const matrixProducts = Object.keys(PRODUCT_VERSION_MATRIX || {});
const versionProducts = Object.values(VERSION_PRODUCT_MATRIX || {}).flat();

export const ALL_PRODUCTS = Array.from(
  new Set([...configuredProducts, ...matrixProducts, ...versionProducts]),
);
