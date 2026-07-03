//
//  MissionPlanningPanel.swift
//  GetFly
//

import CoreLocation
import SwiftUI

enum PanelDetent: CGFloat, CaseIterable {
    case collapsed = 0.28
    case medium = 0.52
    case expanded = 0.78
}

struct MissionPlanningPanel: View {
    @ObservedObject var viewModel: DroneViewModel
    @Binding var panelMode: MissionPanelMode
    @Binding var detent: PanelDetent
    @State private var dragOffset: CGFloat = 0

    var body: some View {
        GeometryReader { geo in
            let panelHeight = geo.size.height * detent.rawValue - dragOffset

            VStack(spacing: 0) {
                Spacer(minLength: 0)

                VStack(spacing: 14) {
                    dragHandle

                    MissionModeSelector(selection: $panelMode)

                    ScrollView(showsIndicators: false) {
                        VStack(spacing: 16) {
                            switch panelMode {
                            case .plan:
                                planContent
                            case .target:
                                targetContent
                            case .fly:
                                flyContent
                            }
                        }
                        .padding(.bottom, 24)
                    }
                }
                .padding(.horizontal, 16)
                .padding(.top, 10)
                .frame(height: max(panelHeight, geo.size.height * PanelDetent.collapsed.rawValue))
                .frame(maxWidth: .infinity)
                .background(
                    GetFlyTheme.panelBackground
                        .overlay(
                            LinearGradient(
                                colors: [GetFlyTheme.accent.opacity(0.08), .clear],
                                startPoint: .top,
                                endPoint: .bottom
                            )
                        )
                )
                .clipShape(RoundedRectangle(cornerRadius: GetFlyTheme.panelRadius, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: GetFlyTheme.panelRadius, style: .continuous)
                        .stroke(Color.white.opacity(0.08), lineWidth: 1)
                )
                .shadow(color: .black.opacity(0.45), radius: 24, y: -8)
                .gesture(panelDrag(in: geo))
                .animation(.spring(response: 0.42, dampingFraction: 0.82), value: detent)
            }
        }
    }

    private var dragHandle: some View {
        Capsule()
            .fill(Color.white.opacity(0.28))
            .frame(width: 40, height: 5)
            .padding(.top, 4)
    }

    // MARK: Plan

    private var planContent: some View {
        VStack(spacing: 14) {
            WaypointStripView(
                waypoints: viewModel.waypoints,
                activeIndex: viewModel.activeWaypointIndex,
                onAdd: { viewModel.addWaypoint() },
                onRemove: { viewModel.removeWaypoint(at: IndexSet(integer: $0)) }
            )

            if viewModel.waypoints.isEmpty {
                VStack(spacing: 8) {
                    Image(systemName: "hand.tap.fill")
                        .font(.title2)
                        .foregroundStyle(GetFlyTheme.accent)
                        .symbolEffect(.bounce, options: .repeating)
                    Text("Tap the map to add waypoints")
                        .font(.subheadline.weight(.medium))
                        .foregroundStyle(GetFlyTheme.textSecondary)
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 20)
            }

            FlyMissionButton(
                title: viewModel.isNavigating ? "Mission In Progress…" : "Execute Mission",
                icon: viewModel.isNavigating ? "airplane" : "play.fill",
                isDisabled: viewModel.waypoints.isEmpty || viewModel.isBusy || !viewModel.isConnected || viewModel.isNavigating,
                isRunning: viewModel.isNavigating
            ) {
                Task { await viewModel.sendMission() }
            }
        }
    }

    // MARK: Target

    private var targetContent: some View {
        VStack(spacing: 14) {
            ProCoordinateEditor(
                coordinate: $viewModel.targetCoordinate,
                homeCoordinate: viewModel.settings.homeCoordinate
            )

            FlyMissionButton(
                title: "Go To Target",
                icon: "paperplane.fill",
                isDisabled: viewModel.isBusy || !viewModel.isConnected,
                isRunning: viewModel.isNavigating
            ) {
                Task { await viewModel.sendGoto() }
            }
        }
    }

    // MARK: Fly

