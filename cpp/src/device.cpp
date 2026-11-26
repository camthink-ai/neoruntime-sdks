// device.cpp — DeviceClient implementation. See device.hpp.
//
// Proto divergence notes (device.py bugs the C++ port corrects):
//   * set_ir_led   — proto SetIrLed takes LightLevelRequest{level}; device.py
//     sends LightSwitchRequest{on}, which only "works" because bool field 1
//     and uint32 field 1 share the wire format. C++ stubs are strongly typed,
//     so we expose set_ir_led(uint32_t level) as the proto defines.
//   * control_iris — proto IrisRequest has int32 speed; device.py passes a
//     non-existent `open` kwarg (would raise at runtime in Python). We expose
//     control_iris(int32_t speed).
//   * DeviceStatus — proto field 41 is ir_led_level (uint32); device.py reads
//     the non-existent ir_led_on. We expose ir_led_level.
#include "neoruntime_ipc_sdk/device.hpp"

#include <grpcpp/grpcpp.h>

#include <chrono>
#include <stdexcept>
#include <thread>
#include <utility>

#include "neoruntime_ipc_sdk/config.hpp"

#include "detail/device_codec.hpp"
#include "detail/grpc_channel.hpp"
#include "detail/transport.hpp"
#include "device-control/device.grpc.pb.h"
#include "device-control/device.pb.h"

namespace neoruntime_ipc_sdk {

namespace pb = aipc::device;

// ---------------------------------------------------------------------------
// DeviceEventStream
// ---------------------------------------------------------------------------
struct DeviceEventStream::Impl {
    grpc::ClientContext ctx;
    std::unique_ptr<grpc::ClientReader<pb::DeviceEvent>> reader;
};

DeviceEventStream::DeviceEventStream() : impl_(std::make_unique<Impl>()) {}
DeviceEventStream::~DeviceEventStream() = default;
DeviceEventStream::DeviceEventStream(DeviceEventStream&&) noexcept = default;
DeviceEventStream& DeviceEventStream::operator=(DeviceEventStream&&) noexcept = default;

std::optional<DeviceEvent> DeviceEventStream::next() {
    if (!impl_->reader) return std::nullopt;
    pb::DeviceEvent msg;
    if (!impl_->reader->Read(&msg)) return std::nullopt;

    DeviceEvent ev{};
    ev.type = static_cast<DeviceEvent::Type>(msg.type());
    ev.timestamp_ns = msg.timestamp_ns();
    switch (msg.data_case()) {
        case pb::DeviceEvent::kGpioState:
            ev.gpio_pin = msg.gpio_state().pin();
            ev.gpio_value = msg.gpio_state().value();
            break;
        case pb::DeviceEvent::kLightSensorValue:
            ev.light_sensor_value = msg.light_sensor_value();
            break;
        case pb::DeviceEvent::kTemperature:
            ev.temperature = msg.temperature();
            break;
        default:
            break;
    }
    return ev;
}

// ---------------------------------------------------------------------------
// Rs485RxEventStream
// ---------------------------------------------------------------------------
struct Rs485RxEventStream::Impl {
    grpc::ClientContext ctx;
    std::unique_ptr<grpc::ClientReader<pb::Rs485RxEvent>> reader;
};

Rs485RxEventStream::Rs485RxEventStream() : impl_(std::make_unique<Impl>()) {}
Rs485RxEventStream::~Rs485RxEventStream() = default;
Rs485RxEventStream::Rs485RxEventStream(Rs485RxEventStream&&) noexcept = default;
Rs485RxEventStream& Rs485RxEventStream::operator=(Rs485RxEventStream&&) noexcept = default;

std::optional<Rs485RxEvent> Rs485RxEventStream::next() {
    if (!impl_->reader) return std::nullopt;
    pb::Rs485RxEvent msg;
    if (!impl_->reader->Read(&msg)) return std::nullopt;

    Rs485RxEvent ev{};
    ev.data = msg.data();
    ev.timestamp_ns = msg.timestamp_ns();
    return ev;
}

// ---------------------------------------------------------------------------
// DeviceClient
// ---------------------------------------------------------------------------
struct DeviceClient::Impl : detail::GrpcClientBase<pb::DeviceControl> {
    explicit Impl(std::string endpoint)
        : GrpcClientBase(std::move(endpoint)) {}

