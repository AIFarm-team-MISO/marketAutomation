from __future__ import annotations

import os
import sys



def confirm_enter_or_escape(
    *,
    execute_message: str = "[Enter / 1 / y] 실행",
    cancel_message: str = "[Esc / 2 / q] 취소",
) -> bool:
    print(execute_message)
    print(cancel_message)

    if os.name == "nt" and sys.stdin.isatty():
        import msvcrt

        while True:
            key = msvcrt.getwch()

            if key in {"\r", "\n", "1", "y", "Y"}:
                print()
                return True

            if key in {"\x1b", "2", "q", "Q", "n", "N"}:
                print()
                return False

            if key == "\x03":
                raise KeyboardInterrupt

            if key in {"\x00", "\xe0"}:
                msvcrt.getwch()

    while True:
        answer = input("선택: ").strip().lower()

        if answer in {"", "1", "y", "yes", "실행"}:
            return True

        if answer in {
            "esc",
            "escape",
            "2",
            "q",
            "n",
            "no",
            "취소",
            "종료",
        }:
            return False

        print("Enter/1/y 또는 Esc/2/q를 입력해 주세요.")
