import { useMutation, useQuery } from "@tanstack/react-query";
import { useRef, useState } from "react";

import { api } from "../api/client";
import type { Consent, InterviewAnswer, InterviewSession } from "../api/types";
import Icon from "../components/Icon";
import { Empty, ErrorNote, Field, Meter, PageHeader, Panel } from "../components/ui";
import { trackFace, type FaceSignals } from "../lib/face";
import { toWav } from "../lib/wav";

type Recognition = {
  continuous: boolean;
  interimResults: boolean;
  onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  start: () => void;
  stop: () => void;
};

function makeRecognition(): Recognition | null {
  const w = window as unknown as { SpeechRecognition?: new () => Recognition; webkitSpeechRecognition?: new () => Recognition };
  const Ctor = w.SpeechRecognition ?? w.webkitSpeechRecognition;
  return Ctor ? new Ctor() : null;
}

export default function Interview() {
  const [companyType, setCompanyType] = useState<"product" | "service">("product");
  const [session, setSession] = useState<InterviewSession | null>(null);
  const [index, setIndex] = useState(0);
  const [results, setResults] = useState<Record<number, InterviewAnswer>>({});
  const consents = useQuery({ queryKey: ["consents"], queryFn: () => api<Consent[]>("/consents") });
  const granted = (scope: string) => consents.data?.find((c) => c.scope === scope)?.granted ?? false;
  const canRecord = granted("interview_recording");
  const canFace = granted("face_analysis");

  const start = useMutation({
    mutationFn: () => api<InterviewSession>("/interviews/sessions", { json: { company_type: companyType } }),
    onSuccess: (s) => {
      setSession(s);
      setIndex(0);
      setResults({});
    },
  });

  if (!session) {
    return (
      <>
        <PageHeader title="Mock interview" lede="Four questions: HR, behavioural, technical and DSA. Answer out loud or type. You get scores for content, communication, delivery and confidence after each one." />
        <Panel className="max-w-xl">
          <Field label="Company type">
            <select className="input" value={companyType} onChange={(e) => setCompanyType(e.target.value as "product" | "service")}>
              <option value="product">Product company</option>
              <option value="service">Service company</option>
            </select>
          </Field>
          <p className="mt-4 text-sm text-muted">
            {canRecord ? "Audio recording is on. We keep your recording until you delete your data." : "Audio recording is off, so you will type your answers. Turn on Interview audio on the Privacy page to speak instead."}
          </p>
          <p className="mt-2 text-sm text-muted">
            {canFace ? "Camera signals are on. Your video stays in this browser; we only receive eye-contact and framing numbers." : "Camera signals are off. Turn on Camera signals on the Privacy page to get eye-contact feedback."}
          </p>
          <button type="button" className="btn-primary mt-6" onClick={() => start.mutate()} disabled={start.isPending}>
            {start.isPending ? "Preparing" : "Start interview"}
          </button>
          <ErrorNote error={start.error} />
        </Panel>
      </>
    );
  }

  const q = session.questions[index];
  const done = Object.keys(results).length === session.questions.length;
  return (
    <>
      <PageHeader title="Mock interview" lede={`Question ${index + 1} of ${session.questions.length}`} />
      <div className="stagger grid gap-6 xl:grid-cols-[1fr_22rem]">
        <AnswerBox key={q.id} sessionId={session.id} question={q} canRecord={canRecord} canFace={canFace}
          result={results[q.id]} onScored={(a) => setResults({ ...results, [q.id]: a })} />
        <Panel title="Progress">
          <ol className="space-y-2">
            {session.questions.map((sq, i) => (
              <li key={sq.id}>
                <button type="button" onClick={() => setIndex(i)}
                  className={`flex min-h-[44px] w-full cursor-pointer items-center justify-between gap-3 rounded-xl px-3 text-left text-sm transition-colors duration-200 ${
                    i === index ? "bg-white/10 text-ink" : "text-muted hover:bg-white/5"}`}>
                  <span className="capitalize">{sq.category}</span>
                  {results[sq.id] ? <span className="tabular-nums text-ok">{Math.round(results[sq.id].scores.overall)}</span> : <span className="text-faint">Pending</span>}
                </button>
              </li>
            ))}
          </ol>
          {done ? (
            <button type="button" className="btn-primary mt-4 w-full" onClick={() => setSession(null)}>Finish</button>
          ) : index < session.questions.length - 1 && results[q.id] ? (
            <button type="button" className="btn-ghost mt-4 w-full" onClick={() => setIndex(index + 1)}>Next question</button>
          ) : null}
        </Panel>
      </div>
    </>
  );
}

