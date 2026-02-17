import random
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.db.session import get_db
from app.models.game import AttendanceStatus, Game, GameAttendance
from app.models.game_draft import DraftStatus, GameDraft, GameDraftPick
from app.models.game_guest import GameGuest
from app.models.game_team import GameTeamGuest, GameTeamMember, TeamSide
from app.models.org_member import MemberType, OrgMember, OrgRole
from app.schemas.game import GameCreate, Game as GameSchema, AttendanceCreate, Attendance
from app.routers.deps import get_current_user
from app.models.user import User

# IMPORTA O HELPER QUE VOCÊ CRIOU
from app.routers.deps import require_org_member
from app.schemas.attendance import AttendanceSetRequest, GameAttendanceSummary
from app.schemas.game_detail import GameDetailResponse
from app.schemas.draft import DraftPickRequest, DraftStateResponse, DraftSummary
from app.schemas.teams import CaptainsResolved, CaptainsSetRequest, TeamsResponse, TeamAssignmentSetRequest

router = APIRouter()


def _get_membership(db: Session, org_id: UUID, user_id: UUID) -> OrgMember | None:
    return (
        db.query(OrgMember)
        .filter(OrgMember.org_id == org_id, OrgMember.user_id == user_id)
        .first()
    )


def _require_admin_membership(db: Session, org_id: UUID, user_id: UUID) -> OrgMember:
    membership = _get_membership(db=db, org_id=org_id, user_id=user_id)
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    if membership.role not in (OrgRole.OWNER, OrgRole.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized")
    return membership


def _resolve_member_payload(m: OrgMember) -> dict:
    included = m.member_type == MemberType.MONTHLY
    return {
        "type": "MEMBER",
        "org_member_id": m.id,
        "nickname": m.nickname,
        "member_type": m.member_type,
        "included": included,
        "billable": not included,
        "user": m.user,
    }


def _resolve_guest_payload(g: GameGuest) -> dict:
    return {
        "type": "GUEST",
        "game_guest_id": g.id,
        "name": g.name,
        "phone": g.phone,
        "billable": True,
        "source": "GAME_GUEST",
    }


def _pick_two_with_anti_repeat(candidates: list[tuple[str, UUID]], forbidden: set[tuple[str, UUID]]) -> tuple[tuple[str, UUID], tuple[str, UUID]]:
    available = [c for c in candidates if c not in forbidden]
    pool = available if len(available) >= 2 else candidates
    if len(pool) < 2:
        raise HTTPException(status_code=400, detail="Not enough eligible captains")
    chosen = random.sample(pool, 2)
    return chosen[0], chosen[1]


def _draft_turn(order_mode: str, pick_index: int) -> TeamSide:
    mode = (order_mode or "ABBA").upper()
    if mode != "ABBA":
        mode = "ABBA"
    seq = [TeamSide.A, TeamSide.B, TeamSide.B, TeamSide.A]
    return seq[pick_index % len(seq)]

@router.post("/orgs/{org_id}/games", response_model=GameSchema)
def create_game(
    org_id: UUID,
    game_in: GameCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # garante que é membro (e org existe)
    require_org_member(org_id=org_id, db=db, current_user=current_user)

    # regra: só ADMIN/OWNER pode criar
    membership = (
        db.query(OrgMember)
        .filter(OrgMember.user_id == current_user.id, OrgMember.org_id == org_id)
        .first()
    )
    if membership.role not in [OrgRole.ADMIN, OrgRole.OWNER]:
        raise HTTPException(status_code=403, detail="Not authorized to create games")

    game = Game(**game_in.model_dump(), org_id=org_id, created_by_member_id=membership.id)
    db.add(game)
    db.commit()
    db.refresh(game)
    return game

@router.get("/orgs/{org_id}/games", response_model=list[GameSchema])
def read_games(
    org_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)
    return db.query(Game).filter(Game.org_id == org_id).all()


@router.get("/orgs/{org_id}/games/{game_id}", response_model=GameDetailResponse)
def get_game_detail(
    org_id: UUID,
    game_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)

    game = (
        db.query(Game)
        .options(joinedload(Game.created_by_member).joinedload(OrgMember.user))
        .filter(Game.id == game_id, Game.org_id == org_id)
        .first()
    )
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    attendance_rows = (
        db.query(GameAttendance)
        .options(joinedload(GameAttendance.org_member).joinedload(OrgMember.user))
        .filter(GameAttendance.org_id == org_id, GameAttendance.game_id == game_id)
        .order_by(GameAttendance.created_at.asc())
        .all()
    )

    going_count = 0
    maybe_count = 0
    not_going_count = 0
    attendance_list = []
    for r in attendance_rows:
        if not r.org_member or not r.org_member.user:
            continue
        if r.status == AttendanceStatus.GOING:
            going_count += 1
        elif r.status == AttendanceStatus.MAYBE:
            maybe_count += 1
        else:
            not_going_count += 1

        mt = r.org_member.member_type
        included = mt == MemberType.MONTHLY
        attendance_list.append(
            {
                "org_member_id": r.org_member_id,
                "status": r.status,
                "member_type": mt,
                "included": included,
                "billable": not included,
                "nickname": r.org_member.nickname,
                "user": r.org_member.user,
            }
        )

    created_by = None
    if game.created_by_member and game.created_by_member.user:
        created_by = {
            "org_member_id": game.created_by_member.id,
            "user_id": game.created_by_member.user.id,
            "email": game.created_by_member.user.email,
            "full_name": game.created_by_member.user.full_name,
            "nickname": game.created_by_member.nickname,
        }

    guest_rows = (
        db.query(GameGuest)
        .filter(GameGuest.org_id == org_id, GameGuest.game_id == game_id)
        .order_by(GameGuest.created_at.asc())
        .all()
    )
    game_guests = [
        {
            "id": g.id,
            "name": g.name,
            "phone": g.phone,
            "billable": True,
            "source": "GAME_GUEST",
        }
        for g in guest_rows
    ]

    captain_a = None
    captain_b = None
    if game.captain_a_member_id:
        m = (
            db.query(OrgMember)
            .options(joinedload(OrgMember.user))
            .filter(OrgMember.id == game.captain_a_member_id, OrgMember.org_id == org_id)
            .first()
        )
        if m and m.user:
            captain_a = _resolve_member_payload(m)
    elif game.captain_a_guest_id:
        g = (
            db.query(GameGuest)
            .filter(GameGuest.id == game.captain_a_guest_id, GameGuest.org_id == org_id, GameGuest.game_id == game_id)
            .first()
        )
        if g:
            captain_a = _resolve_guest_payload(g)

    if game.captain_b_member_id:
        m = (
            db.query(OrgMember)
            .options(joinedload(OrgMember.user))
            .filter(OrgMember.id == game.captain_b_member_id, OrgMember.org_id == org_id)
            .first()
        )
        if m and m.user:
            captain_b = _resolve_member_payload(m)
    elif game.captain_b_guest_id:
        g = (
            db.query(GameGuest)
            .filter(GameGuest.id == game.captain_b_guest_id, GameGuest.org_id == org_id, GameGuest.game_id == game_id)
            .first()
        )
        if g:
            captain_b = _resolve_guest_payload(g)

    member_rows = (
        db.query(GameTeamMember)
        .options(joinedload(GameTeamMember.org_member).joinedload(OrgMember.user))
        .filter(GameTeamMember.org_id == org_id, GameTeamMember.game_id == game_id)
        .all()
    )
    guest_team_rows = (
        db.query(GameTeamGuest)
        .options(joinedload(GameTeamGuest.game_guest))
        .filter(GameTeamGuest.org_id == org_id, GameTeamGuest.game_id == game_id)
        .all()
    )

    team_a_members = []
    team_b_members = []
    for r in member_rows:
        if not r.org_member or not r.org_member.user:
            continue
        payload = _resolve_member_payload(r.org_member)
        item = {
            "org_member_id": payload["org_member_id"],
            "nickname": payload["nickname"],
            "member_type": payload["member_type"],
            "included": payload["included"],
            "billable": payload["billable"],
            "user": payload["user"],
        }
        if r.team == TeamSide.A:
            team_a_members.append(item)
        else:
            team_b_members.append(item)

    team_a_guests = []
    team_b_guests = []
    for r in guest_team_rows:
        if not r.game_guest:
            continue
        payload = _resolve_guest_payload(r.game_guest)
        item = {
            "game_guest_id": payload["game_guest_id"],
            "name": payload["name"],
            "phone": payload["phone"],
            "billable": True,
            "source": "GAME_GUEST",
        }
        if r.team == TeamSide.A:
            team_a_guests.append(item)
        else:
            team_b_guests.append(item)

    teams = {
        "team_a": {"members": team_a_members, "guests": team_a_guests},
        "team_b": {"members": team_b_members, "guests": team_b_guests},
    }

    draft_row = db.query(GameDraft).filter(GameDraft.org_id == org_id, GameDraft.game_id == game_id).first()
    if not draft_row:
        draft_status = DraftStatus.NOT_STARTED
        draft_pick_index = 0
        draft_order_mode = "ABBA"
    else:
        draft_status = draft_row.status
        draft_pick_index = draft_row.current_pick_index
        draft_order_mode = draft_row.order_mode or "ABBA"

    picks_count = (
        db.query(GameDraftPick.id)
        .filter(GameDraftPick.org_id == org_id, GameDraftPick.game_id == game_id)
        .count()
    )
    pool_member_count = (
        db.query(GameAttendance.org_member_id)
        .filter(
            GameAttendance.org_id == org_id,
            GameAttendance.game_id == game_id,
            GameAttendance.status == AttendanceStatus.GOING,
        )
        .distinct()
        .count()
    )
    pool_guest_count = db.query(GameGuest.id).filter(GameGuest.org_id == org_id, GameGuest.game_id == game_id).count()
    total_pool = pool_member_count + pool_guest_count
    remaining_count = max(total_pool - picks_count, 0)

    current_turn = None
    if draft_status == DraftStatus.IN_PROGRESS:
        current_turn = _draft_turn(draft_order_mode, draft_pick_index)

    return {
        "id": game.id,
        "org_id": game.org_id,
        "title": game.title,
        "sport": game.sport,
        "location": game.location,
        "start_at": game.start_at,
        "created_by": created_by,
        "attendance_summary": {
            "going_count": going_count,
            "maybe_count": maybe_count,
            "not_going_count": not_going_count,
        },
        "attendance_list": attendance_list,
        "game_guests": game_guests,
        "captains": {"captain_a": captain_a, "captain_b": captain_b},
        "teams": teams,
        "draft": {
            "status": draft_status,
            "current_turn_team_side": current_turn,
            "picks_count": picks_count,
            "remaining_count": remaining_count,
        },
    }


@router.put("/orgs/{org_id}/games/{game_id}/captains", response_model=CaptainsResolved)
def set_game_captains(
    org_id: UUID,
    game_id: UUID,
    payload: CaptainsSetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)
    _require_admin_membership(db=db, org_id=org_id, user_id=current_user.id)

    game = (
        db.query(Game)
        .filter(Game.id == game_id, Game.org_id == org_id)
        .first()
    )
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    def validate_ref(ref: dict | None) -> tuple[str, UUID] | None:
        if ref is None:
            return None
        t = (ref.get("type") or "").upper()
        rid = ref.get("id")
        if t not in ("MEMBER", "GUEST"):
            raise HTTPException(status_code=400, detail="Invalid captain type")
        if not rid:
            raise HTTPException(status_code=400, detail="Invalid captain id")
        return t, rid

    mode = (payload.mode or "MANUAL").upper()
    if mode not in ("MANUAL", "RANDOM"):
        raise HTTPException(status_code=400, detail="Invalid mode")

    if mode == "MANUAL":
        cap_a = validate_ref(payload.captain_a.model_dump() if payload.captain_a else None)
        cap_b = validate_ref(payload.captain_b.model_dump() if payload.captain_b else None)

        if cap_a and cap_b and cap_a == cap_b:
            raise HTTPException(status_code=400, detail="Captains must be different")

        def assert_member_going(org_member_id: UUID) -> OrgMember:
            row = (
                db.query(GameAttendance)
                .options(joinedload(GameAttendance.org_member).joinedload(OrgMember.user))
                .filter(
                    GameAttendance.org_id == org_id,
                    GameAttendance.game_id == game_id,
                    GameAttendance.org_member_id == org_member_id,
                    GameAttendance.status == AttendanceStatus.GOING,
                )
                .first()
            )
            if not row or not row.org_member:
                raise HTTPException(status_code=409, detail="Member is not GOING")
            return row.org_member

        def assert_guest_in_game(game_guest_id: UUID) -> GameGuest:
            g = (
                db.query(GameGuest)
                .filter(GameGuest.id == game_guest_id, GameGuest.org_id == org_id, GameGuest.game_id == game_id)
                .first()
            )
            if not g:
                raise HTTPException(status_code=404, detail="Game guest not found")
            return g

        resolved_a = None
        resolved_b = None

        if cap_a is None:
            game.captain_a_member_id = None
            game.captain_a_guest_id = None
        elif cap_a[0] == "MEMBER":
            m = assert_member_going(cap_a[1])
            game.captain_a_member_id = m.id
            game.captain_a_guest_id = None
            resolved_a = _resolve_member_payload(m)
        else:
            g = assert_guest_in_game(cap_a[1])
            game.captain_a_guest_id = g.id
            game.captain_a_member_id = None
            resolved_a = _resolve_guest_payload(g)

        if cap_b is None:
            game.captain_b_member_id = None
            game.captain_b_guest_id = None
        elif cap_b[0] == "MEMBER":
            m = assert_member_going(cap_b[1])
            game.captain_b_member_id = m.id
            game.captain_b_guest_id = None
            resolved_b = _resolve_member_payload(m)
        else:
            g = assert_guest_in_game(cap_b[1])
            game.captain_b_guest_id = g.id
            game.captain_b_member_id = None
            resolved_b = _resolve_guest_payload(g)

        db.commit()
        db.refresh(game)
        return {"captain_a": resolved_a, "captain_b": resolved_b}

    going_members = (
        db.query(GameAttendance.org_member_id)
        .filter(
            GameAttendance.org_id == org_id,
            GameAttendance.game_id == game_id,
            GameAttendance.status == AttendanceStatus.GOING,
        )
        .distinct()
        .all()
    )
    member_ids = [r[0] for r in going_members]
    guest_rows = (
        db.query(GameGuest.id)
        .filter(GameGuest.org_id == org_id, GameGuest.game_id == game_id)
        .all()
    )
    guest_ids = [r[0] for r in guest_rows]

    if len(member_ids) >= 2:
        candidates = [("MEMBER", mid) for mid in member_ids]
    else:
        candidates = [("MEMBER", mid) for mid in member_ids] + [("GUEST", gid) for gid in guest_ids]

    prev = (
        db.query(Game)
        .filter(Game.org_id == org_id, Game.start_at < game.start_at, Game.id != game.id)
        .order_by(Game.start_at.desc())
        .first()
    )
    forbidden: set[tuple[str, UUID]] = set()
    if prev:
        if prev.captain_a_member_id:
            forbidden.add(("MEMBER", prev.captain_a_member_id))
        if prev.captain_b_member_id:
            forbidden.add(("MEMBER", prev.captain_b_member_id))
        if prev.captain_a_guest_id:
            forbidden.add(("GUEST", prev.captain_a_guest_id))
        if prev.captain_b_guest_id:
            forbidden.add(("GUEST", prev.captain_b_guest_id))

    cap_a, cap_b = _pick_two_with_anti_repeat(candidates=candidates, forbidden=forbidden)

    def resolve_tuple(t: tuple[str, UUID]) -> dict:
        if t[0] == "MEMBER":
            m = (
                db.query(OrgMember)
                .options(joinedload(OrgMember.user))
                .filter(OrgMember.id == t[1], OrgMember.org_id == org_id)
                .first()
            )
            if not m:
                raise HTTPException(status_code=404, detail="Member not found")
            return _resolve_member_payload(m)
        g = (
            db.query(GameGuest)
            .filter(GameGuest.id == t[1], GameGuest.org_id == org_id, GameGuest.game_id == game_id)
            .first()
        )
        if not g:
            raise HTTPException(status_code=404, detail="Game guest not found")
        return _resolve_guest_payload(g)

    if cap_a[0] == "MEMBER":
        game.captain_a_member_id = cap_a[1]
        game.captain_a_guest_id = None
    else:
        game.captain_a_guest_id = cap_a[1]
        game.captain_a_member_id = None

    if cap_b[0] == "MEMBER":
        game.captain_b_member_id = cap_b[1]
        game.captain_b_guest_id = None
    else:
        game.captain_b_guest_id = cap_b[1]
        game.captain_b_member_id = None

    db.commit()
    db.refresh(game)
    return {"captain_a": resolve_tuple(cap_a), "captain_b": resolve_tuple(cap_b)}


@router.get("/orgs/{org_id}/games/{game_id}/teams", response_model=TeamsResponse)
def get_game_teams(
    org_id: UUID,
    game_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)
    game = db.query(Game).filter(Game.id == game_id, Game.org_id == org_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    member_rows = (
        db.query(GameTeamMember)
        .options(joinedload(GameTeamMember.org_member).joinedload(OrgMember.user))
        .filter(GameTeamMember.org_id == org_id, GameTeamMember.game_id == game_id)
        .all()
    )
    guest_rows = (
        db.query(GameTeamGuest)
        .options(joinedload(GameTeamGuest.game_guest))
        .filter(GameTeamGuest.org_id == org_id, GameTeamGuest.game_id == game_id)
        .all()
    )

    team_a_members = []
    team_b_members = []
    for r in member_rows:
        if not r.org_member or not r.org_member.user:
            continue
        payload = _resolve_member_payload(r.org_member)
        item = {
            "org_member_id": payload["org_member_id"],
            "nickname": payload["nickname"],
            "member_type": payload["member_type"],
            "included": payload["included"],
            "billable": payload["billable"],
            "user": payload["user"],
        }
        if r.team == TeamSide.A:
            team_a_members.append(item)
        else:
            team_b_members.append(item)

    team_a_guests = []
    team_b_guests = []
    for r in guest_rows:
        if not r.game_guest:
            continue
        payload = _resolve_guest_payload(r.game_guest)
        item = {
            "game_guest_id": payload["game_guest_id"],
            "name": payload["name"],
            "phone": payload["phone"],
            "billable": True,
            "source": "GAME_GUEST",
        }
        if r.team == TeamSide.A:
            team_a_guests.append(item)
        else:
            team_b_guests.append(item)

    return {
        "team_a": {"members": team_a_members, "guests": team_a_guests},
        "team_b": {"members": team_b_members, "guests": team_b_guests},
    }


@router.post("/orgs/{org_id}/games/{game_id}/draft/start", response_model=DraftStateResponse)
def start_draft(
    org_id: UUID,
    game_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)
    _require_admin_membership(db=db, org_id=org_id, user_id=current_user.id)

    game = db.query(Game).filter(Game.id == game_id, Game.org_id == org_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    draft = db.query(GameDraft).filter(GameDraft.org_id == org_id, GameDraft.game_id == game_id).first()
    if not draft:
        draft = GameDraft(org_id=org_id, game_id=game_id, status=DraftStatus.IN_PROGRESS, order_mode="ABBA", current_pick_index=0)
        db.add(draft)
        db.commit()
        db.refresh(draft)
    else:
        if draft.status == DraftStatus.FINISHED:
            raise HTTPException(status_code=409, detail="Draft already finished")
        if draft.status != DraftStatus.IN_PROGRESS:
            draft.status = DraftStatus.IN_PROGRESS
            draft.order_mode = draft.order_mode or "ABBA"
            draft.current_pick_index = draft.current_pick_index or 0
            db.commit()
            db.refresh(draft)

    return get_draft(org_id=org_id, game_id=game_id, db=db, current_user=current_user)


@router.post("/orgs/{org_id}/games/{game_id}/draft/pick", response_model=DraftStateResponse)
def draft_pick(
    org_id: UUID,
    game_id: UUID,
    payload: DraftPickRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)
    _require_admin_membership(db=db, org_id=org_id, user_id=current_user.id)

    game = db.query(Game).filter(Game.id == game_id, Game.org_id == org_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    draft = db.query(GameDraft).filter(GameDraft.org_id == org_id, GameDraft.game_id == game_id).first()
    if not draft or draft.status == DraftStatus.NOT_STARTED:
        raise HTTPException(status_code=409, detail="Draft not started")
    if draft.status != DraftStatus.IN_PROGRESS:
        raise HTTPException(status_code=409, detail="Draft is not in progress")

    expected = _draft_turn(draft.order_mode, draft.current_pick_index)
    if payload.team_side != expected:
        raise HTTPException(status_code=409, detail="Not your turn")

    if (payload.org_member_id is None and payload.game_guest_id is None) or (
        payload.org_member_id is not None and payload.game_guest_id is not None
    ):
        raise HTTPException(status_code=400, detail="Pick must have exactly one target")

    pick_number = draft.current_pick_index + 1
    round_number = ((pick_number - 1) // 4) + 1

    item_payload = None

    if payload.org_member_id is not None:
        exists = (
            db.query(GameDraftPick)
            .filter(GameDraftPick.game_id == game_id, GameDraftPick.org_member_id == payload.org_member_id)
            .first()
        )
        if exists:
            raise HTTPException(status_code=409, detail="Already picked")

        row = (
            db.query(GameAttendance)
            .options(joinedload(GameAttendance.org_member).joinedload(OrgMember.user))
            .filter(
                GameAttendance.org_id == org_id,
                GameAttendance.game_id == game_id,
                GameAttendance.org_member_id == payload.org_member_id,
                GameAttendance.status == AttendanceStatus.GOING,
            )
            .first()
        )
        if not row or not row.org_member or not row.org_member.user:
            raise HTTPException(status_code=409, detail="Member is not GOING")

        item_payload = _resolve_member_payload(row.org_member)
        pick = GameDraftPick(
            org_id=org_id,
            game_id=game_id,
            draft_id=draft.id,
            round_number=round_number,
            pick_number=pick_number,
            team_side=expected,
            org_member_id=payload.org_member_id,
            game_guest_id=None,
        )
        db.add(pick)

        side = TeamSide.A if expected == TeamSide.A else TeamSide.B
        tm = (
            db.query(GameTeamMember)
            .filter(GameTeamMember.org_id == org_id, GameTeamMember.game_id == game_id, GameTeamMember.org_member_id == payload.org_member_id)
            .first()
        )
        if tm:
            tm.team = side
        else:
            db.add(GameTeamMember(org_id=org_id, game_id=game_id, org_member_id=payload.org_member_id, team=side))

    else:
        exists = (
            db.query(GameDraftPick)
            .filter(GameDraftPick.game_id == game_id, GameDraftPick.game_guest_id == payload.game_guest_id)
            .first()
        )
        if exists:
            raise HTTPException(status_code=409, detail="Already picked")

        gg = (
            db.query(GameGuest)
            .filter(GameGuest.id == payload.game_guest_id, GameGuest.org_id == org_id, GameGuest.game_id == game_id)
            .first()
        )
        if not gg:
            raise HTTPException(status_code=404, detail="Game guest not found")

        item_payload = _resolve_guest_payload(gg)
        pick = GameDraftPick(
            org_id=org_id,
            game_id=game_id,
            draft_id=draft.id,
            round_number=round_number,
            pick_number=pick_number,
            team_side=expected,
            org_member_id=None,
            game_guest_id=payload.game_guest_id,
        )
        db.add(pick)

        side = TeamSide.A if expected == TeamSide.A else TeamSide.B
        tg = (
            db.query(GameTeamGuest)
            .filter(GameTeamGuest.org_id == org_id, GameTeamGuest.game_id == game_id, GameTeamGuest.game_guest_id == payload.game_guest_id)
            .first()
        )
        if tg:
            tg.team = side
        else:
            db.add(GameTeamGuest(org_id=org_id, game_id=game_id, game_guest_id=payload.game_guest_id, team=side))

    draft.current_pick_index = draft.current_pick_index + 1
    db.commit()

    return get_draft(org_id=org_id, game_id=game_id, db=db, current_user=current_user)


@router.post("/orgs/{org_id}/games/{game_id}/draft/finish", response_model=DraftStateResponse)
def finish_draft(
    org_id: UUID,
    game_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)
    _require_admin_membership(db=db, org_id=org_id, user_id=current_user.id)

    draft = db.query(GameDraft).filter(GameDraft.org_id == org_id, GameDraft.game_id == game_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft.status != DraftStatus.IN_PROGRESS:
        raise HTTPException(status_code=409, detail="Draft is not in progress")
    draft.status = DraftStatus.FINISHED
    db.commit()
    return get_draft(org_id=org_id, game_id=game_id, db=db, current_user=current_user)


@router.get("/orgs/{org_id}/games/{game_id}/draft", response_model=DraftStateResponse)
def get_draft(
    org_id: UUID,
    game_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)

    game = db.query(Game).filter(Game.id == game_id, Game.org_id == org_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    draft = db.query(GameDraft).filter(GameDraft.org_id == org_id, GameDraft.game_id == game_id).first()
    status = draft.status if draft else DraftStatus.NOT_STARTED
    order_mode = draft.order_mode if draft else "ABBA"
    current_pick_index = draft.current_pick_index if draft else 0

    pick_rows = (
        db.query(GameDraftPick)
        .options(joinedload(GameDraftPick.org_member).joinedload(OrgMember.user), joinedload(GameDraftPick.game_guest))
        .filter(GameDraftPick.org_id == org_id, GameDraftPick.game_id == game_id)
        .order_by(GameDraftPick.pick_number.asc())
        .all()
    )
    picked_member_ids = {p.org_member_id for p in pick_rows if p.org_member_id is not None}
    picked_guest_ids = {p.game_guest_id for p in pick_rows if p.game_guest_id is not None}

    going_rows = (
        db.query(GameAttendance)
        .options(joinedload(GameAttendance.org_member).joinedload(OrgMember.user))
        .filter(GameAttendance.org_id == org_id, GameAttendance.game_id == game_id, GameAttendance.status == AttendanceStatus.GOING)
        .all()
    )
    remaining_pool = []
    for r in going_rows:
        if not r.org_member or not r.org_member.user:
            continue
        if r.org_member_id in picked_member_ids:
            continue
        remaining_pool.append(_resolve_member_payload(r.org_member))

    guest_rows = (
        db.query(GameGuest)
        .filter(GameGuest.org_id == org_id, GameGuest.game_id == game_id)
        .order_by(GameGuest.created_at.asc())
        .all()
    )
    for g in guest_rows:
        if g.id in picked_guest_ids:
            continue
        remaining_pool.append(_resolve_guest_payload(g))

    teams = get_game_teams(org_id=org_id, game_id=game_id, db=db, current_user=current_user)

    current_turn = None
    if status == DraftStatus.IN_PROGRESS:
        current_turn = _draft_turn(order_mode, current_pick_index)

    picks_out = []
    for p in pick_rows:
        if p.org_member_id and p.org_member and p.org_member.user:
            item = _resolve_member_payload(p.org_member)
        elif p.game_guest_id and p.game_guest:
            item = _resolve_guest_payload(p.game_guest)
        else:
            continue
        picks_out.append(
            {
                "id": p.id,
                "round_number": p.round_number,
                "pick_number": p.pick_number,
                "team_side": p.team_side,
                "created_at": p.created_at,
                "item": item,
            }
        )

    return {
        "status": status,
        "order_mode": order_mode,
        "current_pick_index": current_pick_index,
        "current_turn_team_side": current_turn,
        "picks": picks_out,
        "remaining_pool": remaining_pool,
        "teams": teams,
    }


@router.put("/orgs/{org_id}/games/{game_id}/teams", response_model=TeamsResponse)
def set_game_team_assignment(
    org_id: UUID,
    game_id: UUID,
    payload: TeamAssignmentSetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)
    _require_admin_membership(db=db, org_id=org_id, user_id=current_user.id)

    game = db.query(Game).filter(Game.id == game_id, Game.org_id == org_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    ttype = (payload.target.type or "").upper()
    tid = payload.target.id
    team = payload.team.upper() if payload.team else None
    if team not in ("A", "B", None):
        raise HTTPException(status_code=400, detail="Invalid team")

    if ttype == "MEMBER":
        going = (
            db.query(GameAttendance)
            .filter(
                GameAttendance.org_id == org_id,
                GameAttendance.game_id == game_id,
                GameAttendance.org_member_id == tid,
                GameAttendance.status == AttendanceStatus.GOING,
            )
            .first()
        )
        if not going:
            raise HTTPException(status_code=409, detail="Member is not GOING")

        row = (
            db.query(GameTeamMember)
            .filter(GameTeamMember.org_id == org_id, GameTeamMember.game_id == game_id, GameTeamMember.org_member_id == tid)
            .first()
        )
        if team is None:
            if row:
                db.delete(row)
        else:
            side = TeamSide.A if team == "A" else TeamSide.B
            if row:
                row.team = side
            else:
                db.add(GameTeamMember(org_id=org_id, game_id=game_id, org_member_id=tid, team=side))

    elif ttype == "GUEST":
        gg = (
            db.query(GameGuest)
            .filter(GameGuest.id == tid, GameGuest.org_id == org_id, GameGuest.game_id == game_id)
            .first()
        )
        if not gg:
            raise HTTPException(status_code=404, detail="Game guest not found")

        row = (
            db.query(GameTeamGuest)
            .filter(GameTeamGuest.org_id == org_id, GameTeamGuest.game_id == game_id, GameTeamGuest.game_guest_id == tid)
            .first()
        )
        if team is None:
            if row:
                db.delete(row)
        else:
            side = TeamSide.A if team == "A" else TeamSide.B
            if row:
                row.team = side
            else:
                db.add(GameTeamGuest(org_id=org_id, game_id=game_id, game_guest_id=tid, team=side))
    else:
        raise HTTPException(status_code=400, detail="Invalid target type")

    db.commit()
    return get_game_teams(org_id=org_id, game_id=game_id, db=db, current_user=current_user)


@router.get("/orgs/{org_id}/games/{game_id}/attendance", response_model=GameAttendanceSummary)
def get_game_attendance(
    org_id: UUID,
    game_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)

    game = db.query(Game).filter(Game.id == game_id, Game.org_id == org_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    membership = (
        db.query(OrgMember)
        .filter(OrgMember.org_id == org_id, OrgMember.user_id == current_user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member")

    counts_rows = (
        db.query(GameAttendance.status, func.count(GameAttendance.id))
        .filter(GameAttendance.org_id == org_id, GameAttendance.game_id == game_id)
        .group_by(GameAttendance.status)
        .all()
    )
    counts_map = {s.value: int(c) for s, c in counts_rows}

    my = (
        db.query(GameAttendance)
        .filter(
            GameAttendance.org_id == org_id,
            GameAttendance.game_id == game_id,
            GameAttendance.org_member_id == membership.id,
        )
        .first()
    )

    going_rows = (
        db.query(GameAttendance)
        .options(joinedload(GameAttendance.org_member).joinedload(OrgMember.user))
        .filter(
            GameAttendance.org_id == org_id,
            GameAttendance.game_id == game_id,
            GameAttendance.status == AttendanceStatus.GOING,
        )
        .all()
    )
    going_members = []
    for r in going_rows:
        if not r.org_member:
            continue
        mt = r.org_member.member_type
        included = mt == MemberType.MONTHLY
        going_members.append(
            {
                "id": r.org_member.id,
                "nickname": r.org_member.nickname,
                "member_type": mt,
                "billable": not included,
                "included": included,
                "user": r.org_member.user,
            }
        )

    my_member_type = membership.member_type
    my_included = my_member_type == MemberType.MONTHLY

    return {
        "counts": {
            "going": counts_map.get("GOING", 0),
            "maybe": counts_map.get("MAYBE", 0),
            "not_going": counts_map.get("NOT_GOING", 0),
        },
        "my_status": my.status if my else None,
        "my_member_type": my_member_type,
        "my_billable": not my_included,
        "my_included": my_included,
        "going_members": going_members,
    }


@router.put("/orgs/{org_id}/games/{game_id}/attendance", response_model=GameAttendanceSummary)
def put_game_attendance(
    org_id: UUID,
    game_id: UUID,
    payload: AttendanceSetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)

    game = db.query(Game).filter(Game.id == game_id, Game.org_id == org_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    membership = (
        db.query(OrgMember)
        .filter(OrgMember.org_id == org_id, OrgMember.user_id == current_user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member")

    row = (
        db.query(GameAttendance)
        .filter(GameAttendance.org_id == org_id, GameAttendance.game_id == game_id, GameAttendance.org_member_id == membership.id)
        .first()
    )
    if row:
        row.status = payload.status
    else:
        row = GameAttendance(
            org_id=org_id,
            game_id=game_id,
            org_member_id=membership.id,
            user_id=current_user.id,
            status=payload.status,
        )
        db.add(row)

    db.commit()
    return get_game_attendance(org_id=org_id, game_id=game_id, db=db, current_user=current_user)


@router.post("/games/{game_id}/attendance", response_model=Attendance)
def mark_attendance(
    game_id: UUID,
    attendance_in: AttendanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # garante que é membro da org do jogo
    require_org_member(org_id=game.org_id, db=db, current_user=current_user)
    membership = (
        db.query(OrgMember)
        .filter(OrgMember.org_id == game.org_id, OrgMember.user_id == current_user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member")

    attendance = (
        db.query(GameAttendance)
        .filter(GameAttendance.game_id == game_id, GameAttendance.user_id == current_user.id)
        .first()
    )

    if attendance:
        attendance.status = attendance_in.status
    else:
        attendance = GameAttendance(
            org_id=game.org_id,
            game_id=game_id,
            user_id=current_user.id,
            org_member_id=membership.id,
            status=attendance_in.status
        )
        db.add(attendance)

    db.commit()
    db.refresh(attendance)
    return attendance

@router.get("/{game_id}/attendance")
def list_attendance(
    game_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    membership = db.query(OrgMember).filter(
        OrgMember.user_id == current_user.id, OrgMember.org_id == game.org_id
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member")

    rows = db.query(GameAttendance).filter(GameAttendance.game_id == game_id).all()
    return rows
