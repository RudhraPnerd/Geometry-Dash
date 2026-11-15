from typing import List, Tuple
from src.entities.obstacles import LevelObject


class LevelBuilder:
    """Constructs the multi-section Stereo Madness style level with Cube and Ship stages."""

    def __init__(self, tile_size: int, ground_y: float) -> None:
        self.tile = tile_size
        self.ground_y = ground_y
        self.objects: List[LevelObject] = []
        self.finish_x: float = 0.0

    def _gx(self, grid_x: float) -> float:
        return grid_x * self.tile

    def _gy(self, grid_y_from_ground: float) -> float:
        # grid_y_from_ground = 1 means resting directly on top of the floor
        return self.ground_y - (grid_y_from_ground * self.tile)

    def add_block(self, gx: float, gy: float, w_tiles: float = 1.0, h_tiles: float = 1.0) -> None:
        self.objects.append(
            LevelObject(
                obj_type="block",
                x=self._gx(gx),
                y=self._gy(gy + h_tiles - 1),
                width=int(w_tiles * self.tile),
                height=int(h_tiles * self.tile),
            )
        )

    def add_slab(self, gx: float, gy: float, w_tiles: float = 1.0) -> None:
        h = int(self.tile * 0.45)
        self.objects.append(
            LevelObject(
                obj_type="slab",
                x=self._gx(gx),
                y=self._gy(gy) + (self.tile - h),
                width=int(w_tiles * self.tile),
                height=h,
            )
        )

    def add_spike(self, gx: float, gy: float = 1.0, upside_down: bool = False) -> None:
        self.objects.append(
            LevelObject(
                obj_type="spike_down" if upside_down else "spike",
                x=self._gx(gx),
                y=self._gy(gy),
                width=self.tile,
                height=self.tile,
            )
        )

    def add_spike_row(self, start_gx: float, count: int, gy: float = 1.0, upside_down: bool = False) -> None:
        for i in range(count):
            self.add_spike(start_gx + i, gy=gy, upside_down=upside_down)

    def add_orb(self, gx: float, gy: float) -> None:
        self.objects.append(
            LevelObject(
                obj_type="orb",
                x=self._gx(gx),
                y=self._gy(gy),
                width=self.tile,
                height=self.tile,
            )
        )

    def add_pad(self, gx: float, gy: float = 1.0) -> None:
        self.objects.append(
            LevelObject(
                obj_type="pad",
                x=self._gx(gx),
                y=self._gy(gy),
                width=self.tile,
                height=self.tile,
            )
        )

    def add_portal(self, gx: float, portal_type: str) -> None:
        h_tiles = 3.2
        self.objects.append(
            LevelObject(
                obj_type=portal_type,
                x=self._gx(gx),
                y=self._gy(h_tiles),
                width=int(self.tile * 1.15),
                height=int(self.tile * h_tiles),
            )
        )

    def build_stereo_madness(self) -> Tuple[List[LevelObject], float]:
        self.objects.clear()

        # --- SECTION 1: Classic Opening Jumps (Grid 16 -> 68) ---
        self.add_spike(18, 1)

        self.add_spike(27, 1)
        self.add_spike(28, 1)

        # Staircase pillars
        self.add_block(37, 1, 2, 1)
        self.add_block(42, 1, 2, 2)
        self.add_block(47, 1, 3, 3)

        # Drop down with spike trap
        self.add_spike_row(50, 3, 1)
        self.add_block(55, 1, 3, 1)
        self.add_spike(58, 1)
        self.add_spike(59, 1)

        # Jump pad launch onto high platform
        self.add_pad(64, 1)
        self.add_spike_row(65, 4, 1)
        self.add_block(69, 3, 5, 1)
        self.add_spike(71, 4)

        # --- SECTION 2: Rhythm Orbs & Pit Gaps (Grid 78 -> 132) ---
        self.add_spike_row(78, 4, 1)
        self.add_orb(79.5, 2.5)
        self.add_block(83, 1, 4, 1)

        self.add_spike_row(87, 4, 1)
        self.add_orb(88.5, 2.6)
        self.add_block(92, 2, 4, 1)
        self.add_spike_row(92, 4, 1)

        # Triple spike challenge + rhythmic platforms
        self.add_block(100, 1, 2, 1)
        self.add_spike(105, 1)
        self.add_spike(106, 1)
        self.add_spike(107, 1)

        self.add_block(113, 1, 2, 1)
        self.add_block(118, 2, 2, 1)
        self.add_spike_row(115, 7, 1)
        self.add_block(123, 3, 3, 1)
        self.add_orb(127.5, 3.8)
        self.add_block(130, 2, 4, 1)

        # --- SECTION 3: Ship Flight Sequence (Grid 138 -> 206) ---
        self.add_portal(138, "portal_ship")

        # Floor & ceiling hazard gates
        self.add_block(146, 1, 3, 2)
        self.add_spike(147, 3)

        self.add_block(155, 6, 3, 2)
        self.add_spike(156, 5, upside_down=True)

        # Mid-air corridor
        self.add_block(165, 1, 5, 2)
        self.add_block(165, 6, 5, 2)

        # Slalom pillars
        self.add_block(176, 1, 2, 3)
        self.add_spike(176.5, 4)

        self.add_block(185, 5, 2, 3)
        self.add_spike(185.5, 4, upside_down=True)

        self.add_block(194, 1, 3, 2)
        self.add_block(194, 6, 3, 2)

        # Return to Cube mode
        self.add_portal(204, "portal_cube")

        # --- SECTION 4: Finale Gauntlet (Grid 210 -> 268) ---
        self.add_spike(213, 1)
        self.add_spike(214, 1)

        self.add_block(220, 1, 2, 1)
        self.add_pad(221, 2)
        self.add_spike_row(222, 5, 1)
        self.add_block(227, 4, 4, 1)

        self.add_spike_row(231, 5, 1)
        self.add_orb(233, 4.2)
        self.add_block(236, 3, 3, 1)

        self.add_spike_row(239, 5, 1)
        self.add_orb(241, 3.5)
        self.add_block(244, 2, 3, 1)

        # Final staircase to finish gate
        self.add_block(251, 1, 2, 1)
        self.add_block(255, 1, 2, 2)
        self.add_block(259, 1, 3, 3)

        finish_gx = 266
        self.finish_x = self._gx(finish_gx)
        self.objects.append(
            LevelObject(
                obj_type="finish",
                x=self.finish_x,
                y=self._gy(8),
                width=int(self.tile * 0.8),
                height=int(self.tile * 8),
            )
        )
        return self.objects, self.finish_x
