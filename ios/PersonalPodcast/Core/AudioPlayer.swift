import AVFoundation
import MediaPlayer
import Observation

/// Speelt een aflevering af, ook op de achtergrond en met de bediening op het toegangsscherm.
@MainActor @Observable
final class AudioPlayer {
    private(set) var currentGuid: String?
    private(set) var isPlaying = false
    private(set) var isLoading = false
    private(set) var position: Double = 0
    private(set) var duration: Double = 0

    private var player: AVPlayer?
    private var timeObserver: Any?
    private var endObserver: NSObjectProtocol?
    private var info: [String: Any] = [:]

    func load(guid: String, url: URL, title: String, show: String) {
        if currentGuid == guid { return }
        stop()
        currentGuid = guid
        isLoading = true
        try? AVAudioSession.sharedInstance().setCategory(.playback, mode: .spokenAudio)
        let item = AVPlayerItem(url: url)
        let player = AVPlayer(playerItem: item)
        self.player = player
        info = [MPMediaItemPropertyTitle: title, MPMediaItemPropertyArtist: show]
        timeObserver = player.addPeriodicTimeObserver(forInterval: CMTime(seconds: 0.5, preferredTimescale: 600), queue: .main) { [weak self] time in
            MainActor.assumeIsolated {
                guard let self else { return }
                self.position = time.seconds
                if let d = self.player?.currentItem?.duration.seconds, d.isFinite { self.duration = d; self.isLoading = false }
                self.publish()
            }
        }
        endObserver = NotificationCenter.default.addObserver(forName: .AVPlayerItemDidPlayToEndTime, object: item, queue: .main) { [weak self] _ in
            MainActor.assumeIsolated { self?.isPlaying = false; self?.position = 0; self?.player?.seek(to: .zero) }
        }
        setUpRemoteCommands()
    }

    func toggle() {
        guard let player else { return }
        if isPlaying { player.pause(); isPlaying = false } else {
            try? AVAudioSession.sharedInstance().setActive(true)
            player.play(); isPlaying = true
        }
        publish()
    }

    func seek(to seconds: Double) {
        position = seconds
        player?.seek(to: CMTime(seconds: seconds, preferredTimescale: 600))
    }

    func skip(_ seconds: Double) { seek(to: min(max(0, position + seconds), duration > 0 ? duration : position + seconds)) }

    func stop() {
        if let timeObserver { player?.removeTimeObserver(timeObserver) }
        if let endObserver { NotificationCenter.default.removeObserver(endObserver) }
        player?.pause()
        player = nil; timeObserver = nil; endObserver = nil
        currentGuid = nil; isPlaying = false; position = 0; duration = 0
        MPNowPlayingInfoCenter.default().nowPlayingInfo = nil
    }

    private func publish() {
        info[MPMediaItemPropertyPlaybackDuration] = duration
        info[MPNowPlayingInfoPropertyElapsedPlaybackTime] = position
        info[MPNowPlayingInfoPropertyPlaybackRate] = isPlaying ? 1.0 : 0.0
        MPNowPlayingInfoCenter.default().nowPlayingInfo = info
    }

    private func setUpRemoteCommands() {
        let c = MPRemoteCommandCenter.shared()
        c.playCommand.removeTarget(nil); c.pauseCommand.removeTarget(nil)
        c.skipForwardCommand.removeTarget(nil); c.skipBackwardCommand.removeTarget(nil); c.changePlaybackPositionCommand.removeTarget(nil)
        c.playCommand.addTarget { [weak self] _ in MainActor.assumeIsolated { if self?.isPlaying == false { self?.toggle() } }; return .success }
        c.pauseCommand.addTarget { [weak self] _ in MainActor.assumeIsolated { if self?.isPlaying == true { self?.toggle() } }; return .success }
        c.skipForwardCommand.preferredIntervals = [30]
        c.skipBackwardCommand.preferredIntervals = [15]
        c.skipForwardCommand.addTarget { [weak self] _ in MainActor.assumeIsolated { self?.skip(30) }; return .success }
        c.skipBackwardCommand.addTarget { [weak self] _ in MainActor.assumeIsolated { self?.skip(-15) }; return .success }
        c.changePlaybackPositionCommand.addTarget { [weak self] event in
            guard let e = event as? MPChangePlaybackPositionCommandEvent else { return .commandFailed }
            MainActor.assumeIsolated { self?.seek(to: e.positionTime) }
            return .success
        }
    }
}
