
class Drone:
    def __init__(self, drone_id: int, start: str) -> None:
        self.drone_id: int = drone_id
        self.drone_tag: str = ""
        self.current_zone: str = start
        self.canva_id: int = 0
        self.path: list[str] = []
        self.delivered = False
        self.is_moving = False
        self.blocked = False
        self.wait_turns = 0
        self.prev_zone: str = ""
        self.blocked_turns: int = 0
        self.wait_target: str | None = None
