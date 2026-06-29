//
//  DroneConnectionSettings.swift
//  Hike
//

import Foundation

@MainActor
final class DroneConnectionSettings: ObservableObject {
    @Published var hostAddress: String {
        didSet { UserDefaults.standard.set(hostAddress, forKey: Keys.hostAddress) }
    }

    @Published var port: Int {
        didSet { UserDefaults.standard.set(port, forKey: Keys.port) }
    }

    @Published var pollIntervalSeconds: Double {
        didSet { UserDefaults.standard.set(pollIntervalSeconds, forKey: Keys.pollInterval) }
    }

    var baseURL: URL? {
        URL(string: "http://\(hostAddress):\(port)")
    }

    init() {
        hostAddress = UserDefaults.standard.string(forKey: Keys.hostAddress) ?? "192.168.4.1"
        port = UserDefaults.standard.object(forKey: Keys.port) as? Int ?? 80
        pollIntervalSeconds = UserDefaults.standard.object(forKey: Keys.pollInterval) as? Double ?? 1.0
    }

    private enum Keys {
        static let hostAddress = "drone.hostAddress"
        static let port = "drone.port"
        static let pollInterval = "drone.pollInterval"
    }
}
