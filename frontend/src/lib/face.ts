/**
 * In-browser face signals for mock interviews (MediaPipe Face Landmarker). Video never leaves the
 * browser: we sample a few frames per second and send only the summary numbers below.
 * The signals are indicative (camera angle and lighting matter) and are not emotion detection.
 */
import type { FaceLandmarker } from "@mediapipe/tasks-vision";

const WASM = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm";
const MODEL =
  "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task";

export interface FaceSample {
  present: boolean;
  yaw: number; // radians, 0 = facing camera
  pitch: number;
  gazeAway: number; // 0..1 from eye-look blendshapes
  smile: number; // 0..1
}

export interface FaceSignals {
  frames: number;
  face_present_ratio: number;
  eye_contact_ratio: number;
  smile_mean: number;
  head_motion: number;
}

const FACING = 0.26; // about 15 degrees
const std = (xs: number[]) => {
  if (xs.length < 2) return 0;
  const m = xs.reduce((a, b) => a + b, 0) / xs.length;
  return Math.sqrt(xs.reduce((a, b) => a + (b - m) ** 2, 0) / xs.length);
};

export function summarize(samples: FaceSample[]): FaceSignals {
  const seen = samples.filter((s) => s.present);
  const contact = seen.filter((s) => Math.abs(s.yaw) < FACING && Math.abs(s.pitch) < FACING && s.gazeAway < 0.5);
  const round = (x: number) => Math.round(x * 1000) / 1000;
  return {
    frames: samples.length,
    face_present_ratio: round(samples.length ? seen.length / samples.length : 0),
    eye_contact_ratio: round(seen.length ? contact.length / seen.length : 0),
    smile_mean: round(seen.length ? seen.reduce((a, s) => a + s.smile, 0) / seen.length : 0),
    head_motion: round((std(seen.map((s) => s.yaw)) + std(seen.map((s) => s.pitch))) / 2),
  };
}

let landmarker: Promise<FaceLandmarker> | null = null;

async function load(): Promise<FaceLandmarker> {
  const { FaceLandmarker, FilesetResolver } = await import("@mediapipe/tasks-vision");
  const files = await FilesetResolver.forVisionTasks(WASM);
  return FaceLandmarker.createFromOptions(files, {
    baseOptions: { modelAssetPath: MODEL, delegate: "GPU" },
    outputFaceBlendshapes: true,
    outputFacialTransformationMatrixes: true,
    runningMode: "VIDEO",
    numFaces: 1,
  });
}

function sampleFrom(lm: FaceLandmarker, video: HTMLVideoElement): FaceSample {
  const r = lm.detectForVideo(video, performance.now());
  const matrix = r.facialTransformationMatrixes?.[0]?.data;
  const shapes = r.faceBlendshapes?.[0]?.categories;
  if (!matrix || !shapes) return { present: false, yaw: 0, pitch: 0, gazeAway: 0, smile: 0 };
  const score = (name: string) => shapes.find((c) => c.categoryName === name)?.score ?? 0;
  // Column-major 4x4 rotation: yaw from the forward axis, pitch from its vertical component.
  const yaw = Math.atan2(matrix[8], matrix[10]);
  const pitch = Math.asin(Math.max(-1, Math.min(1, -matrix[9])));
  const gazeAway = Math.max(
    (score("eyeLookOutLeft") + score("eyeLookInRight")) / 2,
    (score("eyeLookOutRight") + score("eyeLookInLeft")) / 2,
    (score("eyeLookUpLeft") + score("eyeLookUpRight")) / 2,
    (score("eyeLookDownLeft") + score("eyeLookDownRight")) / 2,
  );
  return { present: true, yaw, pitch, gazeAway, smile: (score("mouthSmileLeft") + score("mouthSmileRight")) / 2 };
}

/** Start sampling about five frames a second. Call the returned function to stop and summarise. */
export async function trackFace(video: HTMLVideoElement): Promise<() => FaceSignals> {
  landmarker ??= load();
  const lm = await landmarker;
  const samples: FaceSample[] = [];
  const timer = window.setInterval(() => {
    if (video.readyState >= 2) samples.push(sampleFrom(lm, video));
  }, 200);
  return () => {
    window.clearInterval(timer);
    return summarize(samples);
  };
}
