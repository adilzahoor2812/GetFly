//
//  GetFlyTheme.swift
//  GetFly
//

import SwiftUI

enum GetFlyTheme {
    static let accent = Color(red: 0.22, green: 0.55, blue: 0.98)
    static let accentSecondary = Color(red: 0.35, green: 0.78, blue: 0.98)
    static let surface = Color(.secondarySystemGroupedBackground)
    static let background = Color(.systemGroupedBackground)
    static let success = Color(red: 0.18, green: 0.78, blue: 0.44)
    static let warning = Color(red: 0.98, green: 0.62, blue: 0.18)
    static let danger = Color(red: 0.92, green: 0.26, blue: 0.21)
    static let offline = Color(red: 0.55, green: 0.55, blue: 0.58)

    static let cardRadius: CGFloat = 20
    static let cardShadow = Color.black.opacity(0.06)

    static var heroGradient: LinearGradient {
        LinearGradient(
            colors: [
                Color(red: 0.08, green: 0.16, blue: 0.38),
                Color(red: 0.14, green: 0.36, blue: 0.72),
                Color(red: 0.22, green: 0.55, blue: 0.98)
            ],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
    }

    static var screenBackground: LinearGradient {
        LinearGradient(
            colors: [
                Color(red: 0.95, green: 0.97, blue: 1.0),
                Color(.systemGroupedBackground)
            ],
            startPoint: .top,
            endPoint: .bottom
        )
    }
}

struct GetFlyScreenBackground: ViewModifier {
    func body(content: Content) -> some View {
        content
            .background(GetFlyTheme.screenBackground.ignoresSafeArea())
    }
}

extension View {
    func getFlyScreenBackground() -> some View {
        modifier(GetFlyScreenBackground())
    }
}
