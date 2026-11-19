// コマ画像（JPEG）とナレーション（AIFF）から H.264/AAC の MP4 を作る
// 使い方: swift assemble.swift build/frames build/timeline.json build/audio out.mp4
import AVFoundation
import Foundation
import ImageIO

let a = CommandLine.arguments
let framesDir = a[1], timelinePath = a[2], audioDir = a[3], outPath = a[4]
let W = 1280, H = 720

struct Meta: Decodable { let fps: Int; let n: Int }
struct Seg: Decodable { let id: String; let s: Double; let lead: Double }
let meta = try JSONDecoder().decode(Meta.self, from: Data(contentsOf: URL(fileURLWithPath: framesDir + "/meta.json")))
let segs = try JSONDecoder().decode([Seg].self, from: Data(contentsOf: URL(fileURLWithPath: timelinePath)))

// 1) 映像だけの MP4
let videoURL = URL(fileURLWithPath: outPath + ".video.mp4")
try? FileManager.default.removeItem(at: videoURL)
let writer = try AVAssetWriter(outputURL: videoURL, fileType: .mp4)
let input = AVAssetWriterInput(mediaType: .video, outputSettings: [
  AVVideoCodecKey: AVVideoCodecType.h264, AVVideoWidthKey: W, AVVideoHeightKey: H,
  AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: 6_000_000, AVVideoProfileLevelKey: AVVideoProfileLevelH264HighAutoLevel]
])
input.expectsMediaDataInRealTime = false
let adaptor = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input, sourcePixelBufferAttributes: [
  kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32ARGB,
  kCVPixelBufferWidthKey as String: W, kCVPixelBufferHeightKey as String: H
])
writer.add(input)
writer.startWriting()
writer.startSession(atSourceTime: .zero)
for i in 0..<meta.n {
  while !input.isReadyForMoreMediaData { usleep(2000) }
  let url = URL(fileURLWithPath: String(format: "%@/f%05d.jpg", framesDir, i))
  guard let src = CGImageSourceCreateWithURL(url as CFURL, nil), let img = CGImageSourceCreateImageAtIndex(src, 0, nil) else {
    print("missing frame", i); exit(1)
  }
  var pb: CVPixelBuffer?
  CVPixelBufferPoolCreatePixelBuffer(nil, adaptor.pixelBufferPool!, &pb)
  guard let buf = pb else { print("no buffer"); exit(1) }
  CVPixelBufferLockBaseAddress(buf, [])
  let ctx = CGContext(data: CVPixelBufferGetBaseAddress(buf), width: W, height: H, bitsPerComponent: 8,
                      bytesPerRow: CVPixelBufferGetBytesPerRow(buf), space: CGColorSpace(name: CGColorSpace.sRGB)!,
                      bitmapInfo: CGImageAlphaInfo.noneSkipFirst.rawValue)!
  ctx.draw(img, in: CGRect(x: 0, y: 0, width: W, height: H))
  CVPixelBufferUnlockBaseAddress(buf, [])
  adaptor.append(buf, withPresentationTime: CMTime(value: Int64(i), timescale: Int32(meta.fps)))
  if i % 600 == 0 { print("video", i, "/", meta.n) }
}
input.markAsFinished()
let sem = DispatchSemaphore(value: 0)
writer.finishWriting { sem.signal() }
sem.wait()
if writer.status != .completed { print("writer failed", writer.error as Any); exit(1) }

// 2) 映像＋ナレーションを合成
let comp = AVMutableComposition()
let vAsset = AVURLAsset(url: videoURL)
let vTrack = vAsset.tracks(withMediaType: .video).first!
let cv = comp.addMutableTrack(withMediaType: .video, preferredTrackID: kCMPersistentTrackID_Invalid)!
try cv.insertTimeRange(CMTimeRange(start: .zero, duration: vAsset.duration), of: vTrack, at: .zero)
let ca = comp.addMutableTrack(withMediaType: .audio, preferredTrackID: kCMPersistentTrackID_Invalid)!
for s in segs {
  let aAsset = AVURLAsset(url: URL(fileURLWithPath: "\(audioDir)/\(s.id).aiff"))
  guard let at = aAsset.tracks(withMediaType: .audio).first else { continue }
  let start = CMTime(seconds: s.s + s.lead, preferredTimescale: 600)
  if ca.timeRange.duration < start {
    let cur = ca.timeRange.duration
    ca.insertEmptyTimeRange(CMTimeRange(start: cur, end: start))
  }
  try ca.insertTimeRange(CMTimeRange(start: .zero, duration: aAsset.duration), of: at, at: start)
}
let outURL = URL(fileURLWithPath: outPath)
try? FileManager.default.removeItem(at: outURL)
let ex = AVAssetExportSession(asset: comp, presetName: AVAssetExportPresetHighestQuality)!
ex.outputURL = outURL
ex.outputFileType = .mp4
ex.exportAsynchronously { sem.signal() }
sem.wait()
if ex.status != .completed { print("export failed", ex.error as Any); exit(1) }
try? FileManager.default.removeItem(at: videoURL)
print("done", outPath, CMTimeGetSeconds(comp.duration))
