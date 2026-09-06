from enum import StrEnum


class ActionType(StrEnum):
    BLOCK_IP = "block_ip"
    CLEAR_CACHE = "clear_cache"
    CUSTOM = "custom"
    KILL_PROCESS = "kill_process"
    MODIFY_CONFIG = "modify_config"
    RESTART_SERVICE = "restart_service"
    ROLLBACK = "rollback"
    ROTATE_CREDENTIALS = "rotate_credentials"
    SCALE_DOWN = "scale_down"
    SCALE_UP = "scale_up"

    def __str__(self) -> str:
        return str(self.value)
