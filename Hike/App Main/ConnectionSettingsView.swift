//
//  ConnectionSettingsView.swift
//  Hike
//

import SwiftUI

struct ConnectionSettingsView: View {
    @ObservedObject var settings: DroneConnectionSettings
    @ObservedObject var viewModel: DroneViewModel
    @StateObject private var locationManager = LocationManager()
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            Form {
                Section("ESP32 Network") {
                    TextField("IP Address", text: $settings.hostAddress)
                        .keyboardType(.decimalPad)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()

                    Stepper("Port: \(settings.port)", value: $settings.port, in: 1...65535)

                    Slider(value: $settings.pollIntervalSeconds, in: 0.5...3, step: 0.5) {
                        Text("Status Poll Interval")
                    } minimumValueLabel: {
                        Text("0.5s")
                    } maximumValueLabel: {
                        Text("3s")
                    }

                    Text("Poll every \(String(format: "%.1f", settings.pollIntervalSeconds)) seconds")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Section("OpenStreetMap Home Point") {
                    Text("Set the map home location. Local X/Y coordinates are calculated relative to this point.")
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    TextField("Home Latitude", value: $settings.homeLatitude, format: .number)
                        .keyboardType(.decimalPad)

                    TextField("Home Longitude", value: $settings.homeLongitude, format: .number)
                        .keyboardType(.decimalPad)

                    Button("Use My Current Location") {
                        locationManager.requestLocation()
                    }

                    if let coordinate = locationManager.currentCoordinate {
                        Text("Detected: \(coordinate.latitude, format: .number.precision(.fractionLength(5))), \(coordinate.longitude, format: .number.precision(.fractionLength(5)))")
                            .font(.caption)
                            .foregroundStyle(.secondary)

                        Button("Set As Home") {
                            settings.setHome(to: coordinate)
                        }
                    }

                    if let error = locationManager.lastError {
                        Text(error)
                            .font(.caption)
                            .foregroundStyle(.red)
                    }
                }

                Section("Default ESP32 AP") {
                    Text("When the ESP32 runs as a Wi‑Fi access point, the default address is usually 192.168.4.1 on port 80.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Section {
                    Button("Test Connection") {
                        Task { await viewModel.refreshStatus() }
                    }
                }
            }
            .navigationTitle("Settings")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }
}

#Preview {
    ConnectionSettingsView(settings: DroneConnectionSettings(), viewModel: DroneViewModel())
}
