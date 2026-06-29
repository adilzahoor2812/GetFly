//
//  DroneConnectionSettings.swift
//  Hike
//

import CoreLocation
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

    @Published var homeLatitude: Double {
        didSet { UserDefaults.standard.set(homeLatitude, forKey: Keys.homeLatitude) }
    }

    @Published var homeLongitude: Double {
        didSet { UserDefaults.standard.set(homeLongitude, forKey: Keys.homeLongitude) }
    }

    var baseURL: URL? {
        URL(string: "http://\(hostAddress):\(port)")
    }

    var homeCoordinate: CLLocationCoordinate2D {
        CLLocationCoordinate2D(latitude: homeLatitude, longitude: homeLongitude)
    }

    func setHome(to coordinate: CLLocationCoordinate2D) {
        homeLatitude = coordinate.latitude
        homeLongitude = coordinate.longitude
    }

    init() {
        hostAddress = UserDefaults.standard.string(forKey: Keys.hostAddress) ?? "192.168.4.1"
        port = UserDefaults.standard.object(forKey: Keys.port) as? Int ?? 80
        pollIntervalSeconds = UserDefaults.standard.object(forKey: Keys.pollInterval) as? Double ?? 1.0

        if UserDefaults.standard.object(forKey: Keys.homeLatitude) != nil {
            homeLatitude = UserDefaults.standard.double(forKey: Keys.homeLatitude)
            homeLongitude = UserDefaults.standard.double(forKey: Keys.homeLongitude)
        } else {
            homeLatitude = 33.6844
            homeLongitude = 73.0479
        }
    }

    private enum Keys {
        static let hostAddress = "drone.hostAddress"
        static let port = "drone.port"
        static let pollInterval = "drone.pollInterval"
        static let homeLatitude = "drone.homeLatitude"
        static let homeLongitude = "drone.homeLongitude"
    }
}
