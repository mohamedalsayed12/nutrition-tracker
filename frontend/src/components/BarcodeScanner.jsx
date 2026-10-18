import { useEffect, useRef, useState } from 'react'

export default function BarcodeScanner({ onDetected, onClose }) {
  const videoRef = useRef(null)
  const [error, setError] = useState('')
  const [manual, setManual] = useState('')

  useEffect(() => {
    let stream
    let active = true
    let frameHandle

    async function start() {
      try {
        if (!navigator.mediaDevices?.getUserMedia) {
          setError('Camera is not available here. Enter the barcode digits instead.')
          return
        }
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: 'environment' } },
          audio: false,
        })
        if (!active || !videoRef.current) return
        videoRef.current.srcObject = stream
        await videoRef.current.play()

        if (!('BarcodeDetector' in window)) {
          setError('Live scanning is not supported in this browser. Enter the barcode below.')
          return
        }
        const detector = new window.BarcodeDetector({
          formats: ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128', 'qr_code'],
        })
        const tick = async () => {
          if (!active || !videoRef.current) return
          try {
            const codes = await detector.detect(videoRef.current)
            if (codes[0]?.rawValue) {
              onDetected(String(codes[0].rawValue))
              return
            }
          } catch {
            // Keep trying while the camera is open.
          }
          frameHandle = window.setTimeout(tick, 350)
        }
        tick()
      } catch {
        setError('Could not open the camera. Enter the barcode digits instead.')
      }
    }

    start()
    return () => {
      active = false
      window.clearTimeout(frameHandle)
      stream?.getTracks().forEach((track) => track.stop())
    }
  }, [onDetected])

  return (
    <div className="scanner-card card">
      <div className="scanner-card__head">
        <h2>Scan barcode</h2>
        <button type="button" className="text-btn" onClick={onClose}>Close</button>
      </div>
      <video ref={videoRef} className="scanner-video" muted playsInline />
      {error && <p className="muted">{error}</p>}
      <form
        className="barcode-manual"
        onSubmit={(event) => {
          event.preventDefault()
          if (manual.trim()) onDetected(manual.trim())
        }}
      >
        <input
          value={manual}
          onChange={(e) => setManual(e.target.value)}
          inputMode="numeric"
          placeholder="Or type barcode digits"
          aria-label="Barcode number"
        />
        <button type="submit" className="btn-green">Look up</button>
      </form>
    </div>
  )
}
