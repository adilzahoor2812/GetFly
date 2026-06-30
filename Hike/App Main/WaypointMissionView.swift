//
//  WaypointMissionView.swift
//  GetFly
//

import SwiftUI

struct WaypointMissionView: View {
    @ObservedObject var viewModel: DroneViewModel

    var body: some View {
        GetFlyCard {
            VStack(alignment: .leading, spacing: 16) {
                HStack {
                    Text("\(viewModel.waypoints.count) waypoint\(viewModel.waypoints.count == 1 ? "" : "s")")
                        .font(.subheadline.weight(.medium))
                        .foregroundStyle(.secondary)
                    Spacer()
                    Button {
                        viewModel.addWaypoint()
                    } label: {
                        Label("Add Target", systemImage: "plus.circle.fill")
                            .font(.subheadline.weight(.semibold))
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(GetFlyTheme.accent)
                }

                if viewModel.waypoints.isEmpty {
                    ContentUnavailableView {
                        Label("No Waypoints Yet", systemImage: "mappin.and.ellipse")
                    } description: {
                        Text("Tap the map on the Navigate tab or add your current target to build a mission route.")
                    } actions: {
                        Button("Add Current Target") {
                            viewModel.addWaypoint()
                        }
                        .buttonStyle(.bordered)
                    }
                    .frame(minHeight: 180)
                } else {
                    VStack(spacing: 10) {
                        ForEach(Array(viewModel.waypoints.enumerated()), id: \.element.id) { index, waypoint in
                            waypointRow(index: index, waypoint: waypoint)
                        }
                    }

                    GetFlyActionButton(
                        title: "Run Mission",
                        icon: "play.fill",
                        style: .primary,
                        isDisabled: viewModel.isBusy || !viewModel.isConnected
                    ) {
                        Task { await viewModel.sendMission() }
                    }
                }
            }
        }
    }

    private func waypointRow(index: Int, waypoint: Waypoint) -> some View {
        HStack(spacing: 14) {
            Text("\(index + 1)")
                .font(.headline.bold())
                .foregroundStyle(.white)
                .frame(width: 34, height: 34)
                .background(GetFlyTheme.accent.gradient, in: Circle())

            VStack(alignment: .leading, spacing: 4) {
                Text("Waypoint \(index + 1)")
                    .font(.subheadline.weight(.semibold))
                Text(waypoint.coordinate.formatted)
                    .font(.caption.monospacedDigit())
                    .foregroundStyle(.secondary)
            }

            Spacer()

            Button(role: .destructive) {
                if let idx = viewModel.waypoints.firstIndex(where: { $0.id == waypoint.id }) {
                    viewModel.removeWaypoint(at: IndexSet(integer: idx))
                }
            } label: {
                Image(systemName: "trash")
                    .foregroundStyle(GetFlyTheme.danger)
            }
            .buttonStyle(.plain)
        }
        .padding(12)
        .background(Color(.tertiarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 14))
    }
}

#Preview {
    WaypointMissionView(viewModel: DroneViewModel())
        .padding()
        .getFlyScreenBackground()
}
