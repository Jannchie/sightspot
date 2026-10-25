// 精选集筛选：地图点的属性 c 是所属精选集的位掩码（scripts/export_demo.py 的 COLLECTIONS，顺序相同）。
// 筛选放在数据源上（聚合之前），气泡里的数字跟着变；全都不选等于不筛选。
import type { ExpressionSpecification, GeoJSONSource, Map as MaplibreMap } from "maplibre-gl";

export const COLLECTIONS = { fp: 1, qi: 2, vi: 4, wlm: 8, wle: 16 } as const;
export type Collection = keyof typeof COLLECTIONS;
export const COLLECTION_KEYS = Object.keys(COLLECTIONS) as Collection[];

/** 选中的任一精选集包含这个点；表达式里没有位运算，用 floor(c / bit) % 2 取位 */
function filterOf(selected: Collection[]): ExpressionSpecification | undefined {
  if (!selected.length) return undefined;
  const has = (k: Collection): ExpressionSpecification => ["==", ["%", ["floor", ["/", ["get", "c"], COLLECTIONS[k]]], 2], 1];
  return selected.length === 1 ? has(selected[0]) : ["any", ...selected.map(has)];
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

/** 链接里的 ?c=fp,wlm */
export function parseCollections(v: string | null): Collection[] {
  return (v ?? "").split(",").filter((k): k is Collection => k in COLLECTIONS);
}