    private var flyContent: some View {
        VStack(spacing: 12) {
            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible())], spacing: 10) {
                ForEach(Array(flightActions.enumerated()), id: \.offset) { index, item in
                    ProFlightButton(action: item.action, isPrimary: item.primary, isDisabled: viewModel.isBusy || !viewModel.isConnected) {
                        Task { await viewModel.sendAction(item.action) }
                    }
                    .staggeredAppear(index: index)
                }
            }

            FlyMissionButton(
                title: "Emergency Stop",
                icon: "exclamationmark.octagon.fill",
                isDisabled: viewModel.isBusy || !viewModel.isConnected,
                isRunning: false,
                style: .danger
            ) {
                Task { await viewModel.sendAction(.emergencyStop) }
            }
        }
    }

    private var flightActions: [(action: DroneAction, primary: Bool)] {
        [
            (.arm, false), (.disarm, false), (.takeoff, true),
            (.land, true), (.hover, false), (.home, false)
        ]
    }

    private func panelDrag(in geo: GeometryProxy) -> some Gesture {
        DragGesture()
            .onChanged { value in
                dragOffset = max(0, value.translation.height * 0.35)
            }
            .onEnded { value in
                dragOffset = 0
                let threshold: CGFloat = 50
                if value.translation.height > threshold {
                    detent = detent == .expanded ? .medium : .collapsed
                } else if value.translation.height < -threshold {
                    detent = detent == .collapsed ? .medium : .expanded
                }
            }
    }
}

struct ProCoordinateEditor: View {
    @Binding var coordinate: Coordinate3D
    let homeCoordinate: CLLocationCoordinate2D

    var body: some View {
        VStack(spacing: 12) {
            proAxis("EAST (X)", icon: "arrow.left.and.right", value: $coordinate.x, range: -500...500)
            proAxis("NORTH (Y)", icon: "arrow.up", value: $coordinate.y, range: -500...500)
            proAxis("ALTITUDE", icon: "arrow.up.and.down", value: $coordinate.z, range: 0.5...120)

            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(coordinate.formatted)
                        .font(.system(size: 11, weight: .medium, design: .monospaced))
                        .foregroundStyle(GetFlyTheme.textPrimary)
                    Text(coordinate.geoFormatted(home: homeCoordinate))
                        .font(.system(size: 10, weight: .regular, design: .monospaced))
                        .foregroundStyle(GetFlyTheme.textSecondary)
                }
                Spacer()
            }
            .padding(12)
            .background(GetFlyTheme.surface, in: RoundedRectangle(cornerRadius: 12))
        }
        .padding(14)
        .glassPanel()
    }

    private func proAxis(_ title: String, icon: String, value: Binding<Double>, range: ClosedRange<Double>) -> some View {
        VStack(spacing: 8) {
            HStack {
                Image(systemName: icon)
                    .foregroundStyle(GetFlyTheme.accent)
                    .font(.caption)
                Text(title)
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(GetFlyTheme.textSecondary)
                Spacer()
                Text(String(format: "%.1f m", value.wrappedValue))
                    .font(.system(size: 14, weight: .bold, design: .rounded))
                    .foregroundStyle(GetFlyTheme.accent)
            }
            Slider(value: value, in: range, step: 0.1)
                .tint(GetFlyTheme.accent)
        }
    }
}

struct ProFlightButton: View {
    let action: DroneAction
    let isPrimary: Bool
    let isDisabled: Bool
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            VStack(spacing: 8) {
                Image(systemName: action.iconName)
                    .font(.title3)
                    .frame(width: 46, height: 46)
                    .background(
                        isPrimary ? GetFlyTheme.accentGradient : LinearGradient(colors: [GetFlyTheme.surface, GetFlyTheme.surfaceElevated], startPoint: .top, endPoint: .bottom),
                        in: Circle()
                    )
                    .foregroundStyle(isPrimary ? .black : GetFlyTheme.accent)
                    .shadow(color: isPrimary ? GetFlyTheme.accent.opacity(0.4) : .clear, radius: 8)
                Text(action.displayName)
                    .font(.system(size: 10, weight: .bold))
                    .foregroundStyle(GetFlyTheme.textPrimary)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 8)
            .background(GetFlyTheme.surface.opacity(0.6), in: RoundedRectangle(cornerRadius: 14))
        }
        .buttonStyle(PressScaleButtonStyle())
        .opacity(isDisabled ? 0.4 : 1)
        .disabled(isDisabled)
    }
}
