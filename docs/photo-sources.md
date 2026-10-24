# 摄影机位地图：候选图片来源调研

调研日期：2026-10-24。现有数据为 Commons QI/FP/VI 中带相机坐标的约 11.8 万张。用户已评估过的来源（Geograph UK、YFCC100M、Mapillary/KartaView、Flickr API、Unsplash、500px、Locationscout/PhotoPills/ShotHotspot）这里不再重复。

标注说明：**[实测]** 表示本次调研中实际调用 API 或统计得到；**[未验证]** 表示来自记忆或二手资料，未在一手来源核实。

## 总览（按推荐度排序）

| # | 来源 | 质量信号 | 坐标 | 可用规模（估） | 许可 / 商用 | 结论 |
|---|---|---|---|---|---|---|
| 1 | Wiki Loves Monuments 国家赛提名与获奖作品（Commons） | 各国评审团评选，每国最多 10 张进入国际决赛 | 约 52% 有相机坐标，其余可通过古迹 ID 拿到被摄体坐标 | 2.66 万张，其中约 1.4 万张有相机坐标 [实测] | CC BY / BY-SA 等自由许可，可商用 | **立即用** |
| 2 | Wiki Loves Earth 获奖作品（Commons） | 各国评审团评选（自然保护区题材） | 约 48% 有相机坐标，其余可通过保护区 ID 拿到被摄体坐标 | 1,776 张，约 850 张有相机坐标 [实测] | 同上 | **立即用** |
| 3 | Commons 结构化数据 P1259（相机坐标）补全 | 不是新来源，用来提高 1、2 和现有集合的覆盖率 | 相机位置（含朝向 P7787） | 全站约 2,730 万条 P1259（二手数据） | 同上 | **立即用（作为补全手段）** |
| 4 | OSM `tourism=viewpoint` + Commons 地理搜索 | 观景点由社区标注，照片沿用 Commons QI/FP 质量门槛 | 观景点即机位，3.8 万个带 `direction` | 26.5 万个观景点，带 image/commons 标签的约 3.5k [实测] | OSM ODbL，照片走 Commons 许可 | **立即用（作为机位先验 / 排序信号）** |
| 5 | 韩国观光公社 观光摄影比赛获奖作 API（Photo Korea） | 官方摄影比赛获奖作品 | 拍摄地为文字和法定洞代码（区域级），需要地理编码 | 未知（估计数千张）[未验证] | 平台标注「이용허락범위 제한 없음」；照片有使用限制条款 | **可能** |
| 6 | 韩国 TourAPI 景点图片 / 观光写真画廊 | 官方编辑拍摄 | 景点 mapx/mapy 是被摄体坐标；画廊只有拍摄地文字 | 约 4 万条景点数据 | KOGL 1 型（可商用）或 3 型（不可改作），逐图标注 | **可能** |
| 7 | Library of Congress：Carol M. Highsmith 档案 | 职业摄影师系统拍摄美国建筑与风景 | 只有城市/州文字，无经纬度 | 超过 7 万张 | 公有领域 | **可能**（需要地理编码，与 Commons 去重） |
| 8 | Wikidata P18 + P1259 | 条目主图通常质量较高 | 相机坐标 | 3,821 条 [实测] | Commons 许可 | **可能**（量太小，可顺手合并） |
| 9 | Europeana | 馆藏数字化，非美学策展 | 1,700 万+对象有经纬度（多为被摄体或地点） | 大 | 逐条 rights，有 CC0/BY/BY-SA 子集 | **可能（低优先级）** |
| 10 | Geograph Deutschland / 其他 Geograph 分站 | 社区投稿，质量参差 | 相机和被摄体位置（与 UK 站同一套系统） | 未核实 | CC BY-SA 2.0 | **可能（低）** |
| 11 | Japan Search / 日本自治体照片库 | 各馆、各自治体自行发布 | 部分条目有经纬度 | 零散 | 逐库标注，部分为 CC BY | **暂不** |
| 12 | NPS（美国国家公园）API | 官方图片 | 只有公园或地点坐标 | 中 | 多为公有领域，但部分图片有署名或版权 [未验证] | **暂不** |
| 13 | iNaturalist Open Data | Research Grade 只代表物种鉴定质量 | 观测坐标约等于相机位置 | 数亿张 | CC0/BY/BY-NC 混合 | **不用**（题材不符） |
| 14 | Openverse / Pexels / Pixabay | 图库，无评审 | **无地理字段** [实测] | — | — | **不用** |
| 15 | 摄影大赛（APOTY、NLPA、LPOTY、TPOTY、SWPA、EPSON Pano、Drone Awards 等） | 最强的评审信号 | 只有地名文字 | 每届数十到数百张 | 作者保留版权，无公开许可 | **不用**（最多当选点线索） |
| 16 | NatGeo Your Shot、Atlas Obscura、Google Arts & Culture、图虫/视觉中国 | — | — | — | 无开放数据或许可 | **不用** |

