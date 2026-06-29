//
//  CoordinateInputView.swift
//  Hike
//

import CoreLocation
import SwiftUI

struct CoordinateInputView: View {
    @Binding var coordinate: Coordinate3D
    let homeCoordinate: CLLocationCoordinate2D

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Target Coordinates")
                .font(.headline)

            axisField(title: "X (East)", value: $coordinate.x, range: -500...500)
            axisField(title: "Y (North)", value: $coordinate.y, range: -500...500)
            axisField(title: "Z (Altitude)", value: $coordinate.z, range: 0.5...120)

            Text(coordinate.formatted)
                .font(.caption)
                .foregroundStyle(.secondary)

            Text(coordinate.geoFormatted(home: homeCoordinate))
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding()
        .background(Color(.secondarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 12))
    }

    private func axisField(title: String, value: Binding<Double>, range: ClosedRange<Double>) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(title)
                    .font(.subheadline)
                Spacer()
                Text(String(format: "%.2f m", value.wrappedValue))
                    .font(.subheadline.monospacedDigit())
                    .foregroundStyle(.secondary)
            }
            Slider(value: value, in: range, step: 0.1)
        }
    }
}

#Preview {
    CoordinateInputView(
        coordinate: .constant(Coordinate3D(x: 1, y: 2, z: 1.5)),
        homeCoordinate: CLLocationCoordinate2D(latitude: 33.6844, longitude: 73.0479)
    )
    .padding()
}
