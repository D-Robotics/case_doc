/**
 * 将 Markdown / HTML 表格包裹在可横向滚动的容器内，
 * 使表格默认占满内容区宽度，溢出时出现横向滚动条。
 */
import {visit} from 'unist-util-visit';

const WRAPPER_CLASS = 'markdown-table-scroll';

function isAlreadyWrapped(parent) {
  if (!parent || parent.type !== 'element' || parent.tagName !== 'div') {
    return false;
  }
  const className = parent.properties?.className;
  const classes = Array.isArray(className)
    ? className
    : typeof className === 'string'
      ? className.split(/\s+/)
      : [];
  return (
    classes.includes(WRAPPER_CLASS) || classes.includes('table-responsive')
  );
}

export default function rehypeWrapTables() {
  return (tree) => {
    visit(tree, 'element', (node, index, parent) => {
      if (node.tagName !== 'table' || parent?.type !== 'element') {
        return;
      }
      if (isAlreadyWrapped(parent)) {
        return;
      }

      parent.children[index] = {
        type: 'element',
        tagName: 'div',
        properties: {className: [WRAPPER_CLASS]},
        children: [node],
      };
    });
  };
}
