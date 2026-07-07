import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_reactive_ble/flutter_reactive_ble.dart';

import '../../core/services/ble_service.dart';
import '../live_translate/live_translate_page.dart';

class PairingPage extends StatefulWidget {
  const PairingPage({super.key});

  @override
  State<PairingPage> createState() => _PairingPageState();
}

class _PairingPageState extends State<PairingPage> {
  final BleService _bleService = BleService();
  final List<DiscoveredDevice> _devices = <DiscoveredDevice>[];
  StreamSubscription<DiscoveredDevice>? _scanSub;
  bool _isScanning = false;

  @override
  void dispose() {
    _scanSub?.cancel();
    super.dispose();
  }

  void _startScan() {
    _scanSub?.cancel();
    setState(() {
      _devices.clear();
      _isScanning = true;
    });

    _scanSub = _bleService.scanDevices().listen((device) {
      if (_devices.any((d) => d.id == device.id)) return;
      setState(() {
        _devices.add(device);
      });
    }, onDone: () {
      setState(() {
        _isScanning = false;
      });
    }, onError: (_) {
      setState(() {
        _isScanning = false;
      });
    });
  }

  void _openLivePage(DiscoveredDevice device) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => LiveTranslatePage(device: device, bleService: _bleService),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('SignSpeak Pairing')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            FilledButton.icon(
              onPressed: _isScanning ? null : _startScan,
              icon: const Icon(Icons.bluetooth_searching),
              label: Text(_isScanning ? 'Scanning...' : 'Scan for Glove'),
            ),
            const SizedBox(height: 16),
            const Text('Devices', style: TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            Expanded(
              child: _devices.isEmpty
                  ? const Center(child: Text('No devices yet. Tap scan.'))
                  : ListView.separated(
                      itemCount: _devices.length,
                      separatorBuilder: (_, __) => const Divider(height: 1),
                      itemBuilder: (context, index) {
                        final device = _devices[index];
                        return ListTile(
                          title: Text(device.name.isEmpty ? 'Unknown Device' : device.name),
                          subtitle: Text(device.id),
                          trailing: FilledButton(
                            onPressed: () => _openLivePage(device),
                            child: const Text('Connect'),
                          ),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }
}
