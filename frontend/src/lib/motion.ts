import { useEffect, useRef, useState } from "react";

/** True when the visitor asked the OS to reduce motion. jsdom has no matchMedia, so default off. */
export function prefersReducedMotion(): boolean {
  return typeof window !== "undefined" && typeof window.matchMedia === "function"
    ? window.matchMedia("(prefers-reduced-motion: reduce)").matches
    : false;
}

const easeOutCubic = (t: number) => 1 - (1 - t) ** 3;

/** Animate a number from its previous value to `target` over `ms`; jumps when motion is reduced. */
export function useCountUp(target: number | null, ms = 900): number | null {
  const [value, setValue] = useState<number | null>(target === null ? null : 0);
  const current = useRef(value);
  current.current = value;

  useEffect(() => {
    if (target === null || prefersReducedMotion() || typeof requestAnimationFrame !== "function") {
      setValue(target);
      return;
    }
    const from = current.current ?? 0;
    const start = performance.now();
    let frame = 0;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / ms);
      setValue(from + (target - from) * easeOutCubic(t));
      if (t < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [target, ms]);

  return value;
}

/** Becomes true on the first frame after mount, so CSS transitions can run from an initial state. */
export function useMounted(): boolean {
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    const id = requestAnimationFrame(() => setMounted(true));
    return () => cancelAnimationFrame(id);
  }, []);
  return mounted;
}
