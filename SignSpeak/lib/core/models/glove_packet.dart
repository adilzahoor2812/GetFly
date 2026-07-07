class GlovePacket {
  final String letter;
  final double confidence;
  final int battery;
  final int timestamp;
  final List<double> raw;

  const GlovePacket({
    required this.letter,
    required this.confidence,
    required this.battery,
    required this.timestamp,
    required this.raw,
  });

  factory GlovePacket.fromJson(Map<String, dynamic> json) {
    return GlovePacket(
      letter: (json['letter'] ?? '').toString(),
      confidence: (json['confidence'] ?? 0).toDouble(),
      battery: (json['battery'] ?? 0) as int,
      timestamp: (json['ts'] ?? 0) as int,
      raw: (json['raw'] as List<dynamic>? ?? const [])
          .map((value) => (value as num).toDouble())
          .toList(),
    );
  }
}
