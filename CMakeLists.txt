# SPDX-License-Identifier: MIT
# この config リポジトリ自体を Zephyr モジュールとして扱い、独自 behavior を追加する。

if(CONFIG_ZMK_BEHAVIOR_IME_KEY_PRESS)
  # behavior はセントラル（右手）側で処理されるので、そちらだけでビルドする
  if((NOT CONFIG_ZMK_SPLIT) OR CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
    target_sources(app PRIVATE ${CMAKE_CURRENT_LIST_DIR}/src/behavior_ime_key_press.c)
  endif()
endif()
