//
//  GetFlyComponents.swift
//  GetFly
//

import SwiftUI

struct GetFlySectionHeader: View {
    let title: String
    let subtitle: String?
    let icon: String

    init(_ title: String, subtitle: String? = nil, icon: String) {
        self.title = title
        self.subtitle = subtitle
        self.icon = icon
    }

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: icon)
                .font(.title3.weight(.semibold))
                .foregroundStyle(.white)
                .frame(width: 40, height: 40)
                .background(GetFlyTheme.accent.gradient, in: RoundedRectangle(cornerRadius: 12))

            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.headline)
                if let subtitle {
                    Text(subtitle)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            Spacer()
        }
    }
}

struct GetFlyCard<Content: View>: View {
    @ViewBuilder var content: Content

    var body: some View {
        content
            .padding(16)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(GetFlyTheme.surface, in: RoundedRectangle(cornerRadius: GetFlyTheme.cardRadius))
            .shadow(color: GetFlyTheme.cardShadow, radius: 10, y: 4)
    }
}

struct GetFlyMetricTile: View {
    let title: String
    let value: String
    let icon: String
    let tint: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Image(systemName: icon)
                    .foregroundStyle(tint)
                Spacer()
            }
            Text(value)
                .font(.title3.bold().monospacedDigit())
                .lineLimit(1)
                .minimumScaleFactor(0.8)
            Text(title)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(tint.opacity(0.08), in: RoundedRectangle(cornerRadius: 16))
    }
}

struct GetFlyActionButton: View {
    let title: String
    let icon: String
    let style: Style
    let isDisabled: Bool
    let action: () -> Void

    enum Style {
        case primary, secondary, danger

        var background: AnyShapeStyle {
            switch self {
            case .primary: return AnyShapeStyle(GetFlyTheme.accent.gradient)
            case .secondary: return AnyShapeStyle(GetFlyTheme.surface)
            case .danger: return AnyShapeStyle(GetFlyTheme.danger.gradient)
            }
        }

        var foreground: Color {
            switch self {
            case .primary, .danger: return .white
            case .secondary: return GetFlyTheme.accent
            }
        }

        var border: Color {
            switch self {
            case .secondary: return GetFlyTheme.accent.opacity(0.25)
            default: return .clear
            }
        }
    }

    var body: some View {
        Button(action: action) {
            HStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.body.weight(.semibold))
                Text(title)
                    .font(.subheadline.weight(.semibold))
                    .lineLimit(1)
                    .minimumScaleFactor(0.85)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 14)
            .foregroundStyle(style.foreground)
            .background(style.background, in: RoundedRectangle(cornerRadius: 14))
            .overlay(
                RoundedRectangle(cornerRadius: 14)
                    .stroke(style.border, lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
        .opacity(isDisabled ? 0.45 : 1)
        .disabled(isDisabled)
    }
}

struct GetFlyFlightControlTile: View {
    let action: DroneAction
    let isPrimary: Bool
    let isDisabled: Bool
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            VStack(spacing: 10) {
                Image(systemName: action.iconName)
                    .font(.title2)
                    .frame(width: 48, height: 48)
                    .background(
                        (isPrimary ? GetFlyTheme.accent : Color(.tertiarySystemFill)),
                        in: Circle()
                    )
                    .foregroundStyle(isPrimary ? .white : GetFlyTheme.accent)

                Text(action.displayName)
                    .font(.caption.weight(.semibold))
                    .multilineTextAlignment(.center)
                    .foregroundStyle(.primary)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 12)
            .background(Color(.tertiarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 16))
        }
        .buttonStyle(.plain)
        .opacity(isDisabled ? 0.45 : 1)
        .disabled(isDisabled)
    }
}

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
        .background((isSuccess ? GetFlyTheme.success : GetFlyTheme.danger).opacity(0.95), in: Capsule())
        .shadow(color: .black.opacity(0.12), radius: 8, y: 4)
        .padding(.bottom, 8)
    }
}

struct GetFlyConnectionBanner: View {
    let isConnected: Bool
    let error: String?

    var body: some View {
        HStack(spacing: 10) {
            Circle()
                .fill(isConnected ? GetFlyTheme.success : GetFlyTheme.offline)
                .frame(width: 10, height: 10)

            VStack(alignment: .leading, spacing: 2) {
                Text(isConnected ? "Connected to ESP32" : "Not connected")
                    .font(.subheadline.weight(.semibold))
                Text(isConnected ? "Live telemetry active" : (error ?? "Check Wi‑Fi and ESP32 settings"))
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
            }

            Spacer()

            Image(systemName: isConnected ? "antenna.radiowaves.left.and.right" : "wifi.slash")
                .foregroundStyle(isConnected ? GetFlyTheme.success : GetFlyTheme.offline)
        }
        .padding(14)
        .background(
            (isConnected ? GetFlyTheme.success : GetFlyTheme.offline).opacity(0.1),
            in: RoundedRectangle(cornerRadius: 16)
        )
    }
}
