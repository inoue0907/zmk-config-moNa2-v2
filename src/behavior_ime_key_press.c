/*
 * SPDX-License-Identifier: MIT
 *
 * &ime_kp <keycode>
 *   IME が ON だと判断しているときだけ keycode を送る。OFF のときは何もしない。
 *
 * IME の状態は、キーボードから出た LANGUAGE_1（かな = IME ON）/
 * LANGUAGE_2（英数 = IME OFF）の押下を見て覚える。起動直後は OFF 扱い。
 * マウスなど、キーボード以外で IME を切り替えると実際の状態とずれる。
 * ずれた場合は、かな / 英数キーを 1 回押せば元に戻る。
 */

#define DT_DRV_COMPAT zmk_behavior_ime_key_press

#include <zephyr/device.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <drivers/behavior.h>

#include <zmk/behavior.h>
#include <zmk/event_manager.h>
#include <zmk/events/keycode_state_changed.h>
#include <dt-bindings/zmk/hid_usage.h>
#include <dt-bindings/zmk/hid_usage_pages.h>

LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

static bool ime_on = false;

/* ---- IME 状態のトラッキング ---- */

static int ime_state_listener(const zmk_event_t *eh) {
    const struct zmk_keycode_state_changed *ev = as_zmk_keycode_state_changed(eh);

    if (ev == NULL || !ev->state || ev->usage_page != HID_USAGE_KEY) {
        return ZMK_EV_EVENT_BUBBLE;
    }

    if (ev->keycode == HID_USAGE_KEY_KEYBOARD_LANG1) {
        ime_on = true;
        LOG_DBG("IME state: on");
    } else if (ev->keycode == HID_USAGE_KEY_KEYBOARD_LANG2) {
        ime_on = false;
        LOG_DBG("IME state: off");
    }

    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(ime_state, ime_state_listener);
ZMK_SUBSCRIPTION(ime_state, zmk_keycode_state_changed);

/* ---- &ime_kp behavior ---- */

#if IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)

static const struct behavior_parameter_value_metadata param_values[] = {
    {
        .display_name = "Key",
        .type = BEHAVIOR_PARAMETER_VALUE_TYPE_HID_USAGE,
    },
};

static const struct behavior_parameter_metadata_set param_metadata_set[] = {{
    .param1_values = param_values,
    .param1_values_len = ARRAY_SIZE(param_values),
}};

static const struct behavior_parameter_metadata metadata = {
    .sets_len = ARRAY_SIZE(param_metadata_set),
    .sets = param_metadata_set,
};

#endif

/* 押したときに送ったかどうか。離すときも同じ判断にそろえ、キーが押しっぱなしにならないようにする */
static bool sent_on_press = false;

static int on_ime_kp_pressed(struct zmk_behavior_binding *binding,
                             struct zmk_behavior_binding_event event) {
    sent_on_press = ime_on;
    if (!sent_on_press) {
        return ZMK_BEHAVIOR_OPAQUE;
    }
    return raise_zmk_keycode_state_changed_from_encoded(binding->param1, true, event.timestamp);
}

static int on_ime_kp_released(struct zmk_behavior_binding *binding,
                              struct zmk_behavior_binding_event event) {
    if (!sent_on_press) {
        return ZMK_BEHAVIOR_OPAQUE;
    }
    sent_on_press = false;
    return raise_zmk_keycode_state_changed_from_encoded(binding->param1, false, event.timestamp);
}

static const struct behavior_driver_api behavior_ime_key_press_driver_api = {
    .binding_pressed = on_ime_kp_pressed,
    .binding_released = on_ime_kp_released,
#if IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)
    .parameter_metadata = &metadata,
#endif
};

#define IME_KP_INST(n)                                                                             \
    BEHAVIOR_DT_INST_DEFINE(n, NULL, NULL, NULL, NULL, POST_KERNEL,                                \
                            CONFIG_KERNEL_INIT_PRIORITY_DEFAULT,                                   \
                            &behavior_ime_key_press_driver_api);

DT_INST_FOREACH_STATUS_OKAY(IME_KP_INST)
