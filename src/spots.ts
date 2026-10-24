// 机位详情：按空间分片存放在 /data/d/{shard}.json（scripts/export_demo.py），同一分片只请求一次。

export interface Spot {
  id: number;
  /** 详情所在的分片 */
  shard: string;
  title: string;
  /** Commons 文件页 */
  page: string;
  lng: number;
  lat: number;
  w: number;
  h: number;
  /** 500px 宽，列表与地图上的照片标记 */
  small: string;
  /** 1280px 宽，详情 */
  large: string;
  mirrored: boolean;
  artist: string | null;
  license: string | null;
  licenseUrl: string | null;
  taken: string | null;
  featured: boolean;
  camera: string | null;
  lens: string | null;
  focal: number | null;
  focal35: number | null;
  fnumber: number | null;
  exposure: string | null;
  iso: number | null;
  /** 拍摄朝向，正北为 0°，顺时针 */
  heading: number | null;
}

const shards = new Map<string, Promise<Record<string, Omit<Spot, "id" | "shard">>>>();

function loadShard(shard: string) {
  let p = shards.get(shard);
  if (!p) {
    p = fetch(`/data/d/${shard}.json`).then((r) => {
      if (!r.ok) throw new Error(`shard ${shard}: ${r.status}`);
      return r.json();
    });
    p.catch(() => shards.delete(shard)); // 失败的下次再试
    shards.set(shard, p);
  }
  return p;
}

export async function fetchSpot(id: number, shard: string): Promise<Spot | null> {
  const d = (await loadShard(shard))[id];
  return d ? { id, shard, ...d } : null;
}

/** 一批机位（视野里的），按分片合并请求，保持传入顺序 */
export async function fetchSpots(refs: { id: number; shard: string }[]): Promise<Spot[]> {
  const byShard = await Promise.all([...new Set(refs.map((r) => r.shard))].map(async (s) => [s, await loadShard(s)] as const));
  const lookup = new Map(byShard);
  return refs.flatMap(({ id, shard }) => {
    const d = lookup.get(shard)?.[id];
    return d ? [{ id, shard, ...d }] : [];
  });
}

/** 35mm 等效焦距 → 水平视角（度）；没有等效焦距时不画扇形的宽度，用 60° */
export function fieldOfView(spot: Spot): number {
  const f = spot.focal35;
  if (!f) return 60;
  return (2 * Math.atan(36 / (2 * f)) * 180) / Math.PI;
}

const COMPASS = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"];
export const compass = (deg: number) => COMPASS[Math.round(deg / 45) % 8];
