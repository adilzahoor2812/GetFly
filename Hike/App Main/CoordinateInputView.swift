//
//  CoordinateInputView.swift
//  GetFly
//

import CoreLocation
import SwiftUI

struct CoordinateInputView: View {
    @Binding var coordinate: Coordinate3D
    let homeCoordinate: CLLocationCoordinate2D

    var body: some View {
        GetFlyCard {
            VStack(alignment: .leading, spacing: 16) {
                GetFlySectionHeader(
                    "Target Coordinates",
                    subtitle: "Relative to home point in meters",
                    icon: "scope"
                )

                axisField(
                    title: "East (X)",
                    subtitle: "Positive = east",
                    icon: "arrow.left.and.right",
                    value: $coordinate.x,
                    range: -500...500
                )
                axisField(
                    title: "North (Y)",
                    subtitle: "Positive = north",
                    icon: "arrow.up",
                    value: $coordinate.y,
                    range: -500...500
                )
                axisField(
                    title: "Altitude (Z)",
                    subtitle: "Height above ground",
                    icon: "arrow.up.and.down",
                    value: $coordinate.z,
                    range: 0.5...120
                )

                VStack(alignment: .leading, spacing: 6) {
                    Label("Local", systemImage: "ruler")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(.secondary)
                    Text(coordinate.formatted)
                        .font(.subheadline.monospacedDigit())
                    Text(coordinate.geoFormatted(home: homeCoordinate))
                        .font(.caption.monospacedDigit())
                        .foregroundStyle(.secondary)
                }
                .padding(12)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color(.tertiarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 12))
            }
        }
    }

    private func axisField(
        title: String,
        subtitle: String,
        icon: String,
        value: Binding<Double>,
        range: ClosedRange<Double>
    ) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 10) {
                Image(systemName: icon)
                    .foregroundStyle(GetFlyTheme.accent)
                    .frame(width: 28)
                VStack(alignment: .leading, spacing: 2) {
                    Text(title)
                        .font(.subheadline.weight(.semibold))
                    Text(subtitle)
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
                Spacer()
                Text(String(format: "%.1f m", value.wrappedValue))
                    .font(.headline.monospacedDigit())
                    .foregroundStyle(GetFlyTheme.accent)
            }

            HStack(spacing: 12) {
                stepButton(systemName: "minus") {
                    value.wrappedValue = max(range.lowerBound, value.wrappedValue - 0.5)
                }
                Slider(value: value, in: range, step: 0.1)
                    .tint(GetFlyTheme.accent)
                stepButton(systemName: "plus") {
                    value.wrappedValue = min(range.upperBound, value.wrappedValue + 0.5)
                }
            }
        }
        .padding(12)
        .background(Color(.tertiarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 14))
    }

    private func stepButton(systemName: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Image(systemName: systemName)
                .font(.body.weight(.bold))
                .frame(width: 36, height: 36)
                .background(GetFlyTheme.accent.opacity(0.12), in: Circle())
                .foregroundStyle(GetFlyTheme.accent)
        }
        .buttonStyle(.plain)
    }
}

#Preview {
    CoordinateInputView(
        coordinate: .constant(Coordinate3D(x: 1, y: 2, z: 1.5)),
        homeCoordinate: CLLocationCoordinate2D(latitude: 33.6844, longitude: 73.0479)
    )
    .padding()
    .getFlyScreenBackground()
}
