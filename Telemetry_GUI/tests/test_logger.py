# -*- coding: utf-8 -*-
import os
import tempfile
import unittest

from core.logger import TelemetryCSVLogger, CSV_FIELDNAMES


class LoggerTests(unittest.TestCase):
    def test_logger_creates_file_and_writes_row(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = TelemetryCSVLogger(log_dir=temp_dir, flush_interval=1)
            logger.open()
            self.assertTrue(os.path.exists(logger.filepath))
            self.assertEqual(logger.writer.fieldnames, CSV_FIELDNAMES)

            packet = {
                "seqNumber": 1,
                "uptimeMs": 1000,
                "vehicleState": "READY",
                "faultCode": 0,
                "appsPercent": 10,
                "brakePressure": 5,
                "torqueCommand": 20,
                "batteryVoltage": 350.0,
                "batteryCurrent": 12.5,
                "batterySOC": 98,
                "motorRPM": 1200,
                "motorTemp": 45,
                "inverterTemp": 40,
                "maxCellTemp": 42,
                "lossPercent": 0.0,
                "latencyMs": 10,
                "rssiDbm": -60,
            }

            logger.log_packet(packet)
            logger.close()

            with open(logger.filepath, "r", encoding="utf-8") as handle:
                contents = handle.read().splitlines()

            self.assertEqual(contents[0].split(","), CSV_FIELDNAMES)
            self.assertTrue(len(contents) >= 2)
            self.assertIn("READY", contents[1])


if __name__ == "__main__":
    unittest.main()
