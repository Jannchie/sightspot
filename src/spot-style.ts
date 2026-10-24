// 机位地图的样式：mapette 的底图 + 机位热力图、点、选中高亮与取景扇形
import { coneLayers, createBasemap, focusPointLayer, heatmapLayer, pointLayer, type StyleContext } from "@mapette/core";

const RAIL = "pmtiles://https://cdn.jannchie.com/junrei/rail/rail-v4.pmtiles";

/** 换主题时原样保留的数据源（12 万个点，不要重新解析） */
export const KEEP_SOURCES = ["spots", "cone"];

export function spotStyle({ palette: c }: StyleContext) {
  return createBasemap({
    palette: c,
    locale: "zh-Hans",
    rail: RAIL,
    // focus：选中机位的 pageid（0 表示没有选中）
    state: { focus: { default: 0 } },
    sources: {
      // 全部机位：maplibre 在 worker 里抓取、解析，主线程不碰这 12 万个点
      spots: { type: "geojson", data: "/data/spots.geojson" },
      // 选中机位的取景扇形（有朝向时）
      cone: { type: "geojson", data: { type: "FeatureCollection", features: [] } },
    },
    belowLabels: [heatmapLayer({ source: "spots", palette: c })],
    overlays: [
      ...coneLayers({ source: "cone", palette: c }),
      pointLayer({ source: "spots", palette: c }),
      focusPointLayer({ source: "spots", palette: c, filter: ["==", ["get", "i"], ["global-state", "focus"]] }),
    ],
  });
}
