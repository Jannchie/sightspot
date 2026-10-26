// 精选集筛选：地图点的属性 c 是所属精选集的位掩码（scripts/export_demo.py 的 COLLECTIONS，顺序相同）。
// Commons 以外的来源（Geograph、iNaturalist）各占一位，和精选集一起筛选；wp 是被多个语言的维基百科条目使用的照片。
// 筛选放在数据源上（聚合之前），气泡里的数字跟着变；全都不选时显示默认隐藏（HIDDEN_BY_DEFAULT）以外的全部。
import type { ExpressionSpecification, GeoJSONSource, Map as MaplibreMap } from "maplibre-gl";

export const COLLECTIONS = { fp: 1, qi: 2, vi: 4, wlm: 8, wle: 16, wp: 128, geograph: 32, inat: 64 } as const;
export type Collection = keyof typeof COLLECTIONS;
export const COLLECTION_KEYS = Object.keys(COLLECTIONS) as Collection[];

/** 什么都不选时也不显示，要手动选上：生物观察里有毒虫之类可能让人不适的照片 */
export const HIDDEN_BY_DEFAULT: Collection[] = ["inat"];
const hiddenMask = HIDDEN_BY_DEFAULT.reduce((m, k) => m | COLLECTIONS[k], 0);

/** 选中的任一精选集包含这个点（不选时为默认隐藏以外的全部）；表达式里没有位运算，用 floor(c / bit) % 2 取位 */
export function filterOf(selected: Collection[]): ExpressionSpecification | undefined {
  const bit = (k: Collection, v: 0 | 1): ExpressionSpecification => ["==", ["%", ["floor", ["/", ["get", "c"], COLLECTIONS[k]]], 2], v];
  if (!selected.length) {
    const hide = HIDDEN_BY_DEFAULT.map((k) => bit(k, 0));
    return hide.length === 0 ? undefined : hide.length === 1 ? hide[0] : ["all", ...hide];
  }
  return selected.length === 1 ? bit(selected[0], 1) : ["any", ...selected.map((k) => bit(k, 1))];
}

/**
 * 给 GeoJSON 数据源换筛选条件。maplibre 只在样式里声明 filter，没有运行时的 setter：
 * 改 workerOptions 后重新加载同一个地址（浏览器缓存命中，只在 worker 里重新解析、筛选、聚合）
 */
export function setSourceFilter(map: MaplibreMap, source: string, url: string, selected: Collection[]) {
  const s = map.getSource(source) as (GeoJSONSource & { workerOptions: { filter?: ExpressionSpecification } }) | undefined;
  if (!s) return;
  const next = filterOf(selected);
  if (JSON.stringify(s.workerOptions.filter) === JSON.stringify(next)) return;
  s.workerOptions.filter = next;
  // 视野列表（useViewportFeatures）只在 moveend 时重新统计：新数据画出来之后补一次
  void s.setData(url, true).then(() => map.once("idle", () => map.fire("moveend")));
}

/** 位掩码 c 是否属于选中的任一精选集（不选为默认隐藏以外的全部） */
export const inCollections = (c: number, selected: Collection[]) =>
  selected.length ? selected.some((k) => (c & COLLECTIONS[k]) !== 0) : (c & hiddenMask) === 0;

/** 链接里的 ?c=fp,wlm */
export function parseCollections(v: string | null): Collection[] {
  return (v ?? "").split(",").filter((k): k is Collection => k in COLLECTIONS);
}
