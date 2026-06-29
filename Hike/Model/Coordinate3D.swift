//
//  Coordinate3D.swift
//  Hike
//

import CoreLocation
import Foundation

struct Coordinate3D: Codable, Hashable, Identifiable {
    var id: UUID
    var x: Double
    var y: Double
    var z: Double

    init(id: UUID = UUID(), x: Double = 0, y: Double = 0, z: Double = 1.0) {
        self.id = id
        self.x = x
        self.y = y
        self.z = z
    }

    var formatted: String {
        String(format: "X: %.2f  Y: %.2f  Z: %.2f m", x, y, z)
    }

    func geoFormatted(home: CLLocationCoordinate2D) -> String {
        let geo = CoordinateConverter.coordinate(self, home: home)
        return String(format: "Lat: %.5f  Lon: %.5f  Alt: %.2f m", geo.latitude, geo.longitude, z)
    }
}
