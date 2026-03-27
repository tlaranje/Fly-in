
class Drone:
    def __init__(self, drone_id: int, start: str) -> None:
        self.drone_id: int = drone_id
        self.current_zone: str | None = start
        self.canva_id: int = 0
        self.path: list[str] = []
        self.delivered = False
        self.is_moving = False
        self.blocked = False
        self.blocked_next: str = ""
        self.in_transit: bool = False
        self.transit_target: str = ""
        self.transit_remaining: int = 0
        self.transit_link: str = ""
        self.transit_target_coords: tuple[float, float] = (0, 0)
        self.transit_center_coords: tuple[float, float] = (0, 0)
        self.transit_origin_coords: tuple[float, float] = (0, 0)
