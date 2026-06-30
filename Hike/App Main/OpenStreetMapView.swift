//
//  OpenStreetMapView.swift
//  Hike
//

import MapKit
import SwiftUI

private final class OpenStreetMapTileOverlay: MKTileOverlay {
    init() {
        super.init(urlTemplate: "https://tile.openstreetmap.org/{z}/{x}/{y}.png")
        canReplaceMapContent = true
    }
}

struct OpenStreetMapView: UIViewRepresentable {
    let homeCoordinate: CLLocationCoordinate2D
    let dronePosition: Coordinate3D
    let targetPosition: Coordinate3D
    let waypoints: [Waypoint]
    var onMapTap: ((Coordinate3D) -> Void)?

    func makeCoordinator() -> Coordinator {
        Coordinator(parent: self)
    }

    func makeUIView(context: Context) -> MKMapView {
        let mapView = MKMapView(frame: .zero)
        mapView.delegate = context.coordinator
        mapView.pointOfInterestFilter = .excludingAll
        mapView.showsCompass = true
        mapView.showsScale = true
        mapView.isRotateEnabled = false

        let overlay = OpenStreetMapTileOverlay()
        mapView.addOverlay(overlay, level: .aboveLabels)

        let tap = UITapGestureRecognizer(target: context.coordinator, action: #selector(Coordinator.handleTap(_:)))
        mapView.addGestureRecognizer(tap)

        context.coordinator.mapView = mapView
        context.coordinator.syncMap(animated: false)
        return mapView
    }

    func updateUIView(_ mapView: MKMapView, context: Context) {
        context.coordinator.parent = self
        context.coordinator.syncMap(animated: true)
    }

    final class Coordinator: NSObject, MKMapViewDelegate {
        var parent: OpenStreetMapView
        weak var mapView: MKMapView?

        init(parent: OpenStreetMapView) {
            self.parent = parent
        }

        func syncMap(animated: Bool) {
            guard let mapView else { return }

            mapView.removeAnnotations(mapView.annotations)
            mapView.removeOverlays(mapView.overlays.filter { $0 is MKPolyline })

            let home = parent.homeCoordinate
            let droneGeo = CoordinateConverter.coordinate(parent.dronePosition, home: home)
            let targetGeo = CoordinateConverter.coordinate(parent.targetPosition, home: home)

            mapView.addAnnotation(MapAnnotation(kind: .home, coordinate: home))
            mapView.addAnnotation(MapAnnotation(kind: .drone, coordinate: droneGeo))
            mapView.addAnnotation(MapAnnotation(kind: .target, coordinate: targetGeo))

            for waypoint in parent.waypoints {
                let geo = CoordinateConverter.coordinate(waypoint.coordinate, home: home)
                mapView.addAnnotation(MapAnnotation(kind: .waypoint, coordinate: geo))
            }

            var routePoints = parent.waypoints.map {
                CoordinateConverter.coordinate($0.coordinate, home: home)
            }

            if routePoints.count > 1 {
                var coordinates = routePoints
                let polyline = MKPolyline(coordinates: &coordinates, count: coordinates.count)
                mapView.addOverlay(polyline)
            }

            var droneTarget = [droneGeo, targetGeo]
            let droneToTarget = MKPolyline(coordinates: &droneTarget, count: droneTarget.count)
            mapView.addOverlay(droneToTarget)

            if !animated || mapView.region.span.latitudeDelta > 0.05 {
                let region = regionCovering(
                    home: home,
                    drone: droneGeo,
                    target: targetGeo,
                    waypoints: parent.waypoints.map { CoordinateConverter.coordinate($0.coordinate, home: home) }
                )
                mapView.setRegion(region, animated: animated)
            }
        }

        @objc func handleTap(_ gesture: UITapGestureRecognizer) {
            guard let mapView, gesture.state == .ended else { return }
            let point = gesture.location(in: mapView)
            let coordinate = mapView.convert(point, toCoordinateFrom: mapView)
            let local = CoordinateConverter.localCoordinate(
                from: coordinate,
                home: parent.homeCoordinate,
                altitude: parent.targetPosition.z
            )
            parent.onMapTap?(local)
        }

        func mapView(_ mapView: MKMapView, rendererFor overlay: MKOverlay) -> MKOverlayRenderer {
            if overlay is MKTileOverlay {
                return MKTileOverlayRenderer(overlay: overlay)
            }

            if let polyline = overlay as? MKPolyline {
                let renderer = MKPolylineRenderer(polyline: polyline)
                if polyline.pointCount == 2 {
                    renderer.strokeColor = UIColor.systemOrange.withAlphaComponent(0.85)
                    renderer.lineWidth = 2
                    renderer.lineDashPattern = [6, 4]
                } else {
                    renderer.strokeColor = UIColor.systemBlue.withAlphaComponent(0.75)
                    renderer.lineWidth = 3
                }
                return renderer
            }

            return MKOverlayRenderer(overlay: overlay)
        }

        func mapView(_ mapView: MKMapView, viewFor annotation: MKAnnotation) -> MKAnnotationView? {
            guard let annotation = annotation as? MapAnnotation else { return nil }

            let identifier = "MapAnnotation-\(annotation.kind.rawValue)"
            let view = mapView.dequeueReusableAnnotationView(withIdentifier: identifier) as? MKMarkerAnnotationView
                ?? MKMarkerAnnotationView(annotation: annotation, reuseIdentifier: identifier)

            view.annotation = annotation
            view.canShowCallout = true
            view.titleVisibility = .visible
            view.subtitleVisibility = .hidden

            switch annotation.kind {
            case .home:
                view.markerTintColor = .systemPurple
                view.glyphText = "H"
            case .drone:
                view.markerTintColor = .systemGreen
                view.glyphText = "D"
            case .target:
                view.markerTintColor = .systemOrange
                view.glyphText = "T"
            case .waypoint:
                view.markerTintColor = .systemBlue
                view.glyphText = "W"
            }

            return view
        }

        private func regionCovering(
            home: CLLocationCoordinate2D,
            drone: CLLocationCoordinate2D,
            target: CLLocationCoordinate2D,
            waypoints: [CLLocationCoordinate2D]
        ) -> MKCoordinateRegion {
            var minLat = min(home.latitude, drone.latitude, target.latitude)
            var maxLat = max(home.latitude, drone.latitude, target.latitude)
            var minLon = min(home.longitude, drone.longitude, target.longitude)
            var maxLon = max(home.longitude, drone.longitude, target.longitude)

            for waypoint in waypoints {
                minLat = min(minLat, waypoint.latitude)
                maxLat = max(maxLat, waypoint.latitude)
                minLon = min(minLon, waypoint.longitude)
                maxLon = max(maxLon, waypoint.longitude)
            }

            let center = CLLocationCoordinate2D(
                latitude: (minLat + maxLat) / 2,
                longitude: (minLon + maxLon) / 2
            )

            let latDelta = max((maxLat - minLat) * 1.8, 0.001)
            let lonDelta = max((maxLon - minLon) * 1.8, 0.001)
            let span = MKCoordinateSpan(latitudeDelta: latDelta, longitudeDelta: lonDelta)
            return MKCoordinateRegion(center: center, span: span)
        }
    }
}

private final class MapAnnotation: NSObject, MKAnnotation {
    enum Kind: String {
        case home
        case drone
        case target
        case waypoint
    }

    let kind: Kind
    dynamic var coordinate: CLLocationCoordinate2D

    var title: String? {
        switch kind {
        case .home: "Home"
        case .drone: "Drone"
        case .target: "Target"
        case .waypoint: "Waypoint"
        }
    }

    init(kind: Kind, coordinate: CLLocationCoordinate2D) {
        self.kind = kind
        self.coordinate = coordinate
    }
}