---

## 1. Wiki Loves Monuments（WLM）国家赛提名与获奖作品

- **是什么**：全球最大的摄影比赛（吉尼斯纪录），主题是登记在册的文物古迹，每年 9 月在 Commons 举办。2025 年有 56 个国家赛，共约 22.8 万张投稿。各国评审团评出国家获奖作，每国最多 10 张进入国际决赛。参见 https://www.wikilovesmonuments.org/wlm2025-winners/
- **质量信号**：国家级和国际级评审团评选。题材正好是建筑和城市景观。
- **如何取数**：
  - 分类树根节点为 `Category:Nominated and winning pictures of Wiki Loves Monuments`，下面按年、按国家分出 `Category:Winners of Wiki Loves Monuments {年} in {国}` 等子分类。
  - 用 PetScan（depth=7，ns=6）可以列出 **26,632 个文件** [实测]。注意其中包含「提名」作品，不全是获奖作；如需更严格，只取 `Winners of …` 子分类。
  - 坐标覆盖：随机抽样 400 张，通过 `prop=coordinates&coprimary=all` 查询，**208 张（52%）有相机坐标**（primary 坐标，来自 `{{Location}}`），7 张有 object 坐标 [实测]。由此推算约 **1.38 万张带相机坐标**。
  - 没有相机坐标的作品：先查 EXIF GPS（`prop=imageinfo&iiprop=metadata`）和 SDC P1259；还没有的话，用文件上的古迹 ID 模板对应到 Wikidata 古迹条目的 P625，作为**被摄体坐标**（地图上应标明「仅被摄体位置」）。
- **访问**：MediaWiki API 与现有管线相同；PetScan 无需 key。
- **许可**：Commons 自由许可（CC BY-SA 4.0 为主），允许商用。需要显示作者和许可；缩略图可以镜像。注意部分国家没有全景自由（FoP），但 Commons 上的文件已经按规则处理过。
- **结论**：**立即用**。与现有 QI/FP 集合需要去重，部分获奖作已经是 QI/FP。

## 2. Wiki Loves Earth（WLE）获奖作品

- **是什么**：WLM 的姊妹赛，主题是自然保护区和自然遗产，正好对应风景与自然题材。
- **如何取数**：`Category:Winners of Wiki Loves Earth`，下有 2014–2026 共 13 个年度子分类，递归后共 **1,776 个文件** [实测]。
- **坐标**：抽样 400 张，190 张有坐标，其中 180 张（约 45–48%）是相机坐标 [实测]，推算约 850 张。缺坐标的可以用保护区 ID 对应 Wikidata，得到被摄体或区域坐标（保护区是面状区域，精度较差）。
- **许可**：同 WLM。
- **结论**：**立即用**。量小但题材契合度很高。另外可考虑 WLE 的「国家决赛入围」分类（未统计）。
- 顺带一提：Commons `Category:Pictures of the Year`（POTY）递归共 3,421 个文件 [实测]，但全部来自 FP 候选，**基本已包含在现有 FP 集合里**，不算新来源。

## 3. Commons 结构化数据 P1259 / P9149 补全坐标

