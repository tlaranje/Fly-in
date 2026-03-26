
class Drone:
    def __init__(self, drone_id: int, start: str) -> None:
        self.drone_id = drone_id
        self.current_zone = start
        self.canva_id: int = 0
        self.path: list[str] = []
        self.delivered = False
        self.is_moving = False
