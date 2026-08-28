from typing import List, Optional

from termcolor import colored, cprint


def get_input_number(
    prompt, min_number=None, max_number=None, quit_strs=["quit", "exit", "q"]
):
    """获取用户输入，支持退出功能

    :param message: 提示信息
    :param quit_strs: 退出字符串列表
    :return: 用户输入的整数
    """
    exit_msg = "/".join(quit_strs)
    input_index = input(colored(f"{prompt}[输入 {exit_msg} 退出]: ", color="cyan"))
    input_index = input_index.strip()
    while True:
        if input_index in quit_strs:
            return 0
        try:
            index = int(input_index)
            if (min_number is None or index >= min_number) and (
                max_number is None or index <= max_number
            ):
                return index
            raise ValueError(f"{index} is out of range")
        except ValueError:
            input_index = input(colored("输入错误，请重新输入: ", color="red"))
            input_index = input_index.strip()


def select_items(
    items: List[str],
    default: Optional[str] = None,
    select_prompt: Optional[str] = None,
    input_prompt: Optional[str] = None,
):
    """打印items列表, 并获取用户选择结果"""
    select_prompt = select_prompt or "请选择:"
    input_prompt = input_prompt or "请输入编号"

    cprint(f"---- {select_prompt} ----", color="yellow")
    for i, item in enumerate(items, start=1):
        print(f"{i:<{len(str(len(items)))}}. {item}")
    selected = get_input_number(input_prompt, min_number=1, max_number=len(items))
    if not selected:
        return default
    return items[selected - 1]
