//
//  DroneMissionUI.swift
//  GetFly
//

import SwiftUI

// MARK: - HUD

struct DroneHUDView: View {
    let altitude: Double
    let battery: Int
    let isConnected: Bool
    let isFlying: Bool
    let mode: String
    let navigationLabel: String

    var body: some View {
        VStack(spacing: 10) {
            HStack(alignment: .top, spacing: 10) {
                HUDGauge(
                    value: altitude,
                    max: 120,
                    unit: "m",
                    label: "ALT",
                    tint: GetFlyTheme.accent,
                    icon: "arrow.up.and.down"
                )
                .frame(maxWidth: .infinity)

                VStack(spacing: 8) {
                    HStack(spacing: 6) {
                        Circle()
                            .fill(isConnected ? GetFlyTheme.success : GetFlyTheme.danger)
                            .frame(width: 8, height: 8)
                            .shadow(color: (isConnected ? GetFlyTheme.success : GetFlyTheme.danger).opacity(0.8), radius: 4)
                        Text(isConnected ? "LINK OK" : "NO LINK")
                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                            .foregroundStyle(GetFlyTheme.textPrimary)
                    }
                    .padding(.horizontal, 10)
                    .padding(.vertical, 6)
                    .glassPanel(cornerRadius: 10)

                    if isFlying {
                        Label(navigationLabel, systemImage: "airplane")
                            .font(.system(size: 11, weight: .semibold))
                            .foregroundStyle(GetFlyTheme.success)
                            .symbolEffect(.pulse, isActive: true)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 6)
                            .glassPanel(cornerRadius: 10)
                            .transition(.scale.combined(with: .opacity))
                    }
                }

                HUDGauge(
                    value: Double(battery),
                    max: 100,
                    unit: "%",
                    label: "BAT",
                    tint: batteryTint,
                    icon: "battery.100"
                )
                .frame(maxWidth: .infinity)
            }

            HStack {
                Text("MODE")
                    .font(.system(size: 9, weight: .bold, design: .monospaced))
                    .foregroundStyle(GetFlyTheme.textSecondary)
                Text(mode.uppercased())
                    .font(.system(size: 12, weight: .heavy, design: .monospaced))
                    .foregroundStyle(GetFlyTheme.accent)
                Spacer()
                Image(systemName: "antenna.radiowaves.left.and.right")
                    .foregroundStyle(GetFlyTheme.accent.opacity(0.7))
            }
            .padding(.horizontal, 4)
        }
        .padding(12)
        .glassPanel(cornerRadius: GetFlyTheme.hudRadius)
        .animation(.spring(response: 0.45, dampingFraction: 0.8), value: isFlying)
    }

    private var batteryTint: Color {
        switch battery {
        case 0..<20: return GetFlyTheme.danger
        case 20..<45: return GetFlyTheme.warning
        default: return GetFlyTheme.success
        }
    }
}

struct HUDGauge: View {
    let value: Double
    let max: Double
    let unit: String
    let label: String
    let tint: Color
    let icon: String

    @State private var animatedValue: Double = 0

    var body: some View {
        VStack(spacing: 6) {
            ZStack {
                Circle()
                    .stroke(Color.white.opacity(0.08), lineWidth: 5)
                Circle()
                    .trim(from: 0, to: animatedValue / max)
                    .stroke(tint.gradient, style: StrokeStyle(lineWidth: 5, lineCap: .round))
                    .rotationEffect(.degrees(-90))
                    .shadow(color: tint.opacity(0.5), radius: 6)
                VStack(spacing: 0) {
                    Image(systemName: icon)
                        .font(.caption2)
                        .foregroundStyle(tint)
                    Text(String(format: "%.0f", animatedValue))
                        .font(.system(size: 16, weight: .bold, design: .rounded))
                        .foregroundStyle(GetFlyTheme.textPrimary)
                    Text(unit)
                        .font(.system(size: 9, weight: .medium))
                        .foregroundStyle(GetFlyTheme.textSecondary)
                }
            }
            .frame(width: 72, height: 72)

            Text(label)
                .font(.system(size: 9, weight: .bold, design: .monospaced))
                .foregroundStyle(GetFlyTheme.textSecondary)
        }
        .onAppear { animateTo(value) }
        .onChange(of: value) { _, new in animateTo(new) }
    }

    private func animateTo(_ target: Double) {
        withAnimation(.spring(response: 0.7, dampingFraction: 0.75)) {
            animatedValue = min(target, max)
        }
    }
}

// MARK: - Mode selector