- Commons SDC 的建模规范：P1259 = 相机坐标（可带 P7787 朝向、P2044 海拔），P7108 = 拍摄地点名，P9149 = 被摄体坐标。参见 https://commons.wikimedia.org/wiki/Commons:Structured_data/Modeling/Location
- 二手数据：全站约 2,730 万条 P1259、820 万条 P9149（OSM 社区帖子，日期不明，见 https://community.openstreetmap.org/t/is-there-a-tool-to-compare-osm-and-wikimedia-commons-coordinates/110686 ）[未验证]。
- 获取方式：
  - 批量：Commons Query Service（WCQS，需要 OAuth 登录），或 Commons 的 `mediainfo` JSON dump（`commons-*-mediainfo.json.bz2`，可离线解析）。
  - 少量：`wbgetentities` 查 `M{pageid}`。
- **用途**：为 1、2 两项以及现有集合中「有 EXIF 但无 `{{Location}}` 模板」的文件补相机坐标，同时拿到朝向，可以在地图上画视线方向。
- **结论**：**立即用**，作为管线改进而不是新来源。

## 4. OSM 观景点（`tourism=viewpoint`）+ Commons

- **taginfo 统计** [实测]：共 265,348 个；其中 37,982 个带 `direction`，3,250 个带 `wikidata`，2,342 个带 `image`，1,165 个带 `wikimedia_commons`。API：https://taginfo.openstreetmap.org/api/4/tag/stats?key=tourism&value=viewpoint
- **用法**：
  1. 观景点本身就是「机位」。用 Commons `list=geosearch`（半径 ≤10 km，每次最多 500 条）在观景点半径约 100 m 内查找 QI/FP/VI/WLM/WLE 照片，命中的照片可以提高排序权重，或标记为「经典机位」。
  2. 对于 `wikimedia_commons` 或 `image` 标签直接指向的图片，查它是否在质量分类中。
  3. 观景点的 `direction` 可以与 P7787 朝向交叉验证。
- **许可**：OSM 数据为 ODbL（展示需署名「© OpenStreetMap contributors」；派生数据库需同许可）。照片沿用 Commons 许可。
- **结论**：**立即用**，作为机位先验和排序信号，不单独提供照片。

## 5. 韩国观光公社「관광공모전(사진) 수상작 정보」API

- **是什么**：韩国观光公社「Photo Korea」（phoko.visitkorea.or.kr）旅游摄影比赛的获奖作品，字段包括标题、拍摄日期、**拍摄地（촬영지）**、关键词和图片信息，并附带法定洞代码表。2025-08 上线，2026-04 更新。
- **页面**：https://www.data.go.kr/data/15145706/openapi.do （元数据：https://www.data.go.kr/biz/dcat/metadata/15145706.do ）
- **坐标**：文档描述中只有拍摄地和法定洞代码，**未见经纬度字段**，需要自行地理编码到区或洞级别 [字段名未验证，详细规格见附件 `TourAPI_Guide_(관광공모전 수상작)v4.0.zip`]。
- **规模**：页面未给出 [未验证]。
- **访问**：REST，JSON/XML，免费。开发账号 1,000 次调用（自动批准）；生产账号需要审核，登记使用案例后可以提高限额。
- **许可**：平台标注「이용허락범위 제한 없음」（使用范围无限制）。但同系列 TourAPI 对照片另有限制：禁止用于诽谤被摄体或侵害人格权，禁止用作企业 CI/BI。是否需要逐图标注 KOGL 类型 [未验证]。
- **结论**：**可能**。质量信号强（获奖作），许可宽松，但坐标只到区域级。适合与 TourAPI 景点坐标匹配后使用。

## 6. 韩国 TourAPI（景点图片、观光写真画廊）

