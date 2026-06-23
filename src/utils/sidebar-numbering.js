/**
 * 解析类似 "1.5 显示屏使用" / "1. 快速开始" 的标签。
 */
export function parseNumberedLabel(label) {
  if (typeof label !== 'string') return null;
  const trimmed = label.trim();
  const match = trimmed.match(/^(\d+(?:\.\d+)*)(?:\s*[.。．、-]\s*|\s+)(.+)$/);
  if (!match) return null;
  return {
    prefix: match[1],
    rest: match[2].trim(),
  };
}

/**
 * 去掉标题中的数字前缀。
 */
export function stripNumberPrefix(label) {
  const parsed = parseNumberedLabel(label);
  return parsed ? parsed.rest : label;
}

/**
 * 根据当前可见侧边栏项重排章节编号，避免过滤后出现断号（如 1.4 -> 1.6）。
 * 仅修改 label 显示，不影响文档路径与 docId。
 */
export function renumberVisibleItems(items, parentPrefix = '') {
  if (!Array.isArray(items)) return items;
  let serial = 0;

  return items.map((item) => {
    const next = { ...item };
    const parsed = parseNumberedLabel(item.label);

    let ownPrefix = parentPrefix;
    if (parsed) {
      serial += 1;
      ownPrefix = parentPrefix ? `${parentPrefix}.${serial}` : `${serial}`;
      next.label = `${ownPrefix} ${parsed.rest}`;
    }

    if (item.type === 'category' && Array.isArray(item.items)) {
      const childPrefix = parsed ? ownPrefix : parentPrefix;
      next.items = renumberVisibleItems(item.items, childPrefix);
    }

    return next;
  });
}

/**
 * 从（已重排编号的）侧边栏中获取当前文档显示编号。
 */
export function findDocDisplayNumber(items, targetDocId) {
  if (!Array.isArray(items) || !targetDocId) return null;
  for (const item of items) {
    if (item.type === 'link' && item.docId === targetDocId) {
      const parsed = parseNumberedLabel(item.label);
      return parsed?.prefix ?? null;
    }
    if (item.type === 'category' && Array.isArray(item.items)) {
      const found = findDocDisplayNumber(item.items, targetDocId);
      if (found) return found;
    }
  }
  return null;
}
