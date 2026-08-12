import struct
import unittest

from core.parser import ConnectionHealthTracker, parse_text_line


class ParserTests(unittest.TestCase):
    def test_parse_text_line_supports_json_and_key_value(self):
        json_packet = parse_text_line('{"appsPercent": 45, "batteryVoltage": 396}')
        self.assertEqual(json_packet["appsPercent"], 45)
        self.assertEqual(json_packet["batteryVoltage"], 396)

        kv_packet = parse_text_line("appsPercent: 45, batteryVoltage: 396, seqNumber: 104")
        self.assertEqual(kv_packet["appsPercent"], 45)
        self.assertEqual(kv_packet["batteryVoltage"], 396)
        self.assertEqual(kv_packet["seqNumber"], 104)

    def test_parse_text_line_supports_hex_binary_payload(self):
        payload = struct.pack(
            "<BBBBhhHhBBBBBI",
            2, 0, 45, 12,
            120, 3000,
            3950, -15,
            85, 40, 22, 30,
            0b1011,
            123456,
        )

        packet = parse_text_line(payload.hex())
        self.assertEqual(packet["vehicleState"], "DRIVING")
        self.assertEqual(packet["appsPercent"], 45)
        self.assertEqual(packet["batteryVoltage"], 395.0)
        self.assertTrue(packet["systemFlags"]["AIR-"])
        self.assertTrue(packet["systemFlags"]["SDC Closed"])
        self.assertEqual(packet["uptimeMs"], 123456)

    def test_health_tracker_calculates_loss_and_latency(self):
        tracker = ConnectionHealthTracker()

        first = tracker.process_health_metrics({"seqNumber": 1, "uptimeMs": 1000})
        second = tracker.process_health_metrics({"seqNumber": 3, "uptimeMs": 2000})

        self.assertEqual(first["lossPercent"], 0.0)
        self.assertEqual(second["lossPercent"], 50.0)
        self.assertGreaterEqual(second["latencyMs"], 0)


if __name__ == "__main__":
    unittest.main()
