import 'dart:async';

import 'package:flutter/material.dart';

import '../../core/models/glove_packet.dart';
import '../../core/services/ble_service.dart';
import '../../core/services/mock_prediction_service.dart';
import '../../core/services/tts_service.dart';

class LiveTranslatePage extends StatefulWidget {
  const LiveTranslatePage({
    required this.title,
    required this.bleService,
    this.deviceId,
    this.useMock = false,
    super.key,
  });

  final String title;
  final BleService bleService;
  final String? deviceId;
  final bool useMock;

  @override
  State<LiveTranslatePage> createState() => _LiveTranslatePageState();
}

class _LiveTranslatePageState extends State<LiveTranslatePage> {
  final TtsService _ttsService = TtsService();
  final MockPredictionService _mockPredictionService = MockPredictionService();
  StreamSubscription<dynamic>? _connectionSub;
  StreamSubscription<GlovePacket>? _predictionSub;

  String _connectionText = 'Connecting...';
  String _currentLetter = '-';
  double _confidence = 0;
  int _battery = 0;
  String _sentence = '';

  @override
  void initState() {
    super.initState();
    _ttsService.init();
    if (widget.useMock) {
      _startMockStream();
    } else {
      _connectAndListen();
    }
  }

  @override
  void dispose() {
    _connectionSub?.cancel();
    _predictionSub?.cancel();
    _ttsService.stop();
    super.dispose();
  }

  void _startMockStream() {
    setState(() {
      _connectionText = 'mock_connected';
    });
    _predictionSub = _mockPredictionService.stream().listen((packet) {
      setState(() {
        _currentLetter = packet.letter.isEmpty ? '-' : packet.letter;
        _confidence = packet.confidence;
        _battery = packet.battery;
      });
    });
  }

  void _connectAndListen() {
    final deviceId = widget.deviceId;
    if (deviceId == null) {
      setState(() {
        _connectionText = 'No device selected';
      });
      return;
    }

    _connectionSub = widget.bleService.connect(deviceId).listen((update) {
      setState(() {
        _connectionText = update.connectionState.name;
      });

      if (update.connectionState.name == 'connected') {
        _predictionSub?.cancel();
        _predictionSub = widget.bleService.subscribePredictions(deviceId).listen((packet) {
          setState(() {
            _currentLetter = packet.letter.isEmpty ? '-' : packet.letter;
            _confidence = packet.confidence;
            _battery = packet.battery;
          });
        });
      }
    }, onError: (_) {
      setState(() {
        _connectionText = 'Error';
      });
    });
  }

  void _appendCurrentLetter() {
    if (_currentLetter == '-' || _currentLetter.trim().isEmpty) return;
    setState(() {
      _sentence += _currentLetter;
    });
  }

  void _addSpace() {
    setState(() {
      _sentence = '$_sentence ';
    });
  }

  void _backspace() {
    if (_sentence.isEmpty) return;
    setState(() {
      _sentence = _sentence.substring(0, _sentence.length - 1);
    });
  }

  void _clear() {
    setState(() {
      _sentence = '';
    });
  }

  Future<void> _speak() async {
    await _ttsService.speak(_sentence);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Live: ${widget.title}')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: <Widget>[
                    Text(
                      _currentLetter,
                      style: const TextStyle(fontSize: 72, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    LinearProgressIndicator(value: _confidence.clamp(0, 1)),
                    const SizedBox(height: 8),
                    Text('Confidence: ${(_confidence * 100).toStringAsFixed(1)}%'),
                    Text('Battery: $_battery%'),
                    Text('Connection: $_connectionText'),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            FilledButton(
              onPressed: _appendCurrentLetter,
              child: const Text('Append Letter'),
            ),
            const SizedBox(height: 12),
            Expanded(
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: SingleChildScrollView(
                    child: Text(
                      _sentence.isEmpty ? 'Sentence will appear here...' : _sentence,
                      style: const TextStyle(fontSize: 22),
                    ),
                  ),
                ),
              ),
            ),
            Row(
              children: <Widget>[
                Expanded(
                  child: OutlinedButton(onPressed: _addSpace, child: const Text('Space')),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: OutlinedButton(onPressed: _backspace, child: const Text('Backspace')),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: <Widget>[
                Expanded(
                  child: FilledButton.tonal(onPressed: _clear, child: const Text('Clear')),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: FilledButton(onPressed: _speak, child: const Text('Speak')),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
