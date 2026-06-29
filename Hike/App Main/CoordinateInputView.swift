//
//  CoordinateInputView.swift
//  Hike
//

import SwiftUI

struct CoordinateInputView: View {
    @Binding var coordinate: Coordinate3D

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Target Coordinates (meters)")
                .font(.headline)

            axisField(title: "X (Forward)", value: $coordinate.x, range: -5...5)
            axisField(title: "Y (Left/Right)", value: $coordinate.y, range: -5...5)
            axisField(title: "Z (Altitude)", value: $coordinate.z, range: 0.5...5)

            Text(coordinate.formatted)
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
    CoordinateInputView(coordinate: .constant(Coordinate3D(x: 1, y: 2, z: 1.5)))
        .padding()
}
