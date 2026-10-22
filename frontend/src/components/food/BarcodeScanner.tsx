import { BrowserMultiFormatReader, type IScannerControls } from "@zxing/browser"
import { BarcodeFormat, DecodeHintType } from "@zxing/library"
import { useEffect, useRef, useState } from "react"
import { Button } from "../ui/Button.tsx"
import { Input } from "../ui/Input.tsx"

// Supermarket barcodes: EAN-13 (UK/Europe), UPC-A/E (US), EAN-8 (small packs).
const FORMATS = [BarcodeFormat.EAN_13, BarcodeFormat.EAN_8, BarcodeFormat.UPC_A, BarcodeFormat.UPC_E]

function cameraAvailable(): boolean {
  // mediaDevices is missing on plain HTTP and in some in-app browsers.
  return typeof navigator.mediaDevices?.getUserMedia === "function"
}

/**
 * Full-screen camera view that reads a food barcode with the back camera.
 * Works in Safari on iPhone and Chrome on Android (the site is served over
 * HTTPS, which browsers require for the camera). If the camera is blocked or
 * missing, the number printed under the barcode can be typed instead.
 */
export default function BarcodeScanner({ onDetected, onClose }: { onDetected: (code: string) => void; onClose: () => void }) {
  const video = useRef<HTMLVideoElement>(null)
  const [problem, setProblem] = useState(() => (cameraAvailable()
    ? "" : "This browser can't use the camera. Type the number under the barcode instead."))
  const [typed, setTyped] = useState("")
  const detected = useRef(onDetected)
  useEffect(() => { detected.current = onDetected })

  useEffect(() => {
    let controls: IScannerControls | null = null
    let stopped = false
    const hints = new Map<DecodeHintType, unknown>([[DecodeHintType.POSSIBLE_FORMATS, FORMATS], [DecodeHintType.TRY_HARDER, true]])
    const reader = new BrowserMultiFormatReader(hints, { delayBetweenScanAttempts: 150 })
    if (!cameraAvailable()) return
    reader
      .decodeFromConstraints(
        { video: { facingMode: { ideal: "environment" }, width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false },
        video.current ?? undefined,
        (result, _error, scanControls) => {
          if (result && !stopped) {
            stopped = true
            scanControls.stop()
            navigator.vibrate?.(60)
            detected.current(result.getText())
          }
        },
      )
      .then((started) => {
        controls = started
        if (stopped) started.stop()
      })
      .catch((error: unknown) => {
        const name = error instanceof DOMException ? error.name : ""
        setProblem(name === "NotAllowedError"
          ? "Camera access is off for this site. Allow it in your browser settings, or type the number under the barcode."
          : "The camera couldn't start. Type the number under the barcode instead.")
      })
    const overflow = document.body.style.overflow
    document.body.style.overflow = "hidden"
    return () => {
      stopped = true
      controls?.stop()
      document.body.style.overflow = overflow
    }
  }, [])

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => { if (event.key === "Escape") onClose() }
    document.addEventListener("keydown", onKey)
    return () => document.removeEventListener("keydown", onKey)
  }, [onClose])

  const digits = typed.replace(/\D/g, "")

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-black text-white" role="dialog" aria-modal="true" aria-label="Scan a barcode">
      <div className="flex items-center justify-between px-4 pb-3 pt-[max(1rem,env(safe-area-inset-top))]">
        <p className="font-display text-lg font-medium">Scan a barcode</p>
        <button type="button" className="rounded-full px-3 py-2 text-sm font-semibold hover:bg-white/10 focus-visible:outline-2 focus-visible:outline-white" onClick={onClose}>
          Cancel
        </button>
      </div>
      <div className="relative flex-1 overflow-hidden">
        <video ref={video} className="h-full w-full object-cover" muted playsInline autoPlay />
        {!problem ? (
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center" aria-hidden="true">
            <div className="h-40 w-[78%] max-w-sm rounded-3xl border-4 border-white/90 shadow-[0_0_0_9999px_rgba(0,0,0,0.45)]" />
          </div>
        ) : null}
        {!problem ? (
          <p className="absolute inset-x-0 bottom-6 px-6 text-center text-sm text-white/90">Hold the barcode inside the box. It scans by itself.</p>
        ) : null}
      </div>
      <form
        className="space-y-3 bg-card px-4 pt-4 text-ink pb-[max(1rem,env(safe-area-inset-bottom))]"
        onSubmit={(event) => { event.preventDefault(); if (digits.length >= 8) onDetected(digits) }}
      >
        {problem ? <p className="text-sm text-danger" role="alert">{problem}</p> : null}
        <div className="flex items-end gap-2">
          <div className="min-w-0 flex-1">
            <Input label="Or type the barcode number" inputMode="numeric" autoComplete="off" value={typed} onChange={(event) => setTyped(event.target.value)} placeholder="5000112637922" />
          </div>
          <Button type="submit" disabled={digits.length < 8 || digits.length > 14}>Look up</Button>
        </div>
      </form>
    </div>
  )
}
