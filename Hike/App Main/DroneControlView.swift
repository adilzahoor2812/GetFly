//
//  DroneControlView.swift
//  GetFly
//

import SwiftUI

private enum GetFlyTab: String, CaseIterable {
    case dashboard = "Dashboard"
    case navigate = "Navigate"
    case mission = "Mission"
    case controls = "Controls"

    var icon: String {
        switch self {
        case .dashboard: return "gauge.with.dots.needle.67percent"
        case .navigate: return "map.fill"
        case .mission: return "point.topleft.down.curvedto.point.bottomright.up"
        case .controls: return "slider.horizontal.3"
        }
    }
}

struct DroneControlView: View {
    @StateObject private var viewModel = DroneViewModel()
    @State private var showSettings = false
    @State private var selectedTab: GetFlyTab = .dashboard

    var body: some View {
        TabView(selection: $selectedTab) {
            dashboardTab
                .tabItem { Label(GetFlyTab.dashboard.rawValue, systemImage: GetFlyTab.dashboard.icon) }
                .tag(GetFlyTab.dashboard)

            navigateTab
                .tabItem { Label(GetFlyTab.navigate.rawValue, systemImage: GetFlyTab.navigate.icon) }
                .tag(GetFlyTab.navigate)

            missionTab
                .tabItem { Label(GetFlyTab.mission.rawValue, systemImage: GetFlyTab.mission.icon) }
                .tag(GetFlyTab.mission)

            controlsTab
                .tabItem { Label(GetFlyTab.controls.rawValue, systemImage: GetFlyTab.controls.icon) }
                .tag(GetFlyTab.controls)
        }
        .tint(GetFlyTheme.accent)
        .getFlyScreenBackground()
        .sheet(isPresented: $showSettings) {
            ConnectionSettingsView(settings: viewModel.settings, viewModel: viewModel)
        }
        .overlay(alignment: .bottom) {
            toastOverlay
        }
        .onAppear { viewModel.startPolling() }
        .onDisappear { viewModel.stopPolling() }
    }

    // MARK: - Dashboard

