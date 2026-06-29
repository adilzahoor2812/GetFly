//
//  WaypointMissionView.swift
//  Hike
//

import SwiftUI

struct WaypointMissionView: View {
    @ObservedObject var viewModel: DroneViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Mission Waypoints")
                    .font(.headline)
                Spacer()
                Button("Add Current Target") {
                    viewModel.addWaypoint()
                }
                .buttonStyle(.bordered)
            }

            if viewModel.waypoints.isEmpty {
                ContentUnavailableView(
                    "No Waypoints",
                    systemImage: "mappin.and.ellipse",
                    description: Text("Tap the map or use Add Current Target to build a flight path.")
                )
                .frame(minHeight: 140)
            } else {
                List {
                    ForEach(Array(viewModel.waypoints.enumerated()), id: \.element.id) { index, waypoint in
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Waypoint \(index + 1)")
                                .font(.subheadline.bold())
                            Text(waypoint.coordinate.formatted)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                    .onDelete(perform: viewModel.removeWaypoint)
                    .onMove(perform: viewModel.moveWaypoint)
                }
                .listStyle(.plain)
                .frame(minHeight: 160, maxHeight: 220)

                Button {
                    Task { await viewModel.sendMission() }
                } label: {
                    Label("Run Mission", systemImage: "play.fill")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .disabled(viewModel.isBusy || !viewModel.isConnected)
            }
        }
        .padding()
        .background(Color(.secondarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 12))
    }
}

#Preview {
    WaypointMissionView(viewModel: DroneViewModel())
        .padding()
}
