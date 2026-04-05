import { useState, useRef } from 'react';

interface ResizerProps {
  onDrag: (delta: number) => void;
  direction?: 'horizontal' | 'vertical';
}

export function Resizer({ onDrag, direction = 'horizontal' }: ResizerProps) {
  const isDragging = useRef(false);
  const startPos = useRef(0);
  const [localDragging, setLocalDragging] = useState(false);

  const onMouseDown = (e: React.MouseEvent) => {
    isDragging.current = true;
    setLocalDragging(true);
    startPos.current = direction === 'horizontal' ? e.clientX : e.clientY;

    document.body.style.cursor = direction === 'horizontal' ? 'col-resize' : 'row-resize';
    document.body.style.userSelect = 'none';
    document.body.classList.add('resizing-global');

    const onMove = (ev: MouseEvent) => {
      if (!isDragging.current) return;
      const currentPos = direction === 'horizontal' ? ev.clientX : ev.clientY;
      const delta = currentPos - startPos.current;
      onDrag(delta);
      startPos.current = currentPos;
    };

    const onUp = () => {
      isDragging.current = false;
      setLocalDragging(false);
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      document.body.classList.remove('resizing-global');
    };

    document.addEventListener('mousemove', onMove, { passive: true });
    document.addEventListener('mouseup', onUp);
  };

  return (
    <div
      onMouseDown={onMouseDown}
      style={{
        width: direction === 'horizontal' ? '12px' : '100%',
        height: direction === 'horizontal' ? '100%' : '12px',
        cursor: direction === 'horizontal' ? 'col-resize' : 'row-resize',
        background: 'transparent',
        flexShrink: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 200,
        position: 'relative',
        margin: direction === 'horizontal' ? '0 -6px' : '-6px 0',
      }}
    >
      <div style={{
        width: direction === 'horizontal' ? (localDragging ? '4px' : '2px') : (localDragging ? '40px' : '40px'),
        height: direction === 'horizontal' ? (localDragging ? '40px' : '40px') : (localDragging ? '4px' : '2px'),
        borderRadius: '4px',
        background: localDragging ? 'var(--accent)' : 'var(--border)',
        transition: 'background 0.15s, width 0.15s, height 0.15s',
      }} className="resizer-handle" />
      <style>{`
        .resizer-handle:not(.active):hover {
          background: var(--accent) !important;
          width: ${direction === 'horizontal' ? '4px' : '40px'} !important;
          height: ${direction === 'horizontal' ? '40px' : '4px'} !important;
        }
        body.resizing-global * {
          pointer-events: none !important;
        }
        body.resizing-global [onmousedown] {
          pointer-events: auto !important;
        }
      `}</style>
    </div>
  );
}