    // PTZ helpers (kept here so proto enum types never reach device.hpp).
    void pan(pb::PanDirection direction, std::uint32_t speed) {
        grpc::ClientContext ctx;
        pb::PanRequest req;
        req.set_direction(direction);
        req.set_speed(speed);
        pb::Status resp;
        detail::check_grpc(stub().Pan(&ctx, req, &resp), "Pan");
        detail::require_success(resp.success(), resp.message(), "Pan");
    }
    void tilt(pb::TiltDirection direction, std::uint32_t speed) {
        grpc::ClientContext ctx;
        pb::TiltRequest req;
        req.set_direction(direction);
        req.set_speed(speed);
        pb::Status resp;
        detail::check_grpc(stub().Tilt(&ctx, req, &resp), "Tilt");
        detail::require_success(resp.success(), resp.message(), "Tilt");
    }
};

DeviceClient::DeviceClient(std::string endpoint)
    : impl_(std::make_unique<Impl>(
          endpoint.empty() ? Config::get_device_control_endpoint() : std::move(endpoint))) {}

DeviceClient::~DeviceClient() = default;
DeviceClient::DeviceClient(DeviceClient&&) noexcept = default;
DeviceClient& DeviceClient::operator=(DeviceClient&&) noexcept = default;

void DeviceClient::connect() { impl_->connect(); }

void DeviceClient::close() { impl_->close(); }

bool DeviceClient::connected() const noexcept { return impl_->connected(); }

// --- Light ---
void DeviceClient::set_white_light(std::uint32_t level) {
    grpc::ClientContext ctx;
    pb::LightLevelRequest req;
    req.set_level(level);
    pb::Status resp;
    detail::check_grpc(impl_->stub().SetWhiteLight(&ctx, req, &resp), "SetWhiteLight");
    detail::require_success(resp.success(), resp.message(), "SetWhiteLight");
}

void DeviceClient::set_ir_led(std::uint32_t level) {
    grpc::ClientContext ctx;
    pb::LightLevelRequest req;
    req.set_level(level);
    pb::Status resp;
    detail::check_grpc(impl_->stub().SetIrLed(&ctx, req, &resp), "SetIrLed");
    detail::require_success(resp.success(), resp.message(), "SetIrLed");
}

void DeviceClient::set_ircut(IrCutMode mode) {
    grpc::ClientContext ctx;
    pb::IrCutRequest req;
    req.set_mode(static_cast<pb::IrCutMode>(mode));
    pb::Status resp;
    detail::check_grpc(impl_->stub().SetIrCut(&ctx, req, &resp), "SetIrCut");
    detail::require_success(resp.success(), resp.message(), "SetIrCut");
}

// --- PTZ ---
void DeviceClient::pan_left(std::uint32_t speed) {
    impl_->pan(pb::PAN_LEFT, speed);
}
void DeviceClient::pan_right(std::uint32_t speed) {
    impl_->pan(pb::PAN_RIGHT, speed);
}
void DeviceClient::pan_stop() {
    impl_->pan(pb::PAN_STOP, 0);
}

void DeviceClient::tilt_up(std::uint32_t speed) {
    impl_->tilt(pb::TILT_UP, speed);
}
void DeviceClient::tilt_down(std::uint32_t speed) {
    impl_->tilt(pb::TILT_DOWN, speed);
}
void DeviceClient::tilt_stop() {
    impl_->tilt(pb::TILT_STOP, 0);
}

void DeviceClient::ptz_stop() {
    grpc::ClientContext ctx;
    pb::PTZStopRequest req;
    pb::Status resp;
    detail::check_grpc(impl_->stub().PTZStop(&ctx, req, &resp), "PTZStop");
    detail::require_success(resp.success(), resp.message(), "PTZStop");
}

void DeviceClient::save_preset(std::uint32_t preset_id) {
    grpc::ClientContext ctx;
    pb::PresetRequest req;
    req.set_preset_id(preset_id);
    pb::Status resp;
    detail::check_grpc(impl_->stub().SavePreset(&ctx, req, &resp), "SavePreset");
    detail::require_success(resp.success(), resp.message(), "SavePreset");
}

void DeviceClient::call_preset(std::uint32_t preset_id) {
    grpc::ClientContext ctx;
    pb::PresetRequest req;
    req.set_preset_id(preset_id);
    pb::Status resp;
    detail::check_grpc(impl_->stub().CallPreset(&ctx, req, &resp), "CallPreset");
    detail::require_success(resp.success(), resp.message(), "CallPreset");
}

// --- Lens ---
void DeviceClient::zoom_in(std::int32_t speed) { zoom(speed); }
void DeviceClient::zoom_out(std::int32_t speed) { zoom(-speed); }
void DeviceClient::zoom_stop() { zoom(0); }

void DeviceClient::zoom(std::int32_t speed) {
    grpc::ClientContext ctx;
    pb::ZoomRequest req;
    req.set_speed(speed);
    pb::Status resp;
    detail::check_grpc(impl_->stub().Zoom(&ctx, req, &resp), "Zoom");
    detail::require_success(resp.success(), resp.message(), "Zoom");
}

void DeviceClient::set_zoom_level(float level) {
    grpc::ClientContext ctx;
    pb::ZoomLevelRequest req;
    req.set_level(level);
    pb::Status resp;
    detail::check_grpc(impl_->stub().SetZoomLevel(&ctx, req, &resp), "SetZoomLevel");
    detail::require_success(resp.success(), resp.message(), "SetZoomLevel");
}

void DeviceClient::focus_in(std::int32_t speed) { focus(speed); }
void DeviceClient::focus_out(std::int32_t speed) { focus(-speed); }
void DeviceClient::focus_stop() { focus(0); }

void DeviceClient::focus(std::int32_t speed) {
    grpc::ClientContext ctx;
    pb::FocusRequest req;
    req.set_speed(speed);
    pb::Status resp;
    detail::check_grpc(impl_->stub().Focus(&ctx, req, &resp), "Focus");
    detail::require_success(resp.success(), resp.message(), "Focus");
}

void DeviceClient::focus_auto(bool enable) {
    grpc::ClientContext ctx;
    pb::AutofocusRequest req;
    req.set_enable(enable);
    pb::Status resp;
    detail::check_grpc(impl_->stub().SetAutofocus(&ctx, req, &resp), "SetAutofocus");
    detail::require_success(resp.success(), resp.message(), "SetAutofocus");
}

void DeviceClient::set_focus_level(float level) {
    grpc::ClientContext ctx;
    pb::FocusLevelRequest req;
    req.set_level(level);
    pb::Status resp;
    detail::check_grpc(impl_->stub().SetFocusLevel(&ctx, req, &resp), "SetFocusLevel");
    detail::require_success(resp.success(), resp.message(), "SetFocusLevel");
}

LensStatus DeviceClient::get_lens_status() {
    grpc::ClientContext ctx;
    pb::Empty req;
    pb::LensStatusResponse resp;
    detail::check_grpc(impl_->stub().GetLensStatus(&ctx, req, &resp), "GetLensStatus");

    auto to_limit = [](const pb::LensLimit& l) {
        return LensLimit{l.min_pos(), l.max_pos()};
    };
    LensStatus out{};
    out.zoom_state = resp.zoom_state();
    out.focus_state = resp.focus_state();
    out.zoom_rz_done = resp.zoom_rz_done();
    out.focus_rz_done = resp.focus_rz_done();
    out.zoom_pos = resp.zoom_pos();
    out.focus_pos = resp.focus_pos();
    out.iris_adc = resp.iris_adc();
    out.autofocus_enabled = resp.autofocus_enabled();
    out.zoom_limit = to_limit(resp.zoom_limit());
    out.focus_limit = to_limit(resp.focus_limit());
    return out;
}

void DeviceClient::set_lens_limits(std::optional<LensLimit> zoom_limit,
                                   std::optional<LensLimit> focus_limit) {
    grpc::ClientContext ctx;
    pb::LensLimitsRequest req;
    if (zoom_limit) {
        req.mutable_zoom_limit()->set_min_pos(zoom_limit->min_pos);
        req.mutable_zoom_limit()->set_max_pos(zoom_limit->max_pos);
    }
    if (focus_limit) {
        req.mutable_focus_limit()->set_min_pos(focus_limit->min_pos);
        req.mutable_focus_limit()->set_max_pos(focus_limit->max_pos);
    }
    pb::Status resp;
    detail::check_grpc(impl_->stub().SetLensLimits(&ctx, req, &resp), "SetLensLimits");
    detail::require_success(resp.success(), resp.message(), "SetLensLimits");
}

void DeviceClient::oneshot_autofocus(double timeout_seconds) {

    // 1. Enable continuous AF.
    {
        grpc::ClientContext ctx;
        pb::AutofocusRequest req;
        req.set_enable(true);
        pb::Status resp;
        detail::check_grpc(impl_->stub().SetAutofocus(&ctx, req, &resp), "SetAutofocus");
        detail::require_success(resp.success(), resp.message(), "SetAutofocus");
    }

    // 2. Wait for the focus motor to settle (match backend's 1500ms initial delay).
    constexpr auto kInitialWait = std::chrono::milliseconds(1500);
    constexpr auto kPollInterval = std::chrono::milliseconds(200);
    std::this_thread::sleep_for(kInitialWait);

    const auto deadline = std::chrono::steady_clock::now()
                          + std::chrono::duration_cast<std::chrono::milliseconds>(
                                std::chrono::duration<double>(timeout_seconds));
    bool settled = false;
    while (std::chrono::steady_clock::now() < deadline) {
        grpc::ClientContext ctx;
        pb::Empty req;
        pb::LensStatusResponse st;
        detail::check_grpc(impl_->stub().GetLensStatus(&ctx, req, &st), "GetLensStatus");
        const auto focus_state = st.focus_state();
        if (focus_state == 1 || focus_state == 0) {  // Stopped or NoCfg
            settled = true;
            break;
        }
        if (focus_state == 4) {  // Error
            throw std::runtime_error("Autofocus failed: focus motor error");
        }
        std::this_thread::sleep_for(kPollInterval);
    }

    // 3. Disable continuous AF regardless of outcome.
    {
        grpc::ClientContext ctx;
        pb::AutofocusRequest req;
        req.set_enable(false);
        pb::Status ignored;  // best-effort disable; errors here are not fatal
        impl_->stub().SetAutofocus(&ctx, req, &ignored);
    }

    if (!settled) {
        throw std::runtime_error(
            "Autofocus did not converge within "
            + std::to_string(timeout_seconds) + "s");
    }
}

void DeviceClient::lens_reset_zero(bool zoom, bool focus) {
    grpc::ClientContext ctx;
    pb::LensResetRequest req;
    req.set_zoom(zoom);
    req.set_focus(focus);
    pb::Status resp;
    detail::check_grpc(impl_->stub().LensResetZero(&ctx, req, &resp), "LensResetZero");
    detail::require_success(resp.success(), resp.message(), "LensResetZero");
}

void DeviceClient::control_iris(std::int32_t speed) {
    grpc::ClientContext ctx;
    pb::IrisRequest req;
    req.set_speed(speed);
    pb::Status resp;
    detail::check_grpc(impl_->stub().ControlIris(&ctx, req, &resp), "ControlIris");
    detail::require_success(resp.success(), resp.message(), "ControlIris");
}

void DeviceClient::set_iris_target(std::uint32_t target) {
    grpc::ClientContext ctx;
    pb::IrisTargetRequest req;
    req.set_target(target);
    pb::Status resp;
    detail::check_grpc(impl_->stub().SetIrisTarget(&ctx, req, &resp), "SetIrisTarget");
    detail::require_success(resp.success(), resp.message(), "SetIrisTarget");
}

void DeviceClient::lens_init() {
    grpc::ClientContext ctx;
    pb::LensInitRequest req;
    pb::Status resp;
    detail::check_grpc(impl_->stub().LensInit(&ctx, req, &resp), "LensInit");
    detail::require_success(resp.success(), resp.message(), "LensInit");
}

void DeviceClient::lens_goto_ratio_distance(float zoom_ratio, float focus_distance_m) {
    grpc::ClientContext ctx;
    pb::GotoRatioDistanceRequest req;
    req.set_zoom_ratio(zoom_ratio);
    req.set_focus_distance_m(focus_distance_m);
    pb::Status resp;
    detail::check_grpc(impl_->stub().LensGotoRatioDistance(&ctx, req, &resp),
                       "LensGotoRatioDistance");
    detail::require_success(resp.success(), resp.message(), "LensGotoRatioDistance");
}

// --- Alarm I/O ---
void DeviceClient::set_wiegand_out(std::uint32_t channel, bool enable) {
    grpc::ClientContext ctx;
    pb::AlarmChannelRequest req;
    req.set_channel(channel);
    req.set_enable(enable);
    pb::AlarmChannelStatus resp;
    detail::check_grpc(impl_->stub().SetWiegandOut(&ctx, req, &resp), "SetWiegandOut");
    detail::require_success(resp.success(), resp.message(), "SetWiegandOut");
}

bool DeviceClient::get_wiegand_out(std::uint32_t channel) {
    grpc::ClientContext ctx;
    pb::AlarmChannelRequest req;
    req.set_channel(channel);
    pb::AlarmChannelStatus resp;
    detail::check_grpc(impl_->stub().GetWiegandOut(&ctx, req, &resp), "GetWiegandOut");
    detail::require_success(resp.success(), resp.message(), "GetWiegandOut");
    return resp.enabled();
}

// --- RS485 ---
void DeviceClient::rs485_init(std::uint32_t baudrate, std::string config) {
    grpc::ClientContext ctx;
    pb::Rs485InitRequest req;
    req.set_baudrate(baudrate);
    req.set_config(std::move(config));
    pb::Status resp;
    detail::check_grpc(impl_->stub().Rs485Init(&ctx, req, &resp), "Rs485Init");
    detail::require_success(resp.success(), resp.message(), "Rs485Init");
}

void DeviceClient::rs485_deinit() {
    grpc::ClientContext ctx;
    pb::Empty req;
    pb::Status resp;
    detail::check_grpc(impl_->stub().Rs485Deinit(&ctx, req, &resp), "Rs485Deinit");
    detail::require_success(resp.success(), resp.message(), "Rs485Deinit");
}

void DeviceClient::rs485_tx(std::string_view data) {
    grpc::ClientContext ctx;
    pb::Rs485TxRequest req;
    req.set_data(data.data(), data.size());
    pb::Status resp;
    detail::check_grpc(impl_->stub().Rs485Tx(&ctx, req, &resp), "Rs485Tx");
    detail::require_success(resp.success(), resp.message(), "Rs485Tx");
}

Rs485RxEventStream DeviceClient::subscribe_rs485_rx(std::uint32_t queue_size,
                                                    bool drop_old) {
    Rs485RxEventStream stream;
    pb::Rs485SubscribeRequest req;
    req.set_queue_size(queue_size);
    req.set_drop_old(drop_old);
    stream.impl_->reader =
        impl_->stub().SubscribeRs485Rx(&stream.impl_->ctx, req);
    return stream;
}

// --- GPIO ---
void DeviceClient::gpio_set(std::uint32_t pin, bool value) {
    grpc::ClientContext ctx;
    pb::GPIOWriteRequest req;
    req.set_pin(pin);
    req.set_value(value);
    pb::Status resp;
    detail::check_grpc(impl_->stub().GPIOWrite(&ctx, req, &resp), "GPIOWrite");
    detail::require_success(resp.success(), resp.message(), "GPIOWrite");
}

bool DeviceClient::gpio_get(std::uint32_t pin) {
    grpc::ClientContext ctx;
    pb::GPIOReadRequest req;
    req.set_pin(pin);
    pb::GPIOReadResponse resp;
    detail::check_grpc(impl_->stub().GPIORead(&ctx, req, &resp), "GPIORead");
    detail::require_success(resp.status().success(), resp.status().message(), "GPIORead");
    return resp.value();
}

// --- Status / events ---
DeviceStatus DeviceClient::get_device_status() {
    grpc::ClientContext ctx;
    pb::Empty req;
    pb::DeviceStatus resp;
    detail::check_grpc(impl_->stub().GetDeviceStatus(&ctx, req, &resp), "GetDeviceStatus");

    DeviceStatus out{};
    out.soc_temp_c = resp.soc_temp_c();
    out.mcu_temp_c = resp.mcu_temp_c();
    out.light_sensor = resp.light_sensor();
    out.ptz_pan_pos = resp.ptz_pan_pos();
    out.ptz_tilt_pos = resp.ptz_tilt_pos();
    out.zoom_pos = resp.zoom_pos();
    out.focus_pos = resp.focus_pos();
    out.autofocus_enabled = resp.autofocus_enabled();
    out.ircut_mode = static_cast<IrCutMode>(resp.ircut_mode());
    out.white_light_level = resp.white_light_level();
    out.ir_led_level = resp.ir_led_level();
    out.mcu_version = resp.mcu_version();
    out.mcu_uptime_ms = resp.mcu_uptime_ms();
    return out;
}

DeviceEventStream DeviceClient::subscribe_events() {
    DeviceEventStream stream;
    pb::Empty req;
    stream.impl_->reader = impl_->stub().SubscribeEvents(&stream.impl_->ctx, req);
    return stream;
}

// --- Native autofocus jobs (device.py 0.8) ---
AfJob DeviceClient::start_oneshot_af() {
    grpc::ClientContext ctx;
    pb::AfJobResponse resp;
    detail::check_grpc(impl_->stub().StartOneShotAf(&ctx, pb::Empty{}, &resp),
                       "StartOneShotAf");
    AfJob job = detail::device_codec::af_job_from(resp);
    if (!job.accepted) {
        throw detail::RpcError("StartOneShotAf rejected: " + job.message);
    }
    return job;
}

AfJob DeviceClient::start_zoom_follow(float ratio) {
    grpc::ClientContext ctx;
    pb::ZoomFollowRequest req;
    req.set_ratio(ratio);
    pb::AfJobResponse resp;
    detail::check_grpc(impl_->stub().StartZoomFollow(&ctx, req, &resp), "StartZoomFollow");
    AfJob job = detail::device_codec::af_job_from(resp);
    if (!job.accepted) {
        throw detail::RpcError("StartZoomFollow rejected: " + job.message);
    }
    return job;
}

AfStatus DeviceClient::get_autofocus_status() {
    grpc::ClientContext ctx;
    pb::AfStatusResponse resp;
    detail::check_grpc(impl_->stub().GetAutofocusStatus(&ctx, pb::Empty{}, &resp),
                       "GetAutofocusStatus");
    return detail::device_codec::af_status_from(resp);
}

void DeviceClient::cancel_autofocus(std::uint64_t job_id) {
    grpc::ClientContext ctx;
    pb::AfJobRequest req;
    req.set_job_id(job_id);
    pb::Status resp;
    detail::check_grpc(impl_->stub().CancelAutofocus(&ctx, req, &resp), "CancelAutofocus");
    detail::require_success(resp.success(), resp.message(), "CancelAutofocus");
}

void DeviceClient::set_af_windows(bool enabled, const std::vector<AfWindow>& windows,
                                  const std::string& stream_id) {
    // >3 windows throws std::invalid_argument inside the codec, before any
    // RPC — device.py raises the same ValueError client-side.
    grpc::ClientContext ctx;
    pb::Status resp;
    detail::check_grpc(impl_->stub().SetAfWindows(
                           &ctx, detail::device_codec::af_windows_request(enabled, windows,
                                                                         stream_id),
                           &resp),
                       "SetAfWindows");
    detail::require_success(resp.success(), resp.message(), "SetAfWindows");
}

AfMeasurement DeviceClient::get_af_measurement() {
    grpc::ClientContext ctx;
    pb::AfMeasurementResponse resp;
    detail::check_grpc(impl_->stub().GetAfMeasurement(&ctx, pb::Empty{}, &resp),
                       "GetAfMeasurement");
    return detail::device_codec::af_measurement_from(resp);
}

}  // namespace neoruntime_ipc_sdk
