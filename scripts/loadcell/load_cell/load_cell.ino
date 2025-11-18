#include "HX711.h"

// --- HX711 引脚定义 ---
#define LOADCELL_DOUT_PIN  3
#define LOADCELL_SCK_PIN   2

// --- 气压传感器引脚 ---
#define PRESSURE_PIN A0

// --- 物理常量 ---
const double G0 = 9.80665;  // 标准重力加速度 m/s^2

// --- 你的校准参数（来自拟合结果） ---
const float CAL_SCALE  = 761.654602f; // counts per gram
const float CAL_OFFSET = 602400.9f;   // counts

// --- 自动清零参数 ---
const unsigned long WARMUP_MS = 600; // 上电后小等待，滤掉瞬态
const int AUTOZERO_SAMPLES    = 15;  // 自动清零时平均的样本数
const int READ_SAMPLES        = 2;   // 常规输出的平均样本数 (reduced for speed)
const int LOOP_DELAY_MS       = 10;  // 输出频率控制 (reduced for faster sampling)

// --- 创建 HX711 实例 ---
HX711 scale;

// ----- 工具：打印 JSON 中的浮点数（固定小数位） -----
static inline void printFloat(double val, uint8_t digits) {
  Serial.print(val, digits);
}

// ----- 工具：输出一次测量为二进制格式（更快） -----
void emitMeasurementBinary() {
  if (!scale.is_ready()) {
    return; // Skip if not ready
  }

  long raw = scale.read_average(READ_SAMPLES);   // 原始计数
  float weight_g = scale.get_units(READ_SAMPLES); // 克
  float force_N = (float)weight_g / 1000.0 * G0;

  int adc = analogRead(PRESSURE_PIN);
  float voltage = adc * (5.0 / 1023.0);

  // Binary packet format: [0xAA][0x55][raw:4][force_N:4][pressure_v:4][pressure_adc:2][checksum:1]
  // Total: 16 bytes
  Serial.write(0xAA);  // Start marker 1
  Serial.write(0x55);  // Start marker 2
  
  // Send raw (4 bytes, little-endian)
  Serial.write((uint8_t)(raw & 0xFF));
  Serial.write((uint8_t)((raw >> 8) & 0xFF));
  Serial.write((uint8_t)((raw >> 16) & 0xFF));
  Serial.write((uint8_t)((raw >> 24) & 0xFF));
  
  // Send force_N as float (4 bytes)
  uint8_t* force_ptr = (uint8_t*)&force_N;
  Serial.write(force_ptr, 4);
  
  // Send pressure_v as float (4 bytes)
  uint8_t* volt_ptr = (uint8_t*)&voltage;
  Serial.write(volt_ptr, 4);
  
  // Send pressure_adc (2 bytes)
  Serial.write((uint8_t)(adc & 0xFF));
  Serial.write((uint8_t)((adc >> 8) & 0xFF));
  
  // Simple checksum (XOR of all data bytes)
  uint8_t checksum = 0xAA ^ 0x55;
  checksum ^= (raw & 0xFF) ^ ((raw >> 8) & 0xFF) ^ ((raw >> 16) & 0xFF) ^ ((raw >> 24) & 0xFF);
  checksum ^= force_ptr[0] ^ force_ptr[1] ^ force_ptr[2] ^ force_ptr[3];
  checksum ^= volt_ptr[0] ^ volt_ptr[1] ^ volt_ptr[2] ^ volt_ptr[3];
  checksum ^= (adc & 0xFF) ^ ((adc >> 8) & 0xFF);
  Serial.write(checksum);
}

// ----- 工具：输出一次测量为 JSON（保留作为备用） -----
void emitMeasurementJSON() {
  if (!scale.is_ready()) {
    Serial.println("{\"error\":\"hx711_not_ready\"}");
    return;
  }

  long raw = scale.read_average(READ_SAMPLES);   // 原始计数
  float weight_g = scale.get_units(READ_SAMPLES); // 克
  double force_N = (double)weight_g / 1000.0 * G0;

  int adc = analogRead(PRESSURE_PIN);
  double voltage = adc * (5.0 / 1023.0);

  Serial.print('{');
  Serial.print("\"raw\":");          Serial.print(raw);                    Serial.print(',');
  Serial.print("\"weight_g\":");     printFloat(weight_g, 3);              Serial.print(',');
  Serial.print("\"force_N\":");      printFloat(force_N, 5);               Serial.print(',');
  Serial.print("\"pressure_adc\":"); Serial.print(adc);                    Serial.print(',');
  Serial.print("\"pressure_v\":");   printFloat(voltage, 4);               Serial.print(',');
  Serial.print("\"scale\":");        printFloat(scale.get_scale(), 6);     Serial.print(',');
  Serial.print("\"offset\":");       printFloat(scale.get_offset(), 1);
  Serial.println('}');
}

// ----- 自动清零（不改变比例因子） -----
bool autoZeroOnce(unsigned long& duration_ms_out) {
  unsigned long t0 = millis();

  // 简短预热
  delay(WARMUP_MS);

  // 等待 HX711 就绪（最多 1.5s）
  unsigned long waitStart = millis();
  while (!scale.is_ready() && (millis() - waitStart < 1500)) {
    delay(5);
  }
  if (!scale.is_ready()) {
    // 失败事件（仍继续运行）
    Serial.println("{\"event\":\"auto_zero_failed\",\"reason\":\"hx711_not_ready\"}");
    duration_ms_out = millis() - t0;
    return false;
  }

  long rawNow = scale.read_average(AUTOZERO_SAMPLES);
  scale.set_offset(rawNow);

  duration_ms_out = millis() - t0;

  Serial.print("{\"event\":\"auto_zero_complete\",\"new_offset\":");
  Serial.print(rawNow);
  Serial.print(",\"samples\":");
  Serial.print(AUTOZERO_SAMPLES);
  Serial.print(",\"duration_ms\":");
  Serial.print(duration_ms_out);
  Serial.println("}");
  return true;
}

void setup() {
  Serial.begin(115200);
  while (!Serial) { /* for native USB boards */ }

  // 初始化 HX711 并设置你的校准参数
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  scale.set_scale(CAL_SCALE);
  scale.set_offset(CAL_OFFSET);

  // 上电就绪事件（JSON）
  Serial.print("{\"event\":\"ready\",\"scale\":");
  Serial.print(CAL_SCALE, 6);
  Serial.print(",\"offset\":");
  Serial.print(CAL_OFFSET, 1);
  Serial.println("}");

  // —— 启动时自动置零（仅一次） ——
  unsigned long dur = 0;
  autoZeroOnce(dur);
}

void loop() {
  // 串口命令：set_zero -> 使用当前读数作为新零点
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    cmd.toLowerCase();

    if (cmd == "set_zero") {
      if (!scale.is_ready()) {
        Serial.println("{\"error\":\"hx711_not_ready_for_tare\"}");
      } else {
        long rawNow = scale.read_average(AUTOZERO_SAMPLES);
        scale.set_offset(rawNow);
        Serial.print("{\"event\":\"set_zero\",\"new_offset\":");
        Serial.print(rawNow);
        Serial.println("}");
      }
    } else if (cmd.length() > 0) {
      // 保持 JSON 风格
      cmd.replace("\\", "\\\\");
      cmd.replace("\"", "\\\"");
      Serial.print("{\"event\":\"unknown_cmd\",\"cmd\":\"");
      Serial.print(cmd);
      Serial.println("\"}");
    }
  }

  // 输出一帧测量 JSON
  emitMeasurementJSON();

  delay(LOOP_DELAY_MS);
}
