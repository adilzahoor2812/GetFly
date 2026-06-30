//
//  GetFlyTheme.swift
//  GetFly
//

import SwiftUI

enum GetFlyTheme {
    // Aviation / DJI-inspired palette
    static let accent = Color(red: 0.0, green: 0.75, blue: 1.0)
    static let accentGlow = Color(red: 0.0, green: 0.85, blue: 1.0)
    static let hudBackground = Color(red: 0.04, green: 0.06, blue: 0.10).opacity(0.82)
    static let panelBackground = Color(red: 0.07, green: 0.09, blue: 0.14)
    static let surface = Color(red: 0.11, green: 0.13, blue: 0.18)
    static let surfaceElevated = Color(red: 0.15, green: 0.17, blue: 0.22)
    static let textPrimary = Color.white
    static let textSecondary = Color.white.opacity(0.62)
    static let success = Color(red: 0.20, green: 0.90, blue: 0.55)
    static let warning = Color(red: 1.0, green: 0.72, blue: 0.18)
    static let danger = Color(red: 1.0, green: 0.32, blue: 0.28)
    static let offline = Color(red: 0.45, green: 0.48, blue: 0.52)
    static let missionPath = Color(red: 0.0, green: 0.78, blue: 1.0)
    static let waypointActive = Color(red: 1.0, green: 0.82, blue: 0.0)

    static let cardShadow = Color.black.opacity(0.35)

    static let cardRadius: CGFloat = 22
    static let hudRadius: CGFloat = 16
    static let panelRadius: CGFloat = 28

    static var accentGradient: LinearGradient {
        LinearGradient(
            colors: [Color(red: 0.0, green: 0.55, blue: 0.95), accent],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
    }

    static var mapVignette: LinearGradient {
        LinearGradient(
            colors: [
                Color.black.opacity(0.55),
                Color.black.opacity(0.08),
                Color.black.opacity(0.08),
                Color.black.opacity(0.65)
            ],
            startPoint: .top,
            endPoint: .bottom
        )
    }

    static var flyButtonGradient: LinearGradient {
        LinearGradient(
            colors: [Color(red: 0.0, green: 0.65, blue: 0.45), success],
            startPoint: .top,
            endPoint: .bottom
        )
    }
}

struct GlassPanel: ViewModifier {
    var cornerRadius: CGFloat = GetFlyTheme.hudRadius

    func body(content: Content) -> some View {
        content
            .background(.ultraThinMaterial.opacity(0.85), in: RoundedRectangle(cornerRadius: cornerRadius))
            .background(GetFlyTheme.hudBackground, in: RoundedRectangle(cornerRadius: cornerRadius))
            .overlay(
                RoundedRectangle(cornerRadius: cornerRadius)
                    .stroke(
                        LinearGradient(
                            colors: [Color.white.opacity(0.22), Color.white.opacity(0.04)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ),
                        lineWidth: 1
                    )
            )
    }
}

extension View {
    func glassPanel(cornerRadius: CGFloat = GetFlyTheme.hudRadius) -> some View {
        modifier(GlassPanel(cornerRadius: cornerRadius))
    }

    func getFlyProBackground() -> some View {
        background(Color.black.ignoresSafeArea())
    }
}

struct PressScaleButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.94 : 1)
            .animation(.spring(response: 0.28, dampingFraction: 0.65), value: configuration.isPressed)
    }
}

struct StaggeredAppear: ViewModifier {
    let index: Int
    @State private var appeared = false

    func body(content: Content) -> some View {
        content
            .opacity(appeared ? 1 : 0)
            .offset(y: appeared ? 0 : 18)
            .onAppear {
                withAnimation(.spring(response: 0.5, dampingFraction: 0.78).delay(Double(index) * 0.06)) {
                    appeared = true
                }
            }
    }
}

extension View {
    func staggeredAppear(index: Int) -> some View {
        modifier(StaggeredAppear(index: index))
    }
}
