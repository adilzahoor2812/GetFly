//
//  CoordinateConverter.swift
//  Hike
//

import CoreLocation
import Foundation

enum CoordinateConverter {
    private static let metersPerDegreeLatitude = 111_320.0

    static func localToGeo(x: Double, y: Double, home: CLLocationCoordinate2D) -> CLLocationCoordinate2D {
        let metersPerDegreeLongitude = metersPerDegreeLatitude * cos(home.latitude * .pi / 180)
        let latitude = home.latitude + (y / metersPerDegreeLatitude)
        let longitude = home.longitude + (x / metersPerDegreeLongitude)
        return CLLocationCoordinate2D(latitude: latitude, longitude: longitude)
    }

    static func geoToLocal(_ coordinate: CLLocationCoordinate2D, home: CLLocationCoordinate2D) -> (x: Double, y: Double) {
        let metersPerDegreeLongitude = metersPerDegreeLatitude * cos(home.latitude * .pi / 180)
        let y = (coordinate.latitude - home.latitude) * metersPerDegreeLatitude
        let x = (coordinate.longitude - home.longitude) * metersPerDegreeLongitude
        return (snap(x), snap(y))
    }

    static func coordinate(_ local: Coordinate3D, home: CLLocationCoordinate2D) -> CLLocationCoordinate2D {
        localToGeo(x: local.x, y: local.y, home: home)
    }

    static func localCoordinate(
        from geo: CLLocationCoordinate2D,
        home: CLLocationCoordinate2D,
        altitude: Double
    ) -> Coordinate3D {
        let local = geoToLocal(geo, home: home)
        return Coordinate3D(x: local.x, y: local.y, z: altitude)
    }

    private static func snap(_ value: Double) -> Double {
        (value * 10).rounded() / 10
    }
}
