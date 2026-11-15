from dataclasses import dataclass
from typing import List, Optional
import pygame
from src.entities.obstacles import LevelObject
from src.entities.player import Player
from src.utils.math_helpers import snap_angle_90


@dataclass
class CollisionOutcome:
    died: bool = False
    finished: bool = False
    activated_orb: Optional[LevelObject] = None
    activated_pad: Optional[LevelObject] = None
    switched_mode: Optional[str] = None


class CollisionSystem:
    """Resolves solid platforms, hazards, jump orbs, jump pads, and portals."""

    def resolve(
        self,
        player: Player,
        objects: List[LevelObject],
        prev_bottom: float,
        jump_just_pressed: bool,
        jump_held: bool,
    ) -> CollisionOutcome:
        outcome = CollisionOutcome()
        p_rect = player.rect
        p_hazard = player.hazard_hitbox

        # Broad-phase filter near the player
        nearby = [
            obj
            for obj in objects
            if obj.x + obj.width >= player.x - 96 and obj.x <= player.x + player.size + 96
        ]

        # 1. Resolve solid platforms (blocks & slabs) first
        for obj in nearby:
            if obj.obj_type not in ("block", "slab"):
                continue

            o_rect = obj.rect
            if not p_rect.colliderect(o_rect):
                continue

            # Landing on top surface
            if player.vy >= 0 and prev_bottom <= o_rect.top + 16:
                player.y = float(o_rect.top - player.size)
                player.vy = 0.0
                if not player.on_ground and player.mode == "cube":
                    player.angle = snap_angle_90(player.angle)
                player.on_ground = True
                p_rect = player.rect
                p_hazard = player.hazard_hitbox
            # Ship mode can gently graze ceilings of blocks without dying if not crashing head-on
            elif player.mode == "ship" and player.vy < 0 and p_rect.top >= o_rect.bottom - 14:
                player.y = float(o_rect.bottom)
                player.vy = 0.0
                p_rect = player.rect
                p_hazard = player.hazard_hitbox
            else:
                outcome.died = True
                return outcome

        # 2. Resolve spikes, orbs, pads, portals, and finish line
        for obj in nearby:
            if obj.obj_type in ("block", "slab"):
                continue

            if obj.obj_type in ("spike", "spike_down"):
                if p_hazard.colliderect(obj.hazard_rect):
                    outcome.died = True
                    return outcome

            elif obj.obj_type == "orb":
                orb_zone = obj.rect.inflate(18, 18)
                can_trigger = jump_just_pressed or (jump_held and not player.orb_consumed_this_press)
                if p_rect.colliderect(orb_zone) and can_trigger:
                    player.trigger_orb()
                    outcome.activated_orb = obj

            elif obj.obj_type == "pad":
                if p_rect.colliderect(obj.rect):
                    player.trigger_pad()
                    outcome.activated_pad = obj

            elif obj.obj_type in ("portal_ship", "portal_cube"):
                if p_rect.colliderect(obj.rect):
                    target_mode = "ship" if obj.obj_type == "portal_ship" else "cube"
                    if player.set_mode(target_mode):
                        outcome.switched_mode = target_mode

            elif obj.obj_type == "finish":
                if p_rect.colliderect(obj.rect) or player.x >= obj.x:
                    outcome.finished = True
                    return outcome

        return outcome
