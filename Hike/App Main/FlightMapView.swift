//
//  FlightMapView.swift
//  GetFly
//

import CoreLocation
import SwiftUI

enum FlightMapLayout {
    case fullScreen
    case embedded

    var height: CGFloat? {
        switch self {
        case .fullScreen: return nil
        case .embedded: return 380
        }
    }
}

struct FlightMapView: View {
    let homeCoordinate: CLLocationCoordinate2D
    let dronePosition: Coordinate3D
    let targetPosition: Coordinate3D
    let waypoints: [Waypoint]
    let flightTrail: [Coordinate3D]
    let isFlying: Bool
    let followDrone: Bool
    let activeWaypointIndex: Int?
    let layout: FlightMapLayout
    var onMapTap: ((Coordinate3D) -> Void)?

    init(
        homeCoordinate: CLLocationCoordinate2D,
        dronePosition: Coordinate3D,
        targetPosition: Coordinate3D,
        waypoints: [Waypoint],
        flightTrail: [Coordinate3D] = [],
        isFlying: Bool = false,
        followDrone: Bool = true,
        activeWaypointIndex: Int? = nil,
        navigationLabel: String = "",
        layout: FlightMapLayout = .fullScreen,
        onMapTap: ((Coordinate3D) -> Void)? = nil
    ) {
        self.homeCoordinate = homeCoordinate
        self.dronePosition = dronePosition
        self.targetPosition = targetPosition
        self.waypoints = waypoints
        self.flightTrail = flightTrail
        self.isFlying = isFlying
        self.followDrone = followDrone
        self.activeWaypointIndex = activeWaypointIndex
        self.layout = layout
        self.onMapTap = onMapTap
    }

    var body: some View {
        OpenStreetMapView(
            homeCoordinate: homeCoordinate,
            dronePosition: dronePosition,
            targetPosition: targetPosition,
            waypoints: waypoints,
            flightTrail: flightTrail,
            isFlying: isFlying,
            followDrone: followDrone,
            activeWaypointIndex: activeWaypointIndex,
            onMapTap: onMapTap
        )
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .frame(height: layout.height)
    }
}
