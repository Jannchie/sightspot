// 机位地图的样式：mapette 的底图 + 机位聚合气泡、单个机位、选中高亮与取景扇形
import { clusterLayers, clusterSource, coneLayers, createBasemap, focusPointLayer, pointLayer, UNCLUSTERED, type StyleContext } from "@mapette/core";

const RAIL = "pmtiles://https://cdn.jannchie.com/junrei/rail/rail-v4.pmtiles";

/** 换主题时原样保留的数据源（12 万个点，不要重新解析） */
export const KEEP_SOURCES = ["spots", "cone", "focus"];

export function spotStyle({ palette: c }: StyleContext) {
  return createBasemap({
    palette: c,
    locale: "zh-Hans",
    rail: RAIL,
    sources: {
      // 全部机位：maplibre 在 worker 里抓取、解析并按缩放聚合，主线程不碰这 12 万个点
      spots: clusterSource("/data/spots.geojson", { radius: 48, maxZoom: 11 }),
      // 选中机位的取景扇形（有朝向时）与选中的点：单独放，被聚合进气泡时也看得到
      cone: { type: "geojson", data: { type: "FeatureCollection", features: [] } },
      focus: { type: "geojson", data: { type: "FeatureCollection", features: [] } },
    },
    overlays: [
      ...coneLayers({ source: "cone", palette: c }),
      pointLayer({ source: "spots", palette: c, fade: false, filter: UNCLUSTERED }),
      ...clusterLayers({ source: "spots", palette: c }),
      focusPointLayer({ source: "focus", palette: c }),
    ],
  });
}
