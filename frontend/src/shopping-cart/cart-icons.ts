import { AvocadoIcon, BreadIcon, EggIcon, JarIcon, TomatoIcon } from "./icons";

const iconMatchers = [
  { keywords: ["egg", "eggs"], Icon: EggIcon },
  { keywords: ["bread"], Icon: BreadIcon },
  { keywords: ["tomato", "tomatoes"], Icon: TomatoIcon },
  { keywords: ["avocado", "avocados"], Icon: AvocadoIcon },
];

export function getIconForItem(name: string) {
  const words = name
    .toLowerCase()
    .replace(/[^a-z]/g, " ")
    .split(/\s+/)
    .filter(Boolean);
  for (const entry of iconMatchers) {
    if (entry.keywords.some((keyword) => words.includes(keyword))) {
      return entry.Icon;
    }
  }
  return JarIcon;
}
