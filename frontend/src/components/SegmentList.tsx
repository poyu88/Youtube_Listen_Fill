import { useEffect, useRef } from "react";
import type { Segment } from "../types";
import { formatDuration } from "../utils";

interface SegmentListProps {
  segments: Segment[];
  currentIndex: number;
  onSelect: (index: number) => void;
}

/**
 * 將目前作用中的項目捲至列表可視區中央。
 */
function scrollActiveIntoList(list: HTMLElement, active: HTMLElement): void {
  const listRect = list.getBoundingClientRect();
  const activeRect = active.getBoundingClientRect();
  // 以「相對列表目前捲動位置」計算，避免 offsetParent 造成定位跑掉
  const relativeTop = activeRect.top - listRect.top + list.scrollTop;
  const targetTop = relativeTop - list.clientHeight / 2 + activeRect.height / 2;
  const maxTop = Math.max(0, list.scrollHeight - list.clientHeight);
  list.scrollTo({
    top: Math.min(Math.max(0, targetTop), maxTop),
    behavior: "smooth",
  });
}

/**
 * 字幕分段列表，點擊可跳轉至對應時間；目前段會自動捲入可視區。
 */
export default function SegmentList({ segments, currentIndex, onSelect }: SegmentListProps) {
  const listRef = useRef<HTMLUListElement>(null);
  const itemRefs = useRef<Map<number, HTMLLIElement>>(new Map());

  useEffect(() => {
    const list = listRef.current;
    const active = itemRefs.current.get(currentIndex);
    if (!list || !active || list.clientHeight <= 0) return;

    const frame = window.requestAnimationFrame(() => {
      scrollActiveIntoList(list, active);
    });
    return () => window.cancelAnimationFrame(frame);
  }, [currentIndex]);

  return (
    <div className="segment-list">
      <h3>字幕分段列表</h3>
      <ul ref={listRef}>
        {segments.map((segment) => {
          const isActive = segment.index === currentIndex;
          return (
            <li
              key={segment.index}
              ref={(el) => {
                if (el) itemRefs.current.set(segment.index, el);
                else itemRefs.current.delete(segment.index);
              }}
            >
              <button
                type="button"
                className={isActive ? "active" : ""}
                onClick={() => onSelect(segment.index)}
              >
                <span className="seg-time">{formatDuration(segment.start)}</span>
                <span className="seg-text">{segment.text}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