enum MissionPanelMode: String, CaseIterable {
    case plan = "Plan"
    case target = "Target"
    case fly = "Fly"

    var icon: String {
        switch self {
        case .plan: return "point.topleft.down.curvedto.point.bottomright.up"
        case .target: return "scope"
        case .fly: return "airplane.circle.fill"
        }
    }
}

struct MissionModeSelector: View {
    @Binding var selection: MissionPanelMode
    @Namespace private var ns

    var body: some View {
        HStack(spacing: 4) {
            ForEach(MissionPanelMode.allCases, id: \.self) { mode in
                Button {
                    withAnimation(.spring(response: 0.38, dampingFraction: 0.78)) {
                        selection = mode
                    }
                } label: {
                    HStack(spacing: 6) {
                        Image(systemName: mode.icon)
                            .font(.caption.weight(.semibold))
                        Text(mode.rawValue)
                            .font(.caption.weight(.bold))
                    }
                    .foregroundStyle(selection == mode ? Color.black : GetFlyTheme.textSecondary)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .background {
                        if selection == mode {
                            Capsule()
                                .fill(GetFlyTheme.accent.gradient)
                                .matchedGeometryEffect(id: "modePill", in: ns)
                                .shadow(color: GetFlyTheme.accent.opacity(0.45), radius: 8, y: 2)
                        }
                    }
                }
                .buttonStyle(PressScaleButtonStyle())
            }
        }
        .padding(5)
        .background(Color.white.opacity(0.06), in: Capsule())
    }
}

// MARK: - Waypoint strip

struct WaypointStripView: View {
    let waypoints: [Waypoint]
    let activeIndex: Int?
    let onAdd: () -> Void
    let onRemove: (Int) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Label("Mission Path", systemImage: "arrow.triangle.turn.up.right.diamond.fill")
                    .font(.caption.weight(.bold))
                    .foregroundStyle(GetFlyTheme.textPrimary)
                Spacer()
                Text("\(waypoints.count) WP")
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(GetFlyTheme.accent)
            }
            .padding(.horizontal, 4)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 10) {
                    Button(action: onAdd) {
                        VStack(spacing: 6) {
                            Image(systemName: "plus")
                                .font(.title3.weight(.bold))
                            Text("Add")
                                .font(.caption2.weight(.bold))
                        }
                        .foregroundStyle(GetFlyTheme.accent)
                        .frame(width: 64, height: 72)
                        .background(GetFlyTheme.accent.opacity(0.12), in: RoundedRectangle(cornerRadius: 14))
                        .overlay(
                            RoundedRectangle(cornerRadius: 14)
                                .strokeBorder(GetFlyTheme.accent.opacity(0.35), style: StrokeStyle(lineWidth: 1.5, dash: [5, 4]))
                        )
                    }
                    .buttonStyle(PressScaleButtonStyle())

                    ForEach(Array(waypoints.enumerated()), id: \.element.id) { index, waypoint in
                        WaypointChip(
                            index: index,
                            coordinate: waypoint.coordinate,
                            isActive: activeIndex == index,
                            isCompleted: (activeIndex ?? -1) > index
                        ) {
                            onRemove(index)
                        }
                        .staggeredAppear(index: index)
                    }
                }
                .padding(.horizontal, 2)
            }
        }
        .padding(12)
        .glassPanel(cornerRadius: GetFlyTheme.hudRadius)
    }
}

struct WaypointChip: View {
    let index: Int
    let coordinate: Coordinate3D
    let isActive: Bool
    let isCompleted: Bool
    let onDelete: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                ZStack {
                    Circle()
                        .fill(isActive ? GetFlyTheme.waypointActive.gradient : GetFlyTheme.accentGradient)
                        .frame(width: 26, height: 26)
                    if isCompleted {
                        Image(systemName: "checkmark")
                            .font(.caption2.bold())
                            .foregroundStyle(.black)
                    } else {
                        Text("\(index + 1)")
                            .font(.caption.bold())
                            .foregroundStyle(isActive ? .black : .white)
                    }
                }
                Spacer()
                Button(action: onDelete) {
                    Image(systemName: "xmark")
                        .font(.caption2.bold())
                        .foregroundStyle(GetFlyTheme.textSecondary)
                }
            }
            Text(String(format: "%.1f, %.1f m", coordinate.x, coordinate.y))
                .font(.system(size: 10, weight: .medium, design: .monospaced))
                .foregroundStyle(GetFlyTheme.textSecondary)
            Text(String(format: "Alt %.1fm", coordinate.z))
                .font(.system(size: 9, weight: .semibold, design: .monospaced))
                .foregroundStyle(GetFlyTheme.accent)
        }
        .padding(10)
        .frame(width: 110, height: 72)
        .background(
            isActive ? GetFlyTheme.waypointActive.opacity(0.12) : GetFlyTheme.surface.opacity(0.9),
            in: RoundedRectangle(cornerRadius: 14)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 14)
                .stroke(isActive ? GetFlyTheme.waypointActive : Color.white.opacity(0.08), lineWidth: isActive ? 2 : 1)
        )
        .scaleEffect(isActive ? 1.04 : 1)
        .animation(.spring(response: 0.35, dampingFraction: 0.7), value: isActive)
    }
}

