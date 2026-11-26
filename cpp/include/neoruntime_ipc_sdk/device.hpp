// device.hpp — DeviceControl gRPC client. 1:1 port of device.py.
//
// Transport: sync gRPC stubs over UDS (the default endpoint). The Python SDK
// relies on a wire-format coincidence for set_ir_led / control_iris that the
// strongly-typed C++ stubs cannot reproduce; those two methods therefore
// follow the .proto signatures (SetIrLed(LightLevelRequest), IrisRequest.speed)
// rather than device.py's buggy Python wrappers. See device.cpp notes.
#pragma once

#include <cstdint>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace neoruntime_ipc_sdk {

// IR-cut filter mode. Values match aipc.device.IrCutMode (IRCUT_AUTO/DAY/NIGHT).
enum class IrCutMode : int {
    Auto  = 0,
    Day   = 1,
    Night = 2,
};

struct LensLimit {
    std::int32_t min_pos = 0;
    std::int32_t max_pos = 0;
};

struct LensStatus {
    std::uint32_t zoom_state = 0;   // motor: 0=NoCfg 1=Stopped 2=Running 3=ResetZero 4=Error
    std::uint32_t focus_state = 0;
    bool zoom_rz_done = false;
    bool focus_rz_done = false;
    std::int32_t zoom_pos = 0;
    std::int32_t focus_pos = 0;
    std::uint32_t iris_adc = 0;
    bool autofocus_enabled = false;
    LensLimit zoom_limit{};
    LensLimit focus_limit{};
};

struct DeviceStatus {
    float soc_temp_c = 0.0f;
    float mcu_temp_c = 0.0f;
    std::uint32_t light_sensor = 0;
    std::int32_t ptz_pan_pos = 0;
    std::int32_t ptz_tilt_pos = 0;
    std::int32_t zoom_pos = 0;
    std::int32_t focus_pos = 0;
    bool autofocus_enabled = false;
    IrCutMode ircut_mode = IrCutMode::Auto;
    std::uint32_t white_light_level = 0;
    std::uint32_t ir_led_level = 0;   // proto field 41 (device.py wrongly read ir_led_on)
    std::string mcu_version;
    std::uint64_t mcu_uptime_ms = 0;
};

struct DeviceEvent {
    enum class Type : int {
        GpioChange        = 0,
        LightSensorChange = 1,
        TemperatureAlert  = 2,
        PtzMoveComplete   = 3,
        FocusComplete     = 4,
    };
    Type type = Type::GpioChange;
    std::uint64_t timestamp_ns = 0;
    // Payload — only the field(s) relevant to `type` are populated.
    std::uint32_t gpio_pin = 0;
    bool gpio_value = false;
    std::uint32_t light_sensor_value = 0;
    float temperature = 0.0f;
};

// One RS-485 frame received on the bus (idle-delimited, <= 512 bytes).
// timestamp_ns is the device-side receive time (host clock), not the MCU
// capture time.
struct Rs485RxEvent {
    std::string data;              // protobuf bytes <-> std::string (rs485_tx style)
    std::uint64_t timestamp_ns = 0;
};

// ---- Native autofocus job API (device.py 0.8, StartOneShotAf family) -----------

// Result of starting an autofocus job.
struct AfJob {
    bool accepted = false;
    std::uint64_t job_id = 0;
    std::string message;
};

// Snapshot of the autofocus engine. `operation` is "oneshot" / "zoom_follow";
// `state` is "idle" / "running" / "done" / "failed" / "cancelled". The
// ratio pair distinguishes what the app asked for from what the lens could
// actually hold (optical limits); estimated_distance_m is 0 when unknown.
struct AfStatus {
    std::uint64_t job_id = 0;
    std::string operation;
    std::string state;
    double progress = 0.0;          // [0..1]
    bool busy = false;
    bool anchor_valid = false;
    float requested_ratio = 0.0f;
    float effective_ratio = 0.0f;
    std::int32_t zoom_pos = 0;
    std::int32_t focus_pos = 0;
    std::int32_t best_focus = 0;
    double metric = 0.0;            // focus sharpness metric
    double confidence = 0.0;
    double reproducibility = 0.0;
    float estimated_distance_m = 0.0f;
    std::uint64_t elapsed_ms = 0;
    std::int32_t error_code = 0;
    std::string message;
};

// Latest per-window focus telemetry (pairs with set_af_windows).
struct AfMeasurement {
    std::vector<std::uint32_t> focus_energy;  // higher = sharper at peak focus
    std::vector<std::uint32_t> mean_luma;     // mean brightness per window
    std::uint64_t frame_id = 0;
};

// Pixel rectangle restricting the region the AF metric is computed on.
struct AfWindow {
    std::int32_t x = 0;
    std::int32_t y = 0;
    std::int32_t w = 0;
    std::int32_t h = 0;
};

// Pull-based equivalent of Python's `for ev in dev.subscribe_events():` generator.
// Must not outlive the DeviceClient that produced it (it borrows the channel).
class DeviceEventStream {
public:
    ~DeviceEventStream();
    DeviceEventStream(DeviceEventStream&&) noexcept;
    DeviceEventStream& operator=(DeviceEventStream&&) noexcept;
    DeviceEventStream(const DeviceEventStream&) = delete;
    DeviceEventStream& operator=(const DeviceEventStream&) = delete;

