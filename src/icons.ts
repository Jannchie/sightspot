// 界面图标的集中映射（与 junrei 相同的做法）：语义名 → @jannchie/icons 的图标对象
import type { Icon } from "@jannchie/icons";
import {
  IconCalendar,
  IconExternalLink,
  IconFocus,
  IconLocate,
  IconMinus,
  IconMoon,
  IconNavigation,
  IconPlus,
  IconSun,
  IconTheme,
  IconX,
} from "@jannchie/icons";

export const ICONS = {
  close: IconX,
  date: IconCalendar,
  zoomIn: IconPlus,
  zoomOut: IconMinus,
  locate: IconLocate,
  navigate: IconNavigation,
  external: IconExternalLink,
  focus: IconFocus,
  themeAuto: IconTheme,
  themeLight: IconSun,
  themeDark: IconMoon,
} satisfies Record<string, Icon>;
