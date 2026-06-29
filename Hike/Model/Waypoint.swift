//
//  Waypoint.swift
//  Hike
//

import Foundation

struct Waypoint: Codable, Hashable, Identifiable {
    var id: UUID
    var coordinate: Coordinate3D
    var holdSeconds: Double

    init(id: UUID = UUID(), coordinate: Coordinate3D, holdSeconds: Double = 2.0) {
        self.id = id
        self.coordinate = coordinate
        self.holdSeconds = holdSeconds
    }
}
