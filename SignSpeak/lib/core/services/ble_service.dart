import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter_reactive_ble/flutter_reactive_ble.dart';

import '../constants/ble_constants.dart';
import '../models/glove_packet.dart';

class BleService {
  final FlutterReactiveBle _ble = FlutterReactiveBle();

  Stream<DiscoveredDevice> scanDevices() {
    return _ble.scanForDevices(
      withServices: const [],
      scanMode: ScanMode.lowLatency,
    ).where((device) => device.name.startsWith(BleConstants.deviceNamePrefix));
  }

  Stream<ConnectionStateUpdate> connect(String deviceId) {
    return _ble.connectToDevice(
      id: deviceId,
      connectionTimeout: const Duration(seconds: 10),
    );
  }

  Stream<GlovePacket> subscribePredictions(String deviceId) {
    final characteristic = QualifiedCharacteristic(
      serviceId: Uuid.parse(BleConstants.serviceUuid),
      characteristicId: Uuid.parse(BleConstants.notifyCharUuid),
      deviceId: deviceId,
    );

    return _ble.subscribeToCharacteristic(characteristic).map((bytes) {
      final payload = utf8.decode(bytes);
      final map = jsonDecode(payload) as Map<String, dynamic>;
      return GlovePacket.fromJson(map);
    });
  }

  Future<void> sendCommand(String deviceId, Map<String, dynamic> command) async {
    final characteristic = QualifiedCharacteristic(
      serviceId: Uuid.parse(BleConstants.serviceUuid),
      characteristicId: Uuid.parse(BleConstants.writeCharUuid),
      deviceId: deviceId,
    );
    final data = Uint8List.fromList(utf8.encode(jsonEncode(command)));
    await _ble.writeCharacteristicWithResponse(characteristic, value: data);
  }
}
