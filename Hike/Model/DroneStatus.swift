//
//  DroneStatus.swift
//  Hike
//

import Foundation

enum FlightMode: String, Codable {
    case idle
    case armed
    case flying
    case landing
    case mission
    case error

    var displayName: String {
        rawValue.capitalized
    }
}

struct DroneStatus: Codable, Equatable {
    var armed: Bool
    var flying: Bool
    var x: Double
    var y: Double
    var z: Double
    var batteryPercent: Int
    var mode: FlightMode
    var message: String?

    enum CodingKeys: String, CodingKey {
        case armed, flying, x, y, z, mode, message
        case batteryPercent = "battery"
    }

    static let disconnected = DroneStatus(
        armed: false,
        flying: false,
        x: 0,
        y: 0,
        z: 0,
        batteryPercent: 0,
        mode: .idle,
        message: "Not connected"
    )

    var position: Coordinate3D {
        Coordinate3D(x: x, y: y, z: z)
    }
}
