/** 线性 SVG 图标(1.5px 描边,继承 currentColor),替代字符图标 */

function Svg({ children, size = 16, className = "" }: {
  children: React.ReactNode; size?: number; className?: string;
}) {
  return (
    <svg
      width={size} height={size} viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"
      className={className} aria-hidden
    >
      {children}
    </svg>
  );
}

/** Claude 式放射星标 —— 工作台标识 */
export function Logo({ size = 26, className = "" }: { size?: number; className?: string }) {
  const rays: React.ReactNode[] = [];
  for (let i = 0; i < 12; i++) {
    const a = (i * Math.PI) / 6;
    const r0 = i % 3 === 0 ? 3.2 : 5.2;
    const x1 = 12 + Math.cos(a) * r0, y1 = 12 + Math.sin(a) * r0;
    const x2 = 12 + Math.cos(a) * 10.2, y2 = 12 + Math.sin(a) * 10.2;
    rays.push(<line key={i} x1={x1} y1={y1} x2={x2} y2={y2} />);
  }
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2.1" strokeLinecap="round" className={className} aria-hidden>
      {rays}
    </svg>
  );
}

export function IconOverview({ size, className }: { size?: number; className?: string }) {
  return (
    <Svg size={size} className={className}>
      <rect x="3.5" y="3.5" width="7" height="7" rx="1.6" />
      <rect x="13.5" y="3.5" width="7" height="7" rx="1.6" />
      <rect x="3.5" y="13.5" width="7" height="7" rx="1.6" />
      <rect x="13.5" y="13.5" width="7" height="7" rx="1.6" />
    </Svg>
  );
}

export function IconRuns({ size, className }: { size?: number; className?: string }) {
  return (
    <Svg size={size} className={className}>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M10 8.8l5 3.2-5 3.2z" fill="currentColor" stroke="none" />
    </Svg>
  );
}

export function IconResources({ size, className }: { size?: number; className?: string }) {
  return (
    <Svg size={size} className={className}>
      <rect x="3.5" y="5" width="17" height="14" rx="2" />
      <circle cx="8.5" cy="10" r="1.5" fill="currentColor" stroke="none" />
      <path d="M3.5 16l4.8-4.2 3.7 3.2 3.4-2.8 5.1 3.8" />
    </Svg>
  );
}

export function IconSkills({ size, className }: { size?: number; className?: string }) {
  return (
    <Svg size={size} className={className}>
      <path d="M12 3.5c.7 4.6 3.9 7.8 8.5 8.5-4.6.7-7.8 3.9-8.5 8.5-.7-4.6-3.9-7.8-8.5-8.5 4.6-.7 7.8-3.9 8.5-8.5z" />
    </Svg>
  );
}

export function IconPlay({ size = 13, className }: { size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden>
      <path d="M7.5 5.2c0-.9 1-1.5 1.8-1L19 10.9c.8.5.8 1.6 0 2.1L9.3 19.7c-.8.5-1.8-.1-1.8-1z" />
    </svg>
  );
}

export function IconDoc({ size = 13, className }: { size?: number; className?: string }) {
  return (
    <Svg size={size} className={className}>
      <path d="M6 3.5h8l4 4v13H6z" />
      <path d="M14 3.5v4h4" />
      <path d="M9 12h6M9 15.5h6" />
    </Svg>
  );
}

export function IconGear({ size = 12, className }: { size?: number; className?: string }) {
  return (
    <Svg size={size} className={className}>
      <circle cx="12" cy="12" r="3.2" />
      <path d="M12 2.8v3M12 18.2v3M2.8 12h3M18.2 12h3M5.5 5.5l2.1 2.1M16.4 16.4l2.1 2.1M18.5 5.5l-2.1 2.1M7.6 16.4l-2.1 2.1" />
    </Svg>
  );
}

export function IconDownload({ size = 14, className }: { size?: number; className?: string }) {
  return (
    <Svg size={size} className={className}>
      <path d="M12 4v11M7.5 11l4.5 4.5L16.5 11" />
      <path d="M4.5 19.5h15" />
    </Svg>
  );
}
