// Sightspot 的标志：一个圆环（视野）与落在环上的点（机位），点周围留一圈空隙。坐标系 100×100。
// 页面左上角的标志（SightMark.vue）和 PWA 图标、分享图（scripts/gen-icons.mts）都从这里生成。

export interface MarkOptions {
  /** 图形的颜色 */
  color: string;
  /** 小尺寸（favicon）用：环和点都加粗，缩小后不发虚 */
  bold?: boolean;
  /** 遮罩 id，同一页面里要唯一 */
  id?: string;
}

const R = 26; // 圆环半径
const ANGLE = 50; // 点在环上的位置：从正右方逆时针 50°，约一点钟方向

/** 只有图形、没有底板：空隙用遮罩做成透明，任何背景上都透出底色 */
export function markShapes({ color, bold = false, id = "sightspot-mark" }: MarkOptions): string {
  const stroke = bold ? 7.5 : 6;
  const dot = bold ? 9.5 : 8;
  const gap = dot + 4;
  const a = (ANGLE * Math.PI) / 180;
  const x = +(50 + R * Math.cos(a)).toFixed(2);
  const y = +(50 - R * Math.sin(a)).toFixed(2);
  return (
    `<mask id="${id}"><rect width="100" height="100" fill="#fff"/><circle cx="${x}" cy="${y}" r="${gap}" fill="#000"/></mask>` +
    `<circle cx="50" cy="50" r="${R}" fill="none" stroke="${color}" stroke-width="${stroke}" mask="url(#${id})"/>` +
    `<circle cx="${x}" cy="${y}" r="${dot}" fill="${color}"/>`
  );
}

export interface IconOptions extends MarkOptions {
  /** true：铺满白底（Android 可遮罩图标、iOS 主屏，系统自己裁圆角）；false：带淡边的圆角白底 */
  bleed?: boolean;
  size?: number;
}

/** 白底应用图标 */
export function iconSvg({ bleed = false, size = 512, ...mark }: IconOptions): string {
  const tile = bleed
    ? `<rect width="100" height="100" fill="#fff"/>`
    : `<rect x=".5" y=".5" width="99" height="99" rx="21.5" fill="#fff" stroke="#000" stroke-opacity=".08"/>`;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="${size}" height="${size}">${tile}${markShapes(mark)}</svg>`;
}