- **是什么**：韩国观光公社的国内旅游信息 Open API，约 4 万条数据，包含景点图片。官方说明是「只选取可自由使用的资料」。参见 https://www.data.go.kr/data/15101811/openapi.do
- **坐标**：景点列表的 `mapx`/`mapy` 是**景点坐标**（被摄体位置，非机位）[字段名凭记忆，未在本次调研中逐字核实]。另有「관광사진 갤러리」服务，字段有拍摄地文字、拍摄月份、拍摄者（如 `galPhotographyLocation`），没有经纬度 [未验证]。
- **许可**：图片标注为**公共누리 1 型**（署名，可商用，可改作）或 **3 型**（署名，可商用，不可改作）。缩略图属于缩放，是否算「改作」存在灰色地带，建议只采用 1 型。
- **限额**：同 5（开发账号 1,000 次，生产账号可申请提高）。
- **结论**：**可能**。图片偏「官方宣传照」，美学质量中等偏上，且只有被摄体坐标。

## 7. Library of Congress：Carol M. Highsmith Archive

- **是什么**：摄影师 Highsmith 系统拍摄的美国建筑、城市和风景，**超过 7 万张**，预计会超过 10 万张。参见 https://www.loc.gov/collections/carol-m-highsmith/about-this-collection/
- **质量信号**：单一职业摄影师的作品，技术稳定；但属于纪实存档，不是逐张评审。
- **坐标**：只有地点文字（城市、州、建筑名），**无经纬度**，需要地理编码或匹配 Wikidata。
- **访问**：loc.gov JSON API（在 URL 后加 `?fo=json`）[本次未查阅文档]。Commons 上已经有大量 Highsmith 镜像，可能已经带坐标，建议先查 Commons。
- **许可**：作者声明进入公有领域，可商用；照片中的艺术品可能另有版权。
- **结论**：**可能**。适合优先从 Commons 已有镜像中筛选。

## 8. Wikidata：P18（图像）+ P1259（相机坐标）

- SPARQL `?i wdt:P1259 ?v; wdt:P18 ?img` 共 **3,821** 条 [实测，query.wikidata.org]。量很小。
- 更大的集合是 P18 + P625（被摄体坐标），有数百万条。其中的图片若属于 QI/FP，现有管线大概率已覆盖。
- **结论**：**可能**，可以顺手合并。也可以用 P625 给缺少相机坐标的 Commons 质量图补「被摄体坐标」。

## 9. Europeana

- 1,700 万以上对象有经纬度（`location`/`coverageLocation`/`currentLocation`），支持 `qf=distance(location,lat,lon,km)`。参见 https://europeana.atlassian.net/wiki/spaces/EF/pages/2385739812
- 需要免费的 `wskey`。可以用 `reusability=open` 筛选 CC0、BY、BY-SA 等可复用条目 [参数名凭记忆]。
- **问题**：以馆藏和历史照片为主，没有美学策展；坐标多为地点或机构位置。
- **结论**：**可能（低）**。

## 10. Geograph Deutschland 等分站

- Geograph 的德国分站（https://geo.hlipp.de ，2008 年至今），CC BY-SA 2.0，系统与 UK 站一致（应有相机和被摄体位置）。规模未核实，CC wiki 写的约 1,733 张很可能已过时 [未验证]。
- **结论**：**可能（低）**。社区纪实，质量参差，需要靠评分筛选。

## 11. 日本来源

- **ジャパンサーチ（Japan Search）**：国家级聚合平台，有 SPARQL 和 Web API。每个数据库自带二次利用条件（PDM、CC BY 等 15 种），部分条目有经纬度。但内容以馆藏和地方资料为主，美学策展弱。参见 https://jpsearch.go.jp ，以及非官方说明 https://kanzaki.com/works/ld/jpsearch/
- **自治体或观光协会照片库**：例如冈山观光照片库限定用于观光宣传，不可用于一般商品广告，且需申请（ https://www.okayama-kanko.jp/setouchi/business/photos/terms.html ）；文京区フォトギャラリー有地图显示，但许可不明。这类来源分散、需要申请、许可不统一。
- **「日本の絶景」类榜单、写真コンテスト受賞作**：没有找到带坐标的开放数据；获奖作版权归作者。
- **结论**：**暂不**。可以把 WLM/WLE 日本赛和 Commons 上的日本 QI 作为主力。

## 12. 美国 NPS Data API

