//
//  DroneCommand.swift
//  Hike
//

import Foundation

enum DroneAction: String, Codable, CaseIterable {
    case arm
    case disarm
    case takeoff
    case land
    case hover
    case goto
    case mission
    case emergencyStop = "emergency_stop"
    case home

    var displayName: String {
        switch self {
        case .arm: return "Arm"
        case .disarm: return "Disarm"
        case .takeoff: return "Take Off"
        case .land: return "Land"
        case .hover: return "Hover"
        case .goto: return "Go To"
        case .mission: return "Run Mission"
        case .emergencyStop: return "E-Stop"
        case .home: return "Return Home"
        }
    }

    var iconName: String {
        switch self {
        case .arm: return "power"
        case .disarm: return "power.circle"
        case .takeoff: return "arrow.up.circle.fill"
        case .land: return "arrow.down.circle.fill"
        case .hover: return "pause.circle.fill"
        case .goto: return "location.fill"
        case .mission: return "point.topleft.down.curvedto.point.bottomright.up.fill"
        case .emergencyStop: return "exclamationmark.octagon.fill"
        case .home: return "house.fill"
        }
    }
}

struct DroneCommandPayload: Codable {
    let action: String
    var x: Double?
    var y: Double?
    var z: Double?
    var waypoints: [WaypointPayload]?

    struct WaypointPayload: Codable {
        let x: Double
        let y: Double
        let z: Double
        let holdSeconds: Double

        enum CodingKeys: String, CodingKey {
            case x, y, z
            case holdSeconds = "hold_seconds"
        }
    }

    static func action(_ action: DroneAction) -> DroneCommandPayload {
        DroneCommandPayload(action: action.rawValue, x: nil, y: nil, z: nil, waypoints: nil)
    }

    static func goto(_ coordinate: Coordinate3D) -> DroneCommandPayload {
        DroneCommandPayload(action: DroneAction.goto.rawValue, x: coordinate.x, y: coordinate.y, z: coordinate.z, waypoints: nil)
    }

    static func mission(_ waypoints: [Waypoint]) -> DroneCommandPayload {
        DroneCommandPayload(
            action: DroneAction.mission.rawValue,
            x: nil,
            y: nil,
            z: nil,
            waypoints: waypoints.map {
                WaypointPayload(
                    x: $0.coordinate.x,
                    y: $0.coordinate.y,
                    z: $0.coordinate.z,
                    holdSeconds: $0.holdSeconds
                )
            }
        )
    }
}

struct DroneCommandResponse: Codable {
    let success: Bool
    let message: String?
}