// MARK: - Mission progress ring

struct MissionProgressRing: View {
    let progress: Double
    let label: String

    var body: some View {
        HStack(spacing: 12) {
            ZStack {
                Circle()
                    .stroke(Color.white.opacity(0.1), lineWidth: 4)
                    .frame(width: 44, height: 44)
                Circle()
                    .trim(from: 0, to: progress)
                    .stroke(GetFlyTheme.success.gradient, style: StrokeStyle(lineWidth: 4, lineCap: .round))
                    .frame(width: 44, height: 44)
                    .rotationEffect(.degrees(-90))
                    .animation(.spring(response: 0.6, dampingFraction: 0.8), value: progress)
                Image(systemName: "airplane")
                    .font(.caption)
                    .foregroundStyle(GetFlyTheme.success)
                    .symbolEffect(.bounce, value: progress)
            }
            VStack(alignment: .leading, spacing: 2) {
                Text(label)
                    .font(.caption.weight(.bold))
                    .foregroundStyle(GetFlyTheme.textPrimary)
                Text("\(Int(progress * 100))% complete")
                    .font(.system(size: 10, weight: .medium, design: .monospaced))
                    .foregroundStyle(GetFlyTheme.textSecondary)
            }
            Spacer()
        }
        .padding(12)
        .glassPanel()
        .transition(.move(edge: .top).combined(with: .opacity))
    }
}

// MARK: - FAB

struct DroneFAB: View {
    let icon: String
    let tint: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Image(systemName: icon)
                .font(.body.weight(.semibold))
                .foregroundStyle(.white)
                .frame(width: 48, height: 48)
                .background(tint.gradient, in: Circle())
                .shadow(color: tint.opacity(0.45), radius: 10, y: 4)
        }
        .buttonStyle(PressScaleButtonStyle())
    }
}

struct FlyMissionButton: View {
    let title: String
    let icon: String
    let isDisabled: Bool
    let isRunning: Bool
    var style: Style = .primary
    let action: () -> Void

    enum Style {
        case primary, danger

        var background: AnyShapeStyle {
            switch self {
            case .primary: return AnyShapeStyle(GetFlyTheme.flyButtonGradient)
            case .danger: return AnyShapeStyle(LinearGradient(colors: [GetFlyTheme.danger, GetFlyTheme.danger.opacity(0.75)], startPoint: .top, endPoint: .bottom))
            }
        }

        var shadowColor: Color {
            switch self {
            case .primary: return GetFlyTheme.success
            case .danger: return GetFlyTheme.danger
            }
        }
    }

    var body: some View {
        Button(action: action) {
            HStack(spacing: 10) {
                Image(systemName: icon)
                    .font(.headline)
                    .symbolEffect(.pulse, isActive: isRunning)
                Text(title)
                    .font(.headline.weight(.bold))
            }
            .foregroundStyle(.white)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 16)
            .background(
                isDisabled ? AnyShapeStyle(Color.gray.opacity(0.4)) : background,
                in: RoundedRectangle(cornerRadius: 16)
            )
            .shadow(color: shadowColor.opacity(isDisabled ? 0 : 0.35), radius: 12, y: 4)
        }
        .buttonStyle(PressScaleButtonStyle())
        .disabled(isDisabled)
    }

    private var background: AnyShapeStyle { style.background }
    private var shadowColor: Color { style.shadowColor }
}

// MARK: - Toast

struct GetFlyToast: View {
    let message: String
    let isSuccess: Bool

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: isSuccess ? "checkmark.circle.fill" : "exclamationmark.triangle.fill")
            Text(message)
                .font(.subheadline.weight(.medium))
        }
        .foregroundStyle(.white)
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .glassPanel(cornerRadius: 999)
        .overlay(
            Capsule()
                .stroke((isSuccess ? GetFlyTheme.success : GetFlyTheme.danger).opacity(0.6), lineWidth: 1)
        )
        .padding(.bottom, 8)
    }
}
