/**
 * 将 Markdown 表格包裹在可横向滚动的 div 容器内。
 */
import {visit} from 'unist-util-visit';

const WRAPPER_CLASS = 'markdown-table-scroll';

function isWrapped(parent) {
  if (!parent || parent.type !== 'container') {
    return false;
  }
  const className = parent.data?.hProperties?.className;
  const classes = Array.isArray(className)
    ? className
    : typeof className === 'string'
      ? className.split(/\s+/)
      : [];
  return (
    classes.includes(WRAPPER_CLASS) || classes.includes('table-responsive')
  );
}

export default function remarkWrapTables() {
  return (tree) => {
    visit(tree, 'table', (node, index, parent) => {
      if (!parent || isWrapped(parent)) {
        return;
      }

      parent.children[index] = {
        type: 'container',
        data: {
          hName: 'div',
          hProperties: {className: [WRAPPER_CLASS]},
        },
        children: [node],
      };
    });
  };
}
