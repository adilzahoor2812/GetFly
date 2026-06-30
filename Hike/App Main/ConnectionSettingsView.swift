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
                VStack(spacing: 20) {
                    settingsCard(
                        title: "ESP32 Connection",
                        subtitle: "Network address of your flight controller",
                        icon: "antenna.radiowaves.left.and.right"
                    ) {
                        labeledField("IP Address", text: $settings.hostAddress, keyboard: .decimalPad)
                        Stepper(value: $settings.port, in: 1...65535) {
                            HStack {
                                Text("Port")
                                Spacer()
                                Text("\(settings.port)")
                                    .foregroundStyle(.secondary)
                                    .monospacedDigit()
                            }
                        }
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Text("Status polling")
                                Spacer()
                                Text("\(String(format: "%.1f", settings.pollIntervalSeconds))s")
                                    .foregroundStyle(.secondary)
                            }
                            Slider(value: $settings.pollIntervalSeconds, in: 0.5...3, step: 0.5)
                                .tint(GetFlyTheme.accent)
                        }
                        GetFlyActionButton(
                            title: "Test Connection",
                            icon: "bolt.horizontal.fill",
                            style: .secondary,
                            isDisabled: false
                        ) {
                            Task { await viewModel.refreshStatus() }
                        }
                    }

                    settingsCard(
                        title: "Map Home Point",
                        subtitle: "Origin for local X/Y coordinates on OpenStreetMap",
                        icon: "mappin.and.ellipse"
                    ) {
                        labeledNumberField("Latitude", value: $settings.homeLatitude)
                        labeledNumberField("Longitude", value: $settings.homeLongitude)

                        GetFlyActionButton(
                            title: "Use My Location",
                            icon: "location.fill",
                            style: .secondary,
                            isDisabled: false
                        ) {
                            locationManager.requestLocation()
                        }

                        if let coordinate = locationManager.currentCoordinate {
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Detected location")
                                    .font(.caption.weight(.semibold))
                                    .foregroundStyle(.secondary)
                                Text("\(coordinate.latitude, format: .number.precision(.fractionLength(5))), \(coordinate.longitude, format: .number.precision(.fractionLength(5)))")
                                    .font(.subheadline.monospacedDigit())
                                GetFlyActionButton(
                                    title: "Set As Home",
                                    icon: "house.fill",
                                    style: .primary,
                                    isDisabled: false
                                ) {
                                    settings.setHome(to: coordinate)
                                }
                            }
                        }

                        if let error = locationManager.lastError {
                            Text(error)
                                .font(.caption)
                                .foregroundStyle(GetFlyTheme.danger)
                        }
                    }

                    settingsCard(
                        title: "Quick Tip",
                        subtitle: nil,
                        icon: "lightbulb.fill"
                    ) {
                        Text("When the ESP32 runs as a Wi‑Fi access point, connect your iPhone to GetFly-ESP32 and use address 192.168.4.1 on port 80.")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                }
                .padding(16)
            }
            .getFlyScreenBackground()
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                        .fontWeight(.semibold)
                }
            }
        }
    }

    @ViewBuilder
    private func settingsCard<Content: View>(
        title: String,
        subtitle: String?,
        icon: String,
        @ViewBuilder content: () -> Content
    ) -> some View {
        GetFlyCard {
            VStack(alignment: .leading, spacing: 16) {
                GetFlySectionHeader(title, subtitle: subtitle, icon: icon)
                content()
            }
        }
    }

    private func labeledField(_ title: String, text: Binding<String>, keyboard: UIKeyboardType) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.caption.weight(.semibold))
                .foregroundStyle(.secondary)
            TextField(title, text: text)
                .keyboardType(keyboard)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
                .padding(12)
                .background(Color(.tertiarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 12))
        }
    }

    private func labeledNumberField(_ title: String, value: Binding<Double>) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.caption.weight(.semibold))
                .foregroundStyle(.secondary)
            TextField(title, value: value, format: .number)
                .keyboardType(.decimalPad)
                .padding(12)
                .background(Color(.tertiarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 12))
        }
    }
}

#Preview {
    ConnectionSettingsView(settings: DroneConnectionSettings(), viewModel: DroneViewModel())
}
