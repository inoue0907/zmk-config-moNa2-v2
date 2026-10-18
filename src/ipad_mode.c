/*
 * SPDX-License-Identifier: MIT
 *
 * 出力先が iPad の BT プロファイルのときだけ、指定レイヤーを有効にする。
 *
 *   ipad_mode { compatible = "zmk,ipad-mode"; profile = <3>; layer = <IPAD>; };
 *
 * BT キーで切り替えたときだけでなく、起動後の再接続や USB との切り替えでも
 * 出力先を見直すので、電源を入れ直しても iPad モードのままになる。
 * USB に出力しているときは iPad モードにしない。
 */

#define DT_DRV_COMPAT zmk_ipad_mode

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include <zmk/endpoints.h>
#include <zmk/event_manager.h>
#include <zmk/events/endpoint_changed.h>
#include <zmk/events/ble_active_profile_changed.h>
#include <zmk/keymap.h>

LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

#define IPAD_NODE DT_INST(0, DT_DRV_COMPAT)
#define IPAD_PROFILE DT_PROP(IPAD_NODE, profile)
#define IPAD_LAYER DT_PROP(IPAD_NODE, layer)

static void ipad_mode_update(void) {
    struct zmk_endpoint_instance ep = zmk_endpoints_selected();
    bool ipad = ep.transport == ZMK_TRANSPORT_BLE && ep.ble.profile_index == IPAD_PROFILE;

    if (ipad == zmk_keymap_layer_active(IPAD_LAYER)) {
        return;
    }

    LOG_INF("iPad mode: %s", ipad ? "on" : "off");
    if (ipad) {
        zmk_keymap_layer_activate(IPAD_LAYER);
    } else {
        zmk_keymap_layer_deactivate(IPAD_LAYER);
    }
}

static int ipad_mode_listener(const zmk_event_t *eh) {
    ipad_mode_update();
    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(ipad_mode, ipad_mode_listener);
/* 出力先が変わったとき（BT 番号の切り替え、USB の抜き差し） */
ZMK_SUBSCRIPTION(ipad_mode, zmk_endpoint_changed);
/* 起動直後は出力先が変わらないので endpoint_changed が来ない。接続時のこちらで拾う */
ZMK_SUBSCRIPTION(ipad_mode, zmk_ble_active_profile_changed);
