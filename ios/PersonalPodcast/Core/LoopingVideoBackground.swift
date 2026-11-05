import AVFoundation
import SwiftUI
import UIKit

/// Full-bleed achtergrondvideo die stil en in een lus afspeelt (aspect-fill).
struct LoopingVideoBackground: UIViewRepresentable {
    let resourceName: String
    let resourceExtension: String

    func makeUIView(context: Context) -> LoopingPlayerView {
        let view = LoopingPlayerView()
        view.load(name: resourceName, ext: resourceExtension)
        return view
    }

    func updateUIView(_ uiView: LoopingPlayerView, context: Context) {}

    static func dismantleUIView(_ uiView: LoopingPlayerView, coordinator: ()) {
        uiView.stop()
    }
}

final class LoopingPlayerView: UIView {
    override class var layerClass: AnyClass { AVPlayerLayer.self }

    private var playerLayer: AVPlayerLayer { layer as! AVPlayerLayer }
    private var queuePlayer: AVQueuePlayer?
    private var looper: AVPlayerLooper?
    private var observers: [NSObjectProtocol] = []

    override init(frame: CGRect) {
        super.init(frame: frame)
        isUserInteractionEnabled = false
        backgroundColor = .black
        playerLayer.videoGravity = .resizeAspectFill
        listenForLifecycle()
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    func load(name: String, ext: String) {
        guard let url = Bundle.main.url(forResource: name, withExtension: ext) else {
            print("LoopingVideoBackground: \(name).\(ext) niet in de bundle")
            return
        }
        let item = AVPlayerItem(url: url)
        let queue = AVQueuePlayer()
        queue.isMuted = true
        queue.actionAtItemEnd = .none
        looper = AVPlayerLooper(player: queue, templateItem: item)
        queuePlayer = queue
        playerLayer.player = queue
        queue.play()
    }

    func stop() {
        queuePlayer?.pause()
        looper?.disableLooping()
        looper = nil
        queuePlayer = nil
        playerLayer.player = nil
    }

    private func listenForLifecycle() {
        let center = NotificationCenter.default
        observers.append(center.addObserver(forName: UIApplication.didEnterBackgroundNotification, object: nil, queue: .main) { [weak self] _ in
            self?.queuePlayer?.pause()
        })
        observers.append(center.addObserver(forName: UIApplication.willEnterForegroundNotification, object: nil, queue: .main) { [weak self] _ in
            self?.queuePlayer?.play()
        })
    }

    deinit {
        observers.forEach(NotificationCenter.default.removeObserver)
        stop()
    }
}
