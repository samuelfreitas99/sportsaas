from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.game import Game, GameAttendance
from app.models.organization import OrgMember, OrgRole
from app.schemas.game import GameCreate, Game as GameSchema, AttendanceCreate, Attendance
from app.routers.deps import get_current_user
from app.models.user import User

# IMPORTA O HELPER QUE VOCÊ CRIOU
from app.routers.deps import require_org_member

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

    attendance = (
        db.query(GameAttendance)
        .filter(GameAttendance.game_id == game_id, GameAttendance.user_id == current_user.id)
        .first()
    )

    if attendance:
        attendance.status = attendance_in.status
    else:
        attendance = GameAttendance(
            game_id=game_id,
            user_id=current_user.id,
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
