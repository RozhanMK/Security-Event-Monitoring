import inspect

def get_current_function_name() -> str:
    frame = inspect.currentframe().f_back
    module = inspect.getmodule(frame)
    module_name = module.__name__ if module else "unknown"
    return f"{module_name}.{frame.f_code.co_name}"