- https://www.nps.gov/developer ，免费 key，约 1,000 次/小时（二手资料）。`/parks`、`/places` 带图片和公园或地点坐标。
- 图片带 credit 字段，多数为 NPS 公有领域，但有部分第三方版权 [未验证]。坐标为被摄体或区域。
- **结论**：**暂不**。

## 13. iNaturalist Open Data

- AWS Open Data 上有照片和观测坐标（坐标约等于拍摄位置），许可为 CC0、BY、BY-NC 混合。
- 「Research Grade」代表物种鉴定可信，与摄影质量无关；题材是物种特写，不是风景。
- **结论**：**不用**。

## 14. Openverse / Pexels / Pixabay

- **Openverse** 结果字段共 25 个，**无任何地理字段** [实测 api.openverse.org]。
- **Pexels** Photo 资源**无地理字段**；限额 200 次/小时、2 万次/月；条款禁止「复制 Pexels 的核心功能」。参见 https://www.pexels.com/api/documentation/
- **Pixabay** hits **无地理字段**；禁止永久热链，需要自行下载；禁止批量系统性下载；每个查询最多 500 条。参见 https://pixabay.com/api/docs/
- **结论**：**不用**。

## 15. 国际摄影大赛

涉及 Astronomy Photographer of the Year、Natural Landscape Photography Awards（RAW 审核，「真实性」信号最强）、Landscape Photographer of the Year、TPOTY、Sony World Photography Awards、EPSON Pano、Drone/Aerial Awards 等。

- 获奖作通常只附**地名文字**（例如「Grand Canyon」「Tasmania」），没有经纬度。
- 作者保留版权。APOTY 规则只授权皇家天文台自己做宣传和展览（ https://www.rmg.co.uk/whats-on/astronomy-photographer-year/competition-rules ）。没有找到任何允许第三方展示的开放许可。
- **结论**：**不用于展示照片**。可以把获奖作的地名当作「候选机位线索」：地理编码后，用 Commons 地理搜索找附近的 QI/FP 照片，再链接到大赛原页面（只放链接，不镜像图片）。

## 16. 其他（均为不用）

- **NatGeo Your Shot**：网站已于 2019-10-31 关闭，迁到 Instagram 标签（ https://petapixel.com/2019/09/03/disney-shutting-down-natgeo-your-shot-website-to-focus-on-instagram ）。
- **Atlas Obscura、Google Arts & Culture**：没有公开 API，内容版权归原方 [未查阅具体 ToS]。
- **图虫、视觉中国**：商业图库，只有付费授权，没有开放数据 [未验证]。
- **Panoramax、Mapillary 类**：街景，非艺术类。

---

## 建议的落地顺序

1. 抓取 WLM 提名/获奖作（26.6k）和 WLE 获奖作（1.8k），与现有集合按 pageid 去重。约 1.5 万张有相机坐标，可以直接入库。
2. 对缺少 `{{Location}}` 的文件，依次尝试 SDC P1259（取朝向 P7787）、EXIF GPS、古迹/保护区 ID 对应 Wikidata P625（标记为「被摄体位置」）。
3. 用 OSM 观景点为照片计算「经典机位」权重；带 `direction` 的观景点可以画视线。
4. 再评估韩国 Photo Korea 获奖作 API：下载规格 zip，确认字段和规模后决定是否接入。

## 本次调研中实测的命令或接口（便于复现）

- PetScan：`https://petscan.wmcloud.org/?language=commons&project=wikimedia&categories=Nominated_and_winning_pictures_of_Wiki_Loves_Monuments&depth=7&ns[6]=1&format=tsv&doit=1`
- 坐标覆盖：`https://commons.wikimedia.org/w/api.php?action=query&prop=coordinates&coprimary=all&titles=...`（POST，每批 50 个）
- Wikidata：`SELECT (COUNT(*) AS ?c) WHERE { ?i wdt:P1259 ?v . ?i wdt:P18 ?img }` → 3821
- taginfo：`https://taginfo.openstreetmap.org/api/4/tag/combinations?key=tourism&value=viewpoint`
