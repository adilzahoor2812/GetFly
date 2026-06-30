//
//  DroneControlView.swift
//  GetFly
//

import SwiftUI

struct DroneControlView: View {
    @StateObject private var viewModel = DroneViewModel()
    @State private var showSettings = false
    @State private var panelMode: MissionPanelMode = .plan
    @State private var panelDetent: PanelDetent = .medium
    @State private var mapPulse = false

    var body: some View {
        GeometryReader { geo in
            ZStack {
                // Full-screen map
                FlightMapView(
                    homeCoordinate: viewModel.settings.homeCoordinate,
                    dronePosition: viewModel.displayPosition,
                    targetPosition: viewModel.targetCoordinate,
                    waypoints: viewModel.waypoints,
                    flightTrail: viewModel.flightTrail,
                    isFlying: viewModel.isFlying,
                    followDrone: true,
                    activeWaypointIndex: viewModel.activeWaypointIndex,
                    layout: .fullScreen
                ) { coordinate in
                    withAnimation(.spring(response: 0.4, dampingFraction: 0.75)) {
                        viewModel.targetCoordinate = coordinate
                        viewModel.addWaypoint(from: coordinate)
                        panelMode = .plan
                        panelDetent = .medium
                    }
                }
                .ignoresSafeArea()

                // Cinematic vignette
                GetFlyTheme.mapVignette
                    .ignoresSafeArea()
                    .allowsHitTesting(false)

                // Top HUD
                VStack(spacing: 10) {
                    topBar
                    DroneHUDView(
                        altitude: viewModel.displayPosition.z,
                        battery: viewModel.status.batteryPercent,
                        isConnected: viewModel.isConnected,
                        isFlying: viewModel.isFlying,
                        mode: viewModel.status.mode.displayName,
                        navigationLabel: viewModel.navigationLabel
                    )
                    .padding(.horizontal, 14)

                    if viewModel.isNavigating, !viewModel.waypoints.isEmpty {
                        MissionProgressRing(
                            progress: missionProgress,
                            label: viewModel.navigationLabel
                        )
                        .padding(.horizontal, 14)
                        .transition(.asymmetric(
                            insertion: .move(edge: .top).combined(with: .opacity),
                            removal: .opacity
                        ))
                    }

                    Spacer()
                }
                .padding(.top, 8)

                // Side FABs
                HStack {
                    VStack(spacing: 12) {
                        DroneFAB(icon: "gearshape.fill", tint: GetFlyTheme.surfaceElevated) {
                            showSettings = true
                        }
                        DroneFAB(icon: "plus.viewfinder", tint: GetFlyTheme.accent) {
                            viewModel.addWaypoint()
                            panelMode = .plan
                            withAnimation { panelDetent = .medium }
                        }
                        DroneFAB(icon: "location.fill", tint: GetFlyTheme.success) {
                            Task { await viewModel.sendGoto() }
                            panelMode = .target
                        }
                    }
                    .padding(.leading, 14)
                    .padding(.top, geo.size.height * 0.32)

                    Spacer()
                }

                // Map tap hint
                if viewModel.waypoints.isEmpty && !viewModel.isFlying {
                    VStack {
                        Spacer()
                        Label("Tap map to plan mission", systemImage: "hand.tap.fill")
                            .font(.caption.weight(.semibold))
                            .foregroundStyle(.white)
                            .padding(.horizontal, 14)
                            .padding(.vertical, 8)
                            .glassPanel(cornerRadius: 999)
                            .opacity(mapPulse ? 1 : 0.55)
                            .padding(.bottom, geo.size.height * panelDetent.rawValue + 20)
                    }
                    .allowsHitTesting(false)
                }

                // Bottom mission panel
                MissionPlanningPanel(
                    viewModel: viewModel,
                    panelMode: $panelMode,
                    detent: $panelDetent
                )
            }
        }
        .getFlyProBackground()
        .preferredColorScheme(.dark)
        .sheet(isPresented: $showSettings) {
            ConnectionSettingsView(settings: viewModel.settings, viewModel: viewModel)
                .preferredColorScheme(.dark)
        }
        .overlay(alignment: .bottom) { toastOverlay }
        .onAppear {
            viewModel.startPolling()
            withAnimation(.easeInOut(duration: 1.4).repeatForever(autoreverses: true)) {
                mapPulse = true
            }
        }
        .onDisappear { viewModel.stopPolling() }
        .onChange(of: viewModel.isNavigating) { _, navigating in
            if navigating {
                withAnimation(.spring(response: 0.45, dampingFraction: 0.8)) {
                    panelMode = .plan
                    panelDetent = .medium
                }
            }
        }
        .animation(.spring(response: 0.45, dampingFraction: 0.82), value: viewModel.isNavigating)
    }

    private var topBar: some View {
        HStack {
            HStack(spacing: 8) {
                Image(systemName: "airplane.circle.fill")
                    .font(.title2)
                    .foregroundStyle(GetFlyTheme.accent)
                    .symbolEffect(.pulse, isActive: viewModel.isFlying)
                VStack(alignment: .leading, spacing: 0) {
                    Text("GetFly")
                        .font(.system(size: 18, weight: .heavy, design: .rounded))
                        .foregroundStyle(.white)
                    Text("Mission Planner")
                        .font(.system(size: 10, weight: .semibold, design: .monospaced))
                        .foregroundStyle(GetFlyTheme.textSecondary)
                }
            }
            Spacer()
            if viewModel.isBusy {
                ProgressView()
                    .tint(GetFlyTheme.accent)
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
    }

    private var missionProgress: Double {
        let total = max(viewModel.waypoints.count, 1)
        let completed = min(viewModel.activeWaypointIndex ?? 0, total)
        return Double(completed) / Double(total)
    }

    @ViewBuilder
    private var toastOverlay: some View {
        if let message = viewModel.lastSuccessMessage {
            GetFlyToast(message: message, isSuccess: true)
                .padding(.bottom, 120)
                .transition(.move(edge: .bottom).combined(with: .opacity))
                .onAppear { scheduleToastClear() }
        } else if let error = viewModel.lastError {
            GetFlyToast(message: error, isSuccess: false)
                .padding(.bottom, 120)
                .transition(.move(edge: .bottom).combined(with: .opacity))
                .onAppear { scheduleToastClear() }
        }
    }

    private func scheduleToastClear() {
        Task {
            try? await Task.sleep(for: .seconds(3))
            viewModel.lastSuccessMessage = nil
            viewModel.lastError = nil
        }
    }
}

#Preview {
    DroneControlView()
}