    private var dashboardTab: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    heroHeader
                    GetFlyConnectionBanner(
                        isConnected: viewModel.isConnected,
                        error: viewModel.connectionError
                    )
                    telemetryGrid
                    mapSection(compact: true)
                }
                .padding(.horizontal, 16)
                .padding(.bottom, 24)
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { settingsToolbar }
        }
    }

    // MARK: - Navigate

    private var navigateTab: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    GetFlySectionHeader(
                        "Flight Path",
                        subtitle: "Tap the map to set your target location",
                        icon: "location.viewfinder"
                    )
                    mapSection(compact: false)
                    CoordinateInputView(
                        coordinate: $viewModel.targetCoordinate,
                        homeCoordinate: viewModel.settings.homeCoordinate
                    )
                    GetFlyActionButton(
                        title: "Go To Target",
                        icon: "paperplane.fill",
                        style: .primary,
                        isDisabled: viewModel.isBusy || !viewModel.isConnected
                    ) {
                        Task { await viewModel.sendGoto() }
                    }
                }
                .padding(.horizontal, 16)
                .padding(.bottom, 24)
            }
            .navigationTitle("Navigate")
            .toolbar { settingsToolbar }
        }
    }

    // MARK: - Mission

    private var missionTab: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    GetFlySectionHeader(
                        "Waypoint Mission",
                        subtitle: "Build a multi-point autonomous route",
                        icon: "arrow.triangle.swap"
                    )
                    WaypointMissionView(viewModel: viewModel)
                }
                .padding(.horizontal, 16)
                .padding(.bottom, 24)
            }
            .navigationTitle("Mission")
            .toolbar { settingsToolbar }
        }
    }

    // MARK: - Controls

    private var controlsTab: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    GetFlySectionHeader(
                        "Flight Controls",
                        subtitle: "Arm motors before takeoff",
                        icon: "airplane.circle.fill"
                    )
                    flightControlsGrid
                    GetFlyActionButton(
                        title: "Emergency Stop",
                        icon: "exclamationmark.octagon.fill",
                        style: .danger,
                        isDisabled: viewModel.isBusy || !viewModel.isConnected
                    ) {
                        Task { await viewModel.sendAction(.emergencyStop) }
                    }
                }
                .padding(.horizontal, 16)
                .padding(.bottom, 24)
            }
            .navigationTitle("Controls")
            .toolbar { settingsToolbar }
        }
    }

    // MARK: - Shared Components

    private var heroHeader: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("GetFly")
                        .font(.largeTitle.bold())
                    Text("Autonomous Quadcopter")
                        .font(.subheadline)
                        .opacity(0.85)
                }
                Spacer()
                if viewModel.isBusy {
                    ProgressView()
                        .tint(.white)
                } else {
                    Image(systemName: "airplane")
                        .font(.title)
                        .symbolEffect(.pulse, isActive: viewModel.status.flying)
                }
            }

            HStack(spacing: 8) {
                statusChip(
                    viewModel.status.mode.displayName,
                    icon: "dot.radiowaves.right",
                    active: viewModel.status.flying
                )
                statusChip(
                    viewModel.status.armed ? "Armed" : "Disarmed",
                    icon: "power",
                    active: viewModel.status.armed
                )
            }
        }
        .foregroundStyle(.white)
        .padding(20)
        .background(GetFlyTheme.heroGradient, in: RoundedRectangle(cornerRadius: GetFlyTheme.cardRadius))
        .shadow(color: GetFlyTheme.accent.opacity(0.25), radius: 16, y: 8)
    }

    private var telemetryGrid: some View {
        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
            GetFlyMetricTile(
                title: "Altitude",
                value: String(format: "%.1f m", viewModel.status.position.z),
                icon: "arrow.up.and.down",
                tint: GetFlyTheme.accent
            )
            GetFlyMetricTile(
                title: "Battery",
                value: "\(viewModel.status.batteryPercent)%",
                icon: "battery.100",
                tint: batteryColor(viewModel.status.batteryPercent)
            )
            GetFlyMetricTile(
                title: "Position X",
                value: String(format: "%.1f m", viewModel.status.position.x),
                icon: "arrow.left.and.right",
                tint: .purple
            )
            GetFlyMetricTile(
                title: "Position Y",
                value: String(format: "%.1f m", viewModel.status.position.y),
                icon: "arrow.up.and.down.circle",
                tint: .teal
            )
        }
    }

    private func mapSection(compact: Bool) -> some View {
        GetFlyCard {
            VStack(alignment: .leading, spacing: 12) {
                if compact {
                    GetFlySectionHeader(
                        "Live Map",
                        subtitle: "OpenStreetMap view",
                        icon: "map"
                    )
                }
                FlightMapView(
                    homeCoordinate: viewModel.settings.homeCoordinate,
                    dronePosition: viewModel.status.position,
                    targetPosition: viewModel.targetCoordinate,
                    waypoints: viewModel.waypoints
                ) { coordinate in
                    viewModel.targetCoordinate = coordinate
                    selectedTab = .navigate
                }
                .frame(maxHeight: compact ? 260 : nil)
            }
        }
    }

    private var flightControlsGrid: some View {
        GetFlyCard {
            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                flightTile(.arm, primary: false)
                flightTile(.disarm, primary: false)
                flightTile(.takeoff, primary: true)
                flightTile(.land, primary: true)
                flightTile(.hover, primary: false)
                flightTile(.home, primary: false)
            }
        }
    }

    @ToolbarContentBuilder
    private var settingsToolbar: some ToolbarContent {
        ToolbarItem(placement: .topBarTrailing) {
            Button { showSettings = true } label: {
                Image(systemName: "gearshape.fill")
                    .symbolRenderingMode(.hierarchical)
            }
        }
    }

    @ViewBuilder
    private var toastOverlay: some View {
        if let message = viewModel.lastSuccessMessage {
            GetFlyToast(message: message, isSuccess: true)
                .transition(.move(edge: .bottom).combined(with: .opacity))
                .onAppear { scheduleToastClear() }
        } else if let error = viewModel.lastError {
            GetFlyToast(message: error, isSuccess: false)
                .transition(.move(edge: .bottom).combined(with: .opacity))
                .onAppear { scheduleToastClear() }
        }
    }

    private func flightTile(_ action: DroneAction, primary: Bool) -> some View {
        GetFlyFlightControlTile(
            action: action,
            isPrimary: primary,
            isDisabled: viewModel.isBusy || !viewModel.isConnected
        ) {
            Task { await viewModel.sendAction(action) }
        }
    }

    private func statusChip(_ text: String, icon: String, active: Bool) -> some View {
        Label(text, systemImage: icon)
            .font(.caption.weight(.semibold))
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(.white.opacity(active ? 0.25 : 0.12), in: Capsule())
    }

    private func batteryColor(_ percent: Int) -> Color {
        switch percent {
        case 0..<20: return GetFlyTheme.danger
        case 20..<50: return GetFlyTheme.warning
        default: return GetFlyTheme.success
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
