//
//  ConnectionSettingsView.swift
//  GetFly
//

import SwiftUI

struct ConnectionSettingsView: View {
    @ObservedObject var settings: DroneConnectionSettings
    @ObservedObject var viewModel: DroneViewModel
    @StateObject private var locationManager = LocationManager()
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    settingsSection(
                        title: "ESP32 Link",
                        icon: "antenna.radiowaves.left.and.right"
                    ) {
                        proField("IP Address", text: $settings.hostAddress)
                        Stepper(value: $settings.port, in: 1...65535) {
                            HStack {
                                Text("Port")
                                    .foregroundStyle(GetFlyTheme.textPrimary)
                                Spacer()
                                Text("\(settings.port)")
                                    .foregroundStyle(GetFlyTheme.accent)
                                    .fontDesign(.monospaced)
                            }
                        }
                        .tint(GetFlyTheme.accent)
                        VStack(alignment: .leading, spacing: 6) {
                            Text("Poll interval: \(String(format: "%.1f", settings.pollIntervalSeconds))s")
                                .font(.caption)
                                .foregroundStyle(GetFlyTheme.textSecondary)
                            Slider(value: $settings.pollIntervalSeconds, in: 0.5...3, step: 0.5)
                                .tint(GetFlyTheme.accent)
                        }
                        FlyMissionButton(
                            title: "Test Connection",
                            icon: "bolt.horizontal.fill",
                            isDisabled: false,
                            isRunning: false
                        ) {
                            Task { await viewModel.refreshStatus() }
                        }
                    }

                    settingsSection(title: "Map Home", icon: "mappin.and.ellipse") {
                        proNumberField("Latitude", value: $settings.homeLatitude)
                        proNumberField("Longitude", value: $settings.homeLongitude)
                        FlyMissionButton(
                            title: "Use My Location",
                            icon: "location.fill",
                            isDisabled: false,
                            isRunning: false
                        ) {
                            locationManager.requestLocation()
                        }
                        if let coordinate = locationManager.currentCoordinate {
                            Text("\(coordinate.latitude, format: .number.precision(.fractionLength(5))), \(coordinate.longitude, format: .number.precision(.fractionLength(5)))")
                                .font(.caption.monospacedDigit())
                                .foregroundStyle(GetFlyTheme.textSecondary)
                            FlyMissionButton(
                                title: "Set As Home",
                                icon: "house.fill",
                                isDisabled: false,
                                isRunning: false
                            ) {
                                settings.setHome(to: coordinate)
                            }
                        }
                        if let error = locationManager.lastError {
                            Text(error)
                                .font(.caption)
                                .foregroundStyle(GetFlyTheme.danger)
                        }
                    }
                }
                .padding(16)
            }
            .getFlyProBackground()
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                        .fontWeight(.semibold)
                        .foregroundStyle(GetFlyTheme.accent)
                }
            }
        }
    }

    @ViewBuilder
    private func settingsSection<Content: View>(
        title: String,
        icon: String,
        @ViewBuilder content: () -> Content
    ) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            Label(title, systemImage: icon)
                .font(.headline)
                .foregroundStyle(GetFlyTheme.textPrimary)
            content()
        }
        .padding(16)
        .glassPanel(cornerRadius: GetFlyTheme.cardRadius)
    }

    private func proField(_ placeholder: String, text: Binding<String>) -> some View {
        TextField(placeholder, text: text)
            .keyboardType(.decimalPad)
            .textInputAutocapitalization(.never)
            .autocorrectionDisabled()
            .padding(12)
            .background(GetFlyTheme.surface, in: RoundedRectangle(cornerRadius: 12))
            .foregroundStyle(GetFlyTheme.textPrimary)
    }

    private func proNumberField(_ placeholder: String, value: Binding<Double>) -> some View {
        TextField(placeholder, value: value, format: .number)
            .keyboardType(.decimalPad)
            .padding(12)
            .background(GetFlyTheme.surface, in: RoundedRectangle(cornerRadius: 12))
            .foregroundStyle(GetFlyTheme.textPrimary)
    }
}

#Preview {
    ConnectionSettingsView(settings: DroneConnectionSettings(), viewModel: DroneViewModel())
        .preferredColorScheme(.dark)
}
