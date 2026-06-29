//
//  FlightMapView.swift
//  Hike
//

import CoreLocation
import SwiftUI

struct FlightMapView: View {
    let homeCoordinate: CLLocationCoordinate2D
    let dronePosition: Coordinate3D
    let targetPosition: Coordinate3D
    let waypoints: [Waypoint]
    var onMapTap: ((Coordinate3D) -> Void)?

    var body: some View {
        ZStack(alignment: .topLeading) {
            OpenStreetMapView(
                homeCoordinate: homeCoordinate,
                dronePosition: dronePosition,
                targetPosition: targetPosition,
                waypoints: waypoints,
                onMapTap: onMapTap
            )
            .clipShape(RoundedRectangle(cornerRadius: 16))
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .stroke(Color.secondary.opacity(0.2), lineWidth: 1)
            )

            VStack(alignment: .leading, spacing: 8) {
                HStack(spacing: 8) {
                    legendItem(color: .green, text: "Drone")
                    legendItem(color: .orange, text: "Target")
                    legendItem(color: .blue, text: "Waypoints")
                }
                .font(.caption2)
                .padding(8)
                .background(.ultraThinMaterial, in: Capsule())

                Spacer()

                Text("© OpenStreetMap contributors")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(.ultraThinMaterial, in: Capsule())
            }
            .padding(8)
        }
        .aspectRatio(1, contentMode: .fit)
    }

    private func legendItem(color: Color, text: String) -> some View {
        HStack(spacing: 4) {
            Circle().fill(color).frame(width: 8, height: 8)
            Text(text)
        }
    }
}

#Preview {
    FlightMapView(
        homeCoordinate: CLLocationCoordinate2D(latitude: 33.6844, longitude: 73.0479),
        dronePosition: Coordinate3D(x: 0, y: 0, z: 1),
        targetPosition: Coordinate3D(x: 2, y: 1.5, z: 1.5),
        waypoints: [
            Waypoint(coordinate: Coordinate3D(x: 1, y: 0, z: 1.5)),
            Waypoint(coordinate: Coordinate3D(x: 2, y: 1.5, z: 1.5))
        ]
    )
    .padding()
}