    // Next event, or std::nullopt when the stream ends (server closed / broken).
    std::optional<DeviceEvent> next();

private:
    DeviceEventStream();
    struct Impl;
    std::unique_ptr<Impl> impl_;
    friend class DeviceClient;
};

// Pull-based RS-485 RX frame stream (same lifetime contract as
// DeviceEventStream: must not outlive the producing DeviceClient).
class Rs485RxEventStream {
public:
    ~Rs485RxEventStream();
    Rs485RxEventStream(Rs485RxEventStream&&) noexcept;
    Rs485RxEventStream& operator=(Rs485RxEventStream&&) noexcept;
    Rs485RxEventStream(const Rs485RxEventStream&) = delete;
    Rs485RxEventStream& operator=(const Rs485RxEventStream&) = delete;

    // Next frame, or std::nullopt when the stream ends (server closed /
    // broken — e.g. old firmware without SubscribeRs485Rx).
    std::optional<Rs485RxEvent> next();

private:
    Rs485RxEventStream();
    struct Impl;
    std::unique_ptr<Impl> impl_;
    friend class DeviceClient;
};

class DeviceClient {
public:
    // Empty endpoint => Config::get_device_control_endpoint().
    explicit DeviceClient(std::string endpoint = "");
    ~DeviceClient();
    DeviceClient(const DeviceClient&) = delete;
    DeviceClient& operator=(const DeviceClient&) = delete;
    DeviceClient(DeviceClient&&) noexcept;
    DeviceClient& operator=(DeviceClient&&) noexcept;

    void connect();
    void close();
    bool connected() const noexcept;

    // ---- Light control ----
    void set_white_light(std::uint32_t level);
    void set_ir_led(std::uint32_t level);        // proto: SetIrLed(LightLevelRequest)
    void set_ircut(IrCutMode mode);

    // ---- PTZ ----
    void pan_left(std::uint32_t speed = 50);
    void pan_right(std::uint32_t speed = 50);
    void pan_stop();
    void tilt_up(std::uint32_t speed = 50);
    void tilt_down(std::uint32_t speed = 50);
    void tilt_stop();
    void ptz_stop();
    void save_preset(std::uint32_t preset_id);
    void call_preset(std::uint32_t preset_id);

    // ---- Lens ----
    void zoom_in(std::int32_t speed = 50);
    void zoom_out(std::int32_t speed = 50);
    void zoom_stop();
    void zoom(std::int32_t speed);
    void set_zoom_level(float level);
    void focus_in(std::int32_t speed = 50);
    void focus_out(std::int32_t speed = 50);
    void focus_stop();
    void focus(std::int32_t speed);
    void focus_auto(bool enable = true);
    void set_focus_level(float level);
    LensStatus get_lens_status();
    void set_lens_limits(std::optional<LensLimit> zoom_limit = std::nullopt,
                         std::optional<LensLimit> focus_limit = std::nullopt);
    void oneshot_autofocus(double timeout_seconds = 20.0);
    void lens_reset_zero(bool zoom = true, bool focus = true);
    void control_iris(std::int32_t speed);        // proto: IrisRequest{int32 speed}
    void set_iris_target(std::uint32_t target);
    void lens_init();
    void lens_goto_ratio_distance(float zoom_ratio, float focus_distance_m);

    // ---- Native autofocus jobs (StartOneShotAf family) ----
    // Unlike oneshot_autofocus (a blocking composite over the legacy
    // SetAutofocus RPC), these return at once; poll get_autofocus_status()
    // for convergence. Rejections surface as detail::RpcError
    // ("StartOneShotAf rejected: <daemon message>").
    AfJob start_oneshot_af();
    // Continuous autofocus locked to a zoom ratio (e.g. 1.5).
    AfJob start_zoom_follow(float ratio);
    AfStatus get_autofocus_status();
    // job_id 0 (default) cancels the active job.
    void cancel_autofocus(std::uint64_t job_id = 0);
    // 1-3 pixel rectangles restricting the AF metric region; more than 3
    // throws std::invalid_argument client-side.
    void set_af_windows(bool enabled, const std::vector<AfWindow>& windows,
                        const std::string& stream_id = "main");
    AfMeasurement get_af_measurement();

    // ---- Alarm I/O ----
    void set_wiegand_out(std::uint32_t channel, bool enable);
    bool get_wiegand_out(std::uint32_t channel);

    // ---- RS485 ----
    void rs485_init(std::uint32_t baudrate, std::string config = "");
    void rs485_deinit();
    void rs485_tx(std::string_view data);
    // Stream RS-485 RX frames (one event per bus frame). Valid before
    // rs485_init as well — the stream stays silent until the device's
    // driver produces frames. queue_size 0 selects the default (16), values
    // above 128 are capped at 128; drop_old = keep newest frames on overflow
    // (else keep order).
    Rs485RxEventStream subscribe_rs485_rx(std::uint32_t queue_size = 16,
                                          bool drop_old = true);

    // ---- GPIO ----
    void gpio_set(std::uint32_t pin, bool value);
    bool gpio_get(std::uint32_t pin);

    // ---- Status / events ----
    DeviceStatus get_device_status();
    DeviceEventStream subscribe_events();

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

}  // namespace neoruntime_ipc_sdk
