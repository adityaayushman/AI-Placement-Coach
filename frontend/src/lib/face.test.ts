import { expect, test } from "vitest";

import { summarize, type FaceSample } from "./face";

const facing: FaceSample = { present: true, yaw: 0.02, pitch: -0.03, gazeAway: 0.1, smile: 0.3 };
const away: FaceSample = { present: true, yaw: 0.6, pitch: 0.1, gazeAway: 0.2, smile: 0.0 };
const missing: FaceSample = { present: false, yaw: 0, pitch: 0, gazeAway: 0, smile: 0 };

test("summarises presence, eye contact, smile and head motion", () => {
  const s = summarize([facing, facing, facing, away, missing]);
  expect(s.frames).toBe(5);
  expect(s.face_present_ratio).toBe(0.8);
  expect(s.eye_contact_ratio).toBe(0.75);
  expect(s.smile_mean).toBe(0.225);
  expect(s.head_motion).toBeGreaterThan(0);
});

test("empty clip yields zeros instead of NaN", () => {
  expect(summarize([])).toEqual({
    frames: 0, face_present_ratio: 0, eye_contact_ratio: 0, smile_mean: 0, head_motion: 0,
  });
});
