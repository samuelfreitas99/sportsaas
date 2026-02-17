from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.db.session import get_db
from app.models.game import AttendanceStatus, Game, GameAttendance
from app.models.org_member import OrgMember, OrgRole
from app.schemas.game import GameCreate, Game as GameSchema, AttendanceCreate, Attendance
from app.routers.deps import get_current_user
from app.models.user import User

# IMPORTA O HELPER QUE VOCÊ CRIOU
from app.routers.deps import require_org_member
from app.schemas.attendance import AttendanceSetRequest, GameAttendanceSummary

router = APIRouter()

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

    game = Game(**game_in.model_dump(), org_id=org_id)
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
    going_members = [r.org_member for r in going_rows if r.org_member is not None]

    return {
        "counts": {
            "going": counts_map.get("GOING", 0),
            "maybe": counts_map.get("MAYBE", 0),
            "not_going": counts_map.get("NOT_GOING", 0),
        },
        "my_status": my.status if my else None,
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
