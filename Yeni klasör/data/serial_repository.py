import serial

from domain.ports import SerialPortReader


class SerialRepository(SerialPortReader):
    """Repository responsible for reading and parsing data from a serial port."""

    def __init__(self, ser: serial.Serial):
        self.ser = ser

    def read_available(self) -> list[dict]:
        """Read all available lines from serial and return parsed value dicts."""
        results: list[dict] = []
        if not self.ser or not self.ser.is_open:
            return results

        try:
            while self.ser.in_waiting:
                raw = self.ser.readline().decode("utf-8", errors="ignore").strip()
                if not raw:
                    break
                values = self._parse_line(raw)
                if values:
                    results.append(values)
        except serial.SerialException as exc:
            # Surface the exception so callers can handle disconnect/error logic.
            raise exc

        return results

    def _parse_line(self, line: str) -> dict:
        """
        Parse incoming serial data line

        FORMAT 1 - Sensor Status Response:
        STATUS => V:READY, LC:READY, T:ERROR, I:READY, RPM:NO_RESPONSE
        veya
        STATUS | V:READY | LC:READY | T:ERROR | I:READY | RPM:NO_RESPONSE

        FORMAT 2 - Normal Data:
        V=12.34 | Weight(kg)=0.56 | T=25.3 | I=1.2 | RPM=5000 | ...
        """

        # -------- SENSOR STATUS LINE --------
        if line.startswith("STATUS"):
            status = {}

            # "STATUS" kelimesini çıkar
            cleaned = line.replace("STATUS", "", 1).strip()

            # Ayraçları temizle: =>, |, ,
            cleaned = cleaned.replace("=>", "").replace("|", ",")

            # Her parçayı işle
            parts = [p.strip() for p in cleaned.split(",") if p.strip()]

            for part in parts:
                if ":" in part:
                    key, value = part.split(":", 1)
                    key = key.strip()
                    value = value.strip()

                    # Boş değer kontrolü
                    if value and key:
                        status[key] = value

            # En az bir sensör verisi varsa döndür
            if status:
                return {"sensor_status": status}
            else:
                return {}

        # -------- NORMAL DATA LINE --------
        parts = [p.strip() for p in line.split("|")]
        data: dict[str, float] = {}

        def extract_float(text: str):
            if "=" not in text:
                return None
            after = text.split("=", 1)[1].strip()
            if not after:
                return None
            first = after.split()[0]
            try:
                return float(first)
            except ValueError:
                return None

        for part in parts:
            if part.startswith("V="):
                v = extract_float(part)
                if v is not None:
                    data["voltage"] = v
            elif part.startswith("Weight(kg)="):
                w = extract_float(part)
                if w is not None:
                    data["thrust_kgf"] = w
            elif part.startswith("T="):
                t = extract_float(part)
                if t is not None:
                    data["temperature"] = t
            elif part.startswith("I="):
                i = extract_float(part)
                if i is not None:
                    data["current"] = i
            elif part.startswith("RPM="):
                rpm = extract_float(part)
                if rpm is not None:
                    data["rpm"] = rpm
            elif part.startswith("P_elec="):
                p = extract_float(part)
                if p is not None:
                    data["power"] = p
            elif part.startswith("PTEff="):
                eff = extract_float(part)
                if eff is not None:
                    data["pt_eff"] = eff
            elif part.startswith("TPA="):
                tpa = extract_float(part)
                if tpa is not None:
                    data["tpa"] = tpa

        return data