function AnswerBox({ sessionId, question, canRecord, canFace, result, onScored }: {
  sessionId: number;
  question: InterviewSession["questions"][number];
  canRecord: boolean;
  canFace: boolean;
  result?: InterviewAnswer;
  onScored: (a: InterviewAnswer) => void;
}) {
  const [transcript, setTranscript] = useState("");
  const [recording, setRecording] = useState(false);
  const [audio, setAudio] = useState<Blob | null>(null);
  const [micError, setMicError] = useState<string | null>(null);
  const recorder = useRef<MediaRecorder | null>(null);
  const recognition = useRef<Recognition | null>(null);
  const video = useRef<HTMLVideoElement | null>(null);
  const camStream = useRef<MediaStream | null>(null);
  const stopFace = useRef<(() => FaceSignals) | null>(null);
  const [face, setFace] = useState<FaceSignals | null>(null);
  const [camOn, setCamOn] = useState(false);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 320, height: 240 } });
      camStream.current = stream;
      setCamOn(true);
      if (video.current) {
        video.current.srcObject = stream;
        await video.current.play();
        stopFace.current = await trackFace(video.current);
      }
    } catch {
      setMicError("Camera unavailable, so face signals are skipped for this answer.");
    }
  };
  const stopCamera = () => {
    if (stopFace.current) setFace(stopFace.current());
    stopFace.current = null;
    camStream.current?.getTracks().forEach((t) => t.stop());
    camStream.current = null;
    setCamOn(false);
  };

  const startRec = async () => {
    setMicError(null);
    setFace(null);
    if (canFace) void startCamera();
    if (!canRecord) {
      setRecording(true);
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const chunks: Blob[] = [];
      const rec = new MediaRecorder(stream);
      rec.ondataavailable = (e) => chunks.push(e.data);
      rec.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        try {
          setAudio(await toWav(new Blob(chunks, { type: rec.mimeType })));
        } catch {
          setMicError("Could not process the recording. Type your answer instead.");
        }
      };
      rec.start();
      recorder.current = rec;
      const sr = makeRecognition();
      if (sr) {
        sr.continuous = true;
        sr.interimResults = false;
        sr.onresult = (e) => setTranscript(Array.from(e.results).map((r) => r[0].transcript).join(" "));
        sr.start();
        recognition.current = sr;
      }
      setRecording(true);
    } catch {
      setMicError("Microphone access was blocked. Type your answer instead.");
    }
  };
  const stopRec = () => {
    stopCamera();
    recorder.current?.stop();
    recognition.current?.stop();
    setRecording(false);
  };

  const submit = useMutation({
    mutationFn: () => {
      const form = new FormData();
      form.append("question_id", String(question.id));
      form.append("transcript", transcript);
      if (audio) form.append("audio", audio, "answer.wav");
      if (face) form.append("face_metrics", JSON.stringify(face));
      return api<InterviewAnswer>(`/interviews/sessions/${sessionId}/answers`, { form });
    },
    onSuccess: onScored,
  });

  return (
    <div className="space-y-6">
      <Panel eyebrow={question.category}>
        <p className="font-serif text-2xl leading-snug text-ink">{question.prompt}</p>
        <div className="mt-6 space-y-4">
          {(canRecord || canFace) && (
            <div className="flex flex-wrap items-center gap-4">
              <button type="button" onClick={recording ? stopRec : startRec}
                className={recording ? "btn-primary" : "btn-ghost"} aria-pressed={recording}>
                <Icon name={recording ? "stop" : "mic"} size={16} />
                {recording ? "Stop" : audio || face ? "Answer again" : canRecord ? "Record answer" : "Start camera"}
              </button>
              {recording && <span className="flex items-center gap-2 text-sm text-rose"><span className="h-2 w-2 animate-pulse rounded-full bg-rose" />{canRecord ? "Recording" : "Camera on"}</span>}
              {!recording && (audio || face) && (
                <span className="text-sm text-muted">{[audio && "Audio ready", face && ("Camera: " + face.frames + " frames read")].filter(Boolean).join(" · ")}</span>
              )}
              <video ref={video} muted playsInline aria-label="Your camera preview"
                className={"h-24 w-32 -scale-x-100 rounded-xl border border-line object-cover " + (camOn ? "" : "hidden")} />
            </div>
          )}
          {micError && <p role="alert" className="text-sm text-rose">{micError}</p>}
          <Field label="Your answer" hint={canRecord ? "Your browser fills this in while you speak, where supported. Edit it before you submit." : undefined}>
            <textarea className="input min-h-[160px] py-3" value={transcript} onChange={(e) => setTranscript(e.target.value)}
              placeholder="Talk through your answer as you would in the room." />
          </Field>
          <button type="button" className="btn-primary" onClick={() => submit.mutate()}
            disabled={submit.isPending || recording || (!transcript.trim() && !audio)}>
            {submit.isPending ? "Scoring" : result ? "Score again" : "Score my answer"}
          </button>
          <ErrorNote error={submit.error} />
        </div>
      </Panel>

      {result ? (
        <Panel title="Feedback" eyebrow={`Overall ${Math.round(result.scores.overall)}`}>
          <div className="grid gap-5 sm:grid-cols-2">
            <Meter label="Content" value={result.scores.content} hint="Key points covered and closeness to a model answer" />
            <Meter label="Communication" value={result.scores.communication} hint="Length, structure and filler words" />
            <Meter label="Delivery" value={result.scores.delivery} hint={result.scores.delivery === null ? "Needs a voice recording" : "Pace, pauses and pitch variation"} />
            <Meter label="Confidence" value={result.scores.confidence}
              hint={result.scores.details.face_analyzed ? "Hedging, plus camera framing and eye contact (indicative)" : "Hedging language"} />
          </div>
          <ul className="mt-6 space-y-2">
            {result.feedback.map((f) => (
              <li key={f} className="flex gap-3 text-sm text-ink"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-amber" />{f}</li>
            ))}
          </ul>
          <p className="mt-4 text-xs text-faint">Automated scores are rule-based and have not been checked against human raters yet.</p>
        </Panel>
      ) : (
        <Panel><Empty title="No feedback yet">Answer the question to see your scores.</Empty></Panel>
      )}
    </div>
  );
}
