import 'dart:async';
import 'dart:math';

import '../models/glove_packet.dart';

class MockPredictionService {
  final Random _random = Random();

  Stream<GlovePacket> stream() async* {
    const letters = <String>[
      'H',
      'E',
      'L',
      'L',
      'O',
      ' ',
      'S',
      'I',
      'G',
      'N',
    ];
    var index = 0;

    while (true) {
      await Future<void>.delayed(const Duration(milliseconds: 700));
      final letter = letters[index % letters.length];
      index++;

      yield GlovePacket(
        letter: letter,
        confidence: 0.75 + (_random.nextDouble() * 0.24),
        battery: 70 + _random.nextInt(30),
        timestamp: DateTime.now().millisecondsSinceEpoch,
        raw: List<double>.generate(8, (_) => _random.nextDouble()),
      );
    }
  }
}
