// Sightspot 的标志：一个圆环（视野）与落在环上的点（机位），圆环在点的两侧圆头断开。坐标系 100×100。
// 页面左上角的标志（SightMark.vue）和 PWA 图标、分享图（scripts/gen-icons.mts）都从这里生成。

export interface MarkOptions {
  /** 图形的颜色 */
  color: string;
  /** 小尺寸（favicon）用：环和点都加粗，缩小后不发虚 */
  bold?: boolean;
}

const R = 26; // 圆环半径
const ANGLE = 50; // 点在环上的位置：从正右方逆时针 50°，约一点钟方向

const SPACE = 4; // 圆环断口的圆头与点之间的空隙

/** 环上某个角度的点（0° 朝右、逆时针为正；SVG 的 y 向下） */
const onRing = (deg: number) => {
  const a = (deg * Math.PI) / 180;
  return [+(50 + R * Math.cos(a)).toFixed(2), +(50 - R * Math.sin(a)).toFixed(2)] as const;
};

/**
 * 只有图形、没有底板。圆环是一段圆弧，在点的两侧断开、两端圆头收口（不是把整圈描边裁掉一块），
 * 断口的角度按点的大小算：圆头到点的距离正好是 SPACE
 */
export function markShapes({ color, bold = false }: MarkOptions): string {
  const stroke = bold ? 7.5 : 6;
  const dot = bold ? 9.5 : 8;
  // 同一个圆上相隔 θ 的两点相距 2R·sin(θ/2)：让它等于 点半径 + 空隙 + 圆头半径
  const half = (2 * Math.asin((dot + SPACE + stroke / 2) / (2 * R)) * 180) / Math.PI;
  const [sx, sy] = onRing(ANGLE + half);
  const [ex, ey] = onRing(ANGLE - half);
  const [x, y] = onRing(ANGLE);
  return (
    // 从点的逆时针一侧出发，绕大半圈（large-arc=1，逆时针 sweep=0）回到顺时针一侧
    `<path d="M${sx} ${sy}A${R} ${R} 0 1 0 ${ex} ${ey}" fill="none" stroke="${color}" stroke-width="${stroke}" stroke-linecap="round"/>` +
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
