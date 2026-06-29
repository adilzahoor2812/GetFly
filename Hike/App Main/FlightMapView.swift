//
//  FlightMapView.swift
//  Hike
//

import SwiftUI

struct FlightMapView: View {
    let dronePosition: Coordinate3D
    let targetPosition: Coordinate3D
    let waypoints: [Waypoint]
    var onMapTap: ((Coordinate3D) -> Void)?

    private let mapSizeMeters: Double = 10

    var body: some View {
        GeometryReader { geometry in
            let size = min(geometry.size.width, geometry.size.height)
            let scale = size / mapSizeMeters

            ZStack {
                RoundedRectangle(cornerRadius: 16)
                    .fill(Color(.systemGray6))

                gridLines(in: size)

                Path { path in
                    guard let first = waypoints.first else { return }
                    path.move(to: point(for: first.coordinate, scale: scale, in: size))
                    for waypoint in waypoints.dropFirst() {
                        path.addLine(to: point(for: waypoint.coordinate, scale: scale, in: size))
                    }
                }
                .stroke(Color.blue.opacity(0.5), style: StrokeStyle(lineWidth: 2, dash: [6, 4]))

                ForEach(Array(waypoints.enumerated()), id: \.element.id) { index, waypoint in
                    mapMarker(
                        at: point(for: waypoint.coordinate, scale: scale, in: size),
                        color: .blue,
                        label: "\(index + 1)"
                    )
                }

                mapMarker(
                    at: point(for: targetPosition, scale: scale, in: size),
                    color: .orange,
                    label: "T"
                )

                mapMarker(
                    at: point(for: dronePosition, scale: scale, in: size),
                    color: .green,
                    label: "D"
                )

                VStack {
                    HStack {
                        legendItem(color: .green, text: "Drone")
                        legendItem(color: .orange, text: "Target")
                        legendItem(color: .blue, text: "Waypoints")
                    }
                    .font(.caption2)
                    .padding(8)
                    .background(.ultraThinMaterial, in: Capsule())
                    Spacer()
                }
                .padding(8)
            }
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .stroke(Color.secondary.opacity(0.2), lineWidth: 1)
            )
            .contentShape(Rectangle())
            .gesture(
                DragGesture(minimumDistance: 0)
                    .onEnded { value in
                        let coordinate = coordinate(
                            from: value.location,
                            scale: scale,
                            in: size
                        )
                        onMapTap?(coordinate)
                    }
            )
        }
        .aspectRatio(1, contentMode: .fit)
    }

    private func gridLines(in size: CGFloat) -> some View {
        Canvas { context, canvasSize in
            let step = canvasSize.width / 5
            var path = Path()
            for index in 0...5 {
                let offset = CGFloat(index) * step
                path.move(to: CGPoint(x: offset, y: 0))
                path.addLine(to: CGPoint(x: offset, y: canvasSize.height))
                path.move(to: CGPoint(x: 0, y: offset))
                path.addLine(to: CGPoint(x: canvasSize.width, y: offset))
            }
            context.stroke(path, with: .color(.secondary.opacity(0.15)), lineWidth: 1)
        }
    }

    private func mapMarker(at point: CGPoint, color: Color, label: String) -> some View {
        ZStack {
            Circle()
                .fill(color)
                .frame(width: 22, height: 22)
            Text(label)
                .font(.caption2.bold())
                .foregroundStyle(.white)
        }
        .position(point)
    }

    private func legendItem(color: Color, text: String) -> some View {
        HStack(spacing: 4) {
            Circle().fill(color).frame(width: 8, height: 8)
            Text(text)
        }
    }

    private func point(for coordinate: Coordinate3D, scale: CGFloat, in size: CGFloat) -> CGPoint {
        let center = size / 2
        let x = center + CGFloat(coordinate.x) * scale
        let y = center - CGFloat(coordinate.y) * scale
        return CGPoint(x: x, y: y)
    }

    private func coordinate(from point: CGPoint, scale: CGFloat, in size: CGFloat) -> Coordinate3D {
        let center = size / 2
        let x = Double((point.x - center) / scale)
        let y = Double((center - point.y) / scale)
        return Coordinate3D(x: snapped(x), y: snapped(y), z: targetPosition.z)
    }

    private func snapped(_ value: Double) -> Double {
        (value * 10).rounded() / 10
    }
}

#Preview {
    FlightMapView(
        dronePosition: Coordinate3D(x: 0, y: 0, z: 1),
        targetPosition: Coordinate3D(x: 2, y: 1.5, z: 1.5),
        waypoints: [
            Waypoint(coordinate: Coordinate3D(x: 1, y: 0, z: 1.5)),
            Waypoint(coordinate: Coordinate3D(x: 2, y: 1.5, z: 1.5))
        ]
    )
    .padding()
}
