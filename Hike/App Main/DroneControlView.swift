//
//  DroneControlView.swift
//  Hike
//

import SwiftUI

struct DroneControlView: View {
    @StateObject private var viewModel = DroneViewModel()
    @State private var showSettings = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    statusCard
                    FlightMapView(
                        homeCoordinate: viewModel.settings.homeCoordinate,
                        dronePosition: viewModel.status.position,
                        targetPosition: viewModel.targetCoordinate,
                        waypoints: viewModel.waypoints
                    ) { coordinate in
                        viewModel.targetCoordinate = coordinate
                    }
                    CoordinateInputView(
                        coordinate: $viewModel.targetCoordinate,
                        homeCoordinate: viewModel.settings.homeCoordinate
                    )
                    flightControls
                    WaypointMissionView(viewModel: viewModel)
                }
                .padding()
            }
            .background(Color(.systemGroupedBackground))
            .navigationTitle("Quadcopter Control")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        showSettings = true
                    } label: {
                        Image(systemName: "gearshape.fill")
                    }
                }
                ToolbarItem(placement: .topBarLeading) {
                    connectionBadge
                }
            }
            .sheet(isPresented: $showSettings) {
                ConnectionSettingsView(settings: viewModel.settings, viewModel: viewModel)
            }
            .onAppear {
                viewModel.startPolling()
            }
            .onDisappear {
                viewModel.stopPolling()
            }
            .overlay(alignment: .bottom) {
                if let message = viewModel.lastSuccessMessage {
                    toast(message, color: .green)
                } else if let error = viewModel.lastError {
                    toast(error, color: .red)
                }
            }
        }
    }

    private var statusCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Label(viewModel.status.mode.displayName, systemImage: "airplane")
                    .font(.headline)
                Spacer()
                if viewModel.isBusy {
                    ProgressView()
                }
            }

            HStack {
                statusPill(
                    title: viewModel.status.armed ? "Armed" : "Disarmed",
                    color: viewModel.status.armed ? .orange : .gray
                )
                statusPill(
                    title: viewModel.status.flying ? "Flying" : "Ground",
                    color: viewModel.status.flying ? .green : .gray
                )
                statusPill(
                    title: "\(viewModel.status.batteryPercent)%",
                    color: batteryColor(viewModel.status.batteryPercent)
                )
            }

            Text("Position: \(viewModel.status.position.formatted)")
                .font(.caption)
                .foregroundStyle(.secondary)

            if let connectionError = viewModel.connectionError {
                Text(connectionError)
                    .font(.caption)
                    .foregroundStyle(.red)
            }
        }
        .padding()
        .background(Color(.secondarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 12))
    }

    private var flightControls: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Flight Controls")
                .font(.headline)

            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 10) {
                controlButton(.arm, prominent: false)
                controlButton(.disarm, prominent: false)
                controlButton(.takeoff, prominent: true)
                controlButton(.land, prominent: true)
                controlButton(.hover, prominent: false)
                controlButton(.home, prominent: false)
            }

            Button {
                Task { await viewModel.sendGoto() }
            } label: {
                Label("Go To Target Coordinates", systemImage: "location.fill")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .disabled(viewModel.isBusy || !viewModel.isConnected)

            Button(role: .destructive) {
                Task { await viewModel.sendAction(.emergencyStop) }
            } label: {
                Label("Emergency Stop", systemImage: "exclamationmark.octagon.fill")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.bordered)
            .disabled(viewModel.isBusy || !viewModel.isConnected)
        }
        .padding()
        .background(Color(.secondarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 12))
    }

    private var connectionBadge: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(viewModel.isConnected ? Color.green : Color.red)
                .frame(width: 8, height: 8)
            Text(viewModel.isConnected ? "Online" : "Offline")
                .font(.caption.bold())
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 4)
        .background(.ultraThinMaterial, in: Capsule())
    }

    @ViewBuilder
    private func controlButton(_ action: DroneAction, prominent: Bool) -> some View {
        if prominent {
            Button {
                Task { await viewModel.sendAction(action) }
            } label: {
                Label(action.displayName, systemImage: action.iconName)
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .disabled(viewModel.isBusy || !viewModel.isConnected)
        } else {
            Button {
                Task { await viewModel.sendAction(action) }
            } label: {
                Label(action.displayName, systemImage: action.iconName)
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.bordered)
            .disabled(viewModel.isBusy || !viewModel.isConnected)
        }
    }

    private func statusPill(title: String, color: Color) -> some View {
        Text(title)
            .font(.caption.bold())
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(color.opacity(0.15), in: Capsule())
            .foregroundStyle(color)
    }

    private func batteryColor(_ percent: Int) -> Color {
        switch percent {
        case 0..<20: return .red
        case 20..<50: return .orange
        default: return .green
        }
    }

    private func toast(_ message: String, color: Color) -> some View {
        Text(message)
            .font(.caption)
            .foregroundStyle(.white)
            .padding(.horizontal, 14)
            .padding(.vertical, 10)
            .background(color.opacity(0.9), in: Capsule())
            .padding(.bottom, 12)
            .transition(.move(edge: .bottom).combined(with: .opacity))
    }
}

#Preview {
    DroneControlView()
